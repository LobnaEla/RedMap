#!/usr/bin/env python3
"""
Complete Event-Driven CTI Service
Monitors external sources and triggers ingestion pipelines automatically
"""

import requests
import yaml
import json
import logging
import asyncio
import aiohttp
import feedparser
import hashlib
import redis
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# The project root for Docker imports
sys.path.append("/opt/project/cti_pipeline")

# Path Configuration
BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
CONFIG_PATH = os.path.join(BASE_PROJECT_PATH, "config")


class EventType(Enum):
    """Event types that can trigger CTI pipeline"""

    NEW_CONTENT = "new_content"
    HIGH_PRIORITY = "high_priority"
    THREAT_INDICATOR = "threat_indicator"
    VULNERABILITY = "vulnerability"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class Priority(Enum):
    """Priority levels for events"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CTIEvent:
    """CTI Event data structure"""

    source_name: str
    event_type: str
    reason: str
    priority: str
    timestamp: str = None
    source_metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.source_metadata is None:
            self.source_metadata = {}


class CTIEventService:
    """Core service for managing CTI events and triggers"""

    def __init__(
        self,
        n8n_webhook_url: str = None,
        redis_host: str = None,
        redis_port: int = None,
        config_dir: str = CONFIG_PATH,
    ):

        # Load configuration from environment
        self.n8n_webhook_url = n8n_webhook_url or os.getenv(
            "N8N_WEBHOOK_URL", "http://n8n:5678/webhook/cti-event"
        )
        redis_host = redis_host or os.getenv("REDIS_HOST", "redis")
        redis_port = redis_port or int(os.getenv("REDIS_PORT", 6379))

        self.config_dir = Path(config_dir)

        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=redis_host, port=redis_port, decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

        # Load configurations
        self.sources_config = self._load_sources_config()
        self.source_limits = self._get_source_limits()

    def _load_sources_config(self) -> Dict[str, Any]:
        """Load sources configuration from YAML"""
        try:
            sources_file = self.config_dir / "sources.yaml"
            if sources_file.exists():
                with open(sources_file, "r") as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"Sources config file not found at {sources_file}")
                return {"sources": []}
        except Exception as e:
            logger.error(f"Error loading sources config: {e}")
            return {"sources": []}

    def _get_source_limits(self) -> Dict[str, Dict[str, int]]:
        """Get rate limiting configuration for each source"""
        return {
            "otx": {"cooldown_minutes": 60, "max_concurrent": 2},
            "rss": {"cooldown_minutes": 30, "max_concurrent": 3},
            "tuncert": {"cooldown_minutes": 120, "max_concurrent": 1},
            "twitter": {"cooldown_minutes": 15, "max_concurrent": 5},
            "blog": {"cooldown_minutes": 45, "max_concurrent": 2},
        }

    def _check_rate_limit(self, source_name: str) -> bool:
        """Check if source can be triggered based on rate limits"""
        if not self.redis_client:
            logger.warning("Redis not available, skipping rate limit check")
            return True

        limits = self.source_limits.get(source_name, {"cooldown_minutes": 30})
        cooldown_key = f"last_trigger_{source_name}"

        try:
            last_trigger = self.redis_client.get(cooldown_key)
            if last_trigger:
                last_time = datetime.fromisoformat(last_trigger)
                cooldown_period = timedelta(minutes=limits["cooldown_minutes"])

                if datetime.utcnow() - last_time < cooldown_period:
                    remaining = cooldown_period - (datetime.utcnow() - last_time)
                    logger.info(
                        f"Source {source_name} rate limited. {remaining.total_seconds()/60:.1f} minutes remaining"
                    )
                    return False

            return True
        except Exception as e:
            logger.error(f"Error checking rate limit for {source_name}: {e}")
            return True

    def _update_trigger_time(self, source_name: str):
        """Update the last trigger time for a source"""
        if self.redis_client:
            try:
                cooldown_key = f"last_trigger_{source_name}"
                self.redis_client.set(cooldown_key, datetime.utcnow().isoformat())
            except Exception as e:
                logger.error(f"Error updating trigger time for {source_name}: {e}")

    def trigger_event(self, event: CTIEvent) -> Dict[str, Any]:
        """Trigger a CTI event via n8n webhook"""

        # Validate source exists
        valid_sources = [s["name"] for s in self.sources_config.get("sources", [])]
        if event.source_name not in valid_sources:
            logger.error(f"Unknown source: {event.source_name}")
            return {
                "status": "error",
                "message": f"Unknown source: {event.source_name}",
                "valid_sources": valid_sources,
            }

        # Check rate limits
        if not self._check_rate_limit(event.source_name):
            limits = self.source_limits.get(event.source_name, {})
            return {
                "status": "rate_limited",
                "source": event.source_name,
                "message": "Source triggered too recently, ignoring event",
                "cooldown_minutes": limits.get("cooldown_minutes", 30),
            }

        # Prepare payload for n8n
        payload = asdict(event)

        try:
            # Send to n8n webhook
            response = requests.post(
                self.n8n_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                # Update trigger time on successful trigger
                self._update_trigger_time(event.source_name)

                logger.info(
                    f"Successfully triggered event for source {event.source_name}"
                )
                return {
                    "status": "triggered",
                    "source": event.source_name,
                    "event_type": event.event_type,
                    "response": response.json() if response.content else {},
                }
            else:
                logger.error(
                    f"Failed to trigger event. Status: {response.status_code}, Response: {response.text}"
                )
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}: {response.text}",
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {"status": "error", "message": f"Request failed: {str(e)}"}

    def get_source_status(self, source_name: str) -> Dict[str, Any]:
        """Get current status of a source"""
        if not self.redis_client:
            return {"status": "unknown", "message": "Redis not available"}

        try:
            cooldown_key = f"last_trigger_{source_name}"
            last_trigger = self.redis_client.get(cooldown_key)
            limits = self.source_limits.get(source_name, {"cooldown_minutes": 30})

            if last_trigger:
                last_time = datetime.fromisoformat(last_trigger)
                cooldown_period = timedelta(minutes=limits["cooldown_minutes"])
                time_since_trigger = datetime.utcnow() - last_time

                if time_since_trigger < cooldown_period:
                    remaining = cooldown_period - time_since_trigger
                    return {
                        "status": "rate_limited",
                        "last_trigger": last_trigger,
                        "cooldown_remaining_minutes": remaining.total_seconds() / 60,
                        "can_trigger": False,
                    }
                else:
                    return {
                        "status": "ready",
                        "last_trigger": last_trigger,
                        "can_trigger": True,
                    }
            else:
                return {"status": "ready", "last_trigger": None, "can_trigger": True}

        except Exception as e:
            logger.error(f"Error getting status for {source_name}: {e}")
            return {"status": "error", "message": str(e)}


class EventMonitor:
    """Base class for monitoring external sources for changes"""

    def __init__(self, event_service: CTIEventService):
        self.event_service = event_service
        self.last_check_hashes: Dict[str, str] = {}
        self.redis_key_prefix = "monitor_hash_"

        # Load previous hashes from Redis if available
        self._load_previous_hashes()

    def _load_previous_hashes(self):
        """Load previous content hashes from Redis"""
        if self.event_service.redis_client:
            try:
                keys = self.event_service.redis_client.keys(f"{self.redis_key_prefix}*")
                for key in keys:
                    source_key = key.replace(self.redis_key_prefix, "")
                    hash_value = self.event_service.redis_client.get(key)
                    if hash_value:
                        self.last_check_hashes[source_key] = hash_value
                logger.info(f"Loaded {len(self.last_check_hashes)} previous hashes")
            except Exception as e:
                logger.error(f"Error loading previous hashes: {e}")

    def _save_hash(self, source_key: str, hash_value: str):
        """Save content hash to Redis"""
        if self.event_service.redis_client:
            try:
                redis_key = f"{self.redis_key_prefix}{source_key}"
                self.event_service.redis_client.set(
                    redis_key, hash_value, ex=86400
                )  # 24 hour expiry
            except Exception as e:
                logger.error(f"Error saving hash for {source_key}: {e}")

    async def monitor(self):
        """Override in subclasses"""
        raise NotImplementedError


class RSSMonitor(EventMonitor):
    """Monitor RSS feeds for new entries"""

    def __init__(self, event_service: CTIEventService):
        super().__init__(event_service)
        self.rss_sources = self._load_rss_sources()

    def _load_rss_sources(self) -> List[Dict]:
        """Load RSS sources configuration"""
        try:
            from ...cti_pipeline.config.rss_sources import RSS_SOURCES

            return RSS_SOURCES
        except ImportError:
            logger.warning("RSS sources not found")
            return []

    async def monitor(self):
        """Check RSS feeds for new content"""
        if not self.rss_sources:
            return

        for source in self.rss_sources:
            try:
                feed = feedparser.parse(source["url"])

                # Create hash of recent entries
                recent_entries = feed.entries[:10]  # Check last 10 entries
                content_hash = self._hash_entries(recent_entries)

                source_key = f"rss_{source['name']}"

                # Check if content changed
                if source_key in self.last_check_hashes:
                    if content_hash != self.last_check_hashes[source_key]:
                        logger.info(
                            f"New content detected in RSS source: {source['name']}"
                        )

                        # Trigger event
                        event = CTIEvent(
                            source_name="rss",
                            event_type=EventType.NEW_CONTENT.value,
                            reason=f"New entries detected in {source['name']}",
                            priority=Priority.MEDIUM.value,
                            source_metadata={
                                "rss_source": source["name"],
                                "feed_url": source["url"],
                                "new_entries_count": len(recent_entries),
                                "latest_entry_title": (
                                    recent_entries[0].get("title", "")
                                    if recent_entries
                                    else ""
                                ),
                            },
                        )

                        result = self.event_service.trigger_event(event)
                        logger.info(f"RSS trigger result: {result.get('status')}")

                # Update hash
                self.last_check_hashes[source_key] = content_hash
                self._save_hash(source_key, content_hash)

            except Exception as e:
                logger.error(
                    f"Error monitoring RSS source {source.get('name', 'unknown')}: {e}"
                )

    def _hash_entries(self, entries: List) -> str:
        """Create hash of entry titles and dates"""
        content = ""
        for entry in entries:
            content += f"{entry.get('title', '')}{entry.get('published', '')}"
        return hashlib.md5(content.encode()).hexdigest()


class BlogMonitor(EventMonitor):
    """Monitor blog sources for new posts"""

    def __init__(self, event_service: CTIEventService):
        super().__init__(event_service)
        self.blog_sources = self._load_blog_sources()

    def _load_blog_sources(self) -> List[Dict]:
        """Load blog sources configuration"""
        try:
            from ...cti_pipeline.config.blog_sources import BLOG_SOURCES

            return BLOG_SOURCES
        except ImportError:
            logger.warning("Blog sources not found")
            return []

    async def monitor(self):
        """Check blog sources for new content"""
        if not self.blog_sources:
            return

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for source in self.blog_sources:
                try:
                    async with session.get(source["url"]) as response:
                        if response.status == 200:
                            content = await response.text()
                            # Use first 5000 characters to detect changes
                            content_hash = hashlib.md5(
                                content[:5000].encode()
                            ).hexdigest()

                            source_key = f"blog_{source['name']}"

                            if source_key in self.last_check_hashes:
                                if content_hash != self.last_check_hashes[source_key]:
                                    logger.info(
                                        f"Content change detected in blog: {source['name']}"
                                    )

                                    event = CTIEvent(
                                        source_name="blog",
                                        event_type=EventType.NEW_CONTENT.value,
                                        reason=f"Content change detected in {source['name']}",
                                        priority=Priority.MEDIUM.value,
                                        source_metadata={
                                            "blog_source": source["name"],
                                            "blog_url": source["url"],
                                            "response_status": response.status,
                                        },
                                    )

                                    result = self.event_service.trigger_event(event)
                                    logger.info(
                                        f"Blog trigger result: {result.get('status')}"
                                    )

                            # Update hash
                            self.last_check_hashes[source_key] = content_hash
                            self._save_hash(source_key, content_hash)
                        else:
                            logger.warning(
                                f"HTTP {response.status} for blog {source['name']}"
                            )

                except asyncio.TimeoutError:
                    logger.warning(
                        f"Timeout monitoring blog {source.get('name', 'unknown')}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error monitoring blog {source.get('name', 'unknown')}: {e}"
                    )


class OTXMonitor(EventMonitor):
    """Monitor OTX for new pulses"""

    def __init__(self, event_service: CTIEventService):
        super().__init__(event_service)
        self.otx_api_key = os.getenv("OTX_API_KEY")
        self.otx_url = "https://otx.alienvault.com/api/v1/pulses/subscribed"

    async def monitor(self):
        """Check OTX for new pulses"""
        if not self.otx_api_key:
            logger.debug("OTX API key not configured, skipping OTX monitoring")
            return

        headers = {"X-OTX-API-KEY": self.otx_api_key}

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.otx_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Get recent pulses (last 2 hours)
                        recent_pulses = []
                        cutoff_time = datetime.utcnow() - timedelta(hours=2)

                        for pulse in data.get("results", []):
                            try:
                                pulse_time = datetime.fromisoformat(
                                    pulse["created"].replace("Z", "+00:00")
                                )
                                if pulse_time > cutoff_time:
                                    recent_pulses.append(pulse)
                            except (ValueError, KeyError):
                                continue

                        if recent_pulses:
                            # Check for high-priority indicators
                            high_priority = any(
                                pulse.get("TLP", "").lower() in ["red", "amber"]
                                or len(pulse.get("indicators", [])) > 100
                                for pulse in recent_pulses
                            )

                            priority = (
                                Priority.HIGH.value
                                if high_priority
                                else Priority.MEDIUM.value
                            )
                            event_type = (
                                EventType.HIGH_PRIORITY.value
                                if high_priority
                                else EventType.NEW_CONTENT.value
                            )

                            event = CTIEvent(
                                source_name="otx",
                                event_type=event_type,
                                reason=f"New OTX pulses detected ({len(recent_pulses)} pulses)",
                                priority=priority,
                                source_metadata={
                                    "new_pulses_count": len(recent_pulses),
                                    "high_priority": high_priority,
                                    "pulse_ids": [
                                        p.get("id")
                                        for p in recent_pulses[:5]
                                        if p.get("id")
                                    ],
                                },
                            )

                            result = self.event_service.trigger_event(event)
                            logger.info(f"OTX trigger result: {result.get('status')}")
                    else:
                        logger.warning(f"OTX API returned status {response.status}")

        except asyncio.TimeoutError:
            logger.warning("Timeout monitoring OTX")
        except Exception as e:
            logger.error(f"Error monitoring OTX: {e}")


class TunCertMonitor(EventMonitor):
    """Monitor Turkey CERT for new vulnerabilities"""

    async def monitor(self):
        """Check TunCert for new vulnerability announcements"""
        try:
            # TunCert typically has RSS feeds or web pages to monitor
            # This is a placeholder - implement based on actual TunCert API/feeds

            # For now, trigger based on schedule (every 2 hours)
            source_key = "tuncert_last_check"
            now = datetime.utcnow()

            if source_key in self.last_check_hashes:
                last_check = datetime.fromisoformat(self.last_check_hashes[source_key])
                if now - last_check < timedelta(hours=2):
                    return

            # Simulate checking for new vulnerabilities
            logger.info("Checking TunCert for new vulnerabilities")

            event = CTIEvent(
                source_name="tuncert",
                event_type=EventType.VULNERABILITY.value,
                reason="Scheduled TunCert vulnerability check",
                priority=Priority.MEDIUM.value,
                source_metadata={
                    "check_type": "scheduled",
                    "last_check": self.last_check_hashes.get(source_key),
                },
            )

            result = self.event_service.trigger_event(event)
            logger.info(f"TunCert trigger result: {result.get('status')}")

            # Update last check time
            self.last_check_hashes[source_key] = now.isoformat()
            self._save_hash(source_key, now.isoformat())

        except Exception as e:
            logger.error(f"Error monitoring TunCert: {e}")


class TwitterMonitor(EventMonitor):
    """Monitor Twitter for security-related content"""

    async def monitor(self):
        """Monitor Twitter accounts for new security content"""
        # Note: Twitter API v2 requires authentication and has rate limits
        # This is a placeholder implementation

        twitter_config = self._load_twitter_config()
        if not twitter_config:
            logger.debug("Twitter configuration not found, skipping Twitter monitoring")
            return

        # Implement Twitter API monitoring here
        logger.debug("Twitter monitoring requires API v2 implementation")

    def _load_twitter_config(self) -> Optional[Dict]:
        """Load Twitter configuration"""
        try:
            config_file = self.event_service.config_dir / "twitter_users.yaml"
            if config_file.exists():
                with open(config_file, "r") as f:
                    return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading Twitter config: {e}")
        return None


class EventOrchestrator:
    """Orchestrates all event monitors"""

    def __init__(self, event_service: CTIEventService, check_interval: int = None):
        self.event_service = event_service
        self.check_interval = check_interval or int(
            os.getenv("MONITOR_INTERVAL", 300)
        )  # 5 minutes default
        self.monitors: List[EventMonitor] = []
        self.running = False

        self._setup_monitors()

    def _setup_monitors(self):
        """Setup all monitors based on configuration"""
        monitor_classes = [
            RSSMonitor,
            BlogMonitor,
            OTXMonitor,
            TunCertMonitor,
            TwitterMonitor,
        ]

        for monitor_class in monitor_classes:
            try:
                monitor = monitor_class(self.event_service)
                self.monitors.append(monitor)
                logger.info(f"Setup {monitor_class.__name__}")
            except Exception as e:
                logger.error(f"Failed to setup {monitor_class.__name__}: {e}")

    async def start_monitoring(self):
        """Start continuous monitoring"""
        self.running = True
        logger.info(f"Starting event monitoring with {len(self.monitors)} monitors")
        logger.info(f"Check interval: {self.check_interval} seconds")

        while self.running:
            try:
                start_time = datetime.utcnow()

                # Run all monitors concurrently
                monitor_tasks = [monitor.monitor() for monitor in self.monitors]
                await asyncio.gather(*monitor_tasks, return_exceptions=True)

                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.debug(f"Completed monitoring cycle in {duration:.2f} seconds")

                # Wait before next check
                await asyncio.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("Monitoring stop requested")


# Main execution
async def main():
    """Main async function"""
    # Initialize services
    event_service = CTIEventService()

    # Start monitoring
    orchestrator = EventOrchestrator(event_service)

    try:
        await orchestrator.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        orchestrator.stop_monitoring()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the event-driven monitoring
    asyncio.run(main())
