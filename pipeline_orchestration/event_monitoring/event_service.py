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

# Add the project root for Docker imports
sys.path.append("/opt/project/cti_pipeline")

# === Path Configuration ===
# Try to detect if we're running in Docker or local environment
if os.path.exists("/opt/project/cti_pipeline"):
    BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
else:
    # Local development environment
    BASE_PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

CONFIG_PATH = os.path.join(BASE_PROJECT_PATH, "config")
logger.info(f"Using BASE_PROJECT_PATH: {BASE_PROJECT_PATH}")
logger.info(f"Using CONFIG_PATH: {CONFIG_PATH}")

# === Load Configuration Modules ===
BLOG_SOURCES = []
RSS_SOURCES = []
TWITTER_USERS = []

try:
    import importlib.util

    # Load blog_sources
    blog_path = os.path.join(CONFIG_PATH, "blog_sources.py")
    if os.path.exists(blog_path):
        blog_spec = importlib.util.spec_from_file_location("blog_sources", blog_path)
        if blog_spec and blog_spec.loader:
            blog_module = importlib.util.module_from_spec(blog_spec)
            blog_spec.loader.exec_module(blog_module)
            BLOG_SOURCES = getattr(blog_module, "BLOG_SOURCES", [])

    # Load rss_sources
    rss_path = os.path.join(CONFIG_PATH, "rss_sources.py")
    if os.path.exists(rss_path):
        rss_spec = importlib.util.spec_from_file_location("rss_sources", rss_path)
        if rss_spec and rss_spec.loader:
            rss_module = importlib.util.module_from_spec(rss_spec)
            rss_spec.loader.exec_module(rss_module)
            RSS_SOURCES = getattr(rss_module, "RSS_SOURCES", [])

    # Load twitter_users
    twitter_path = os.path.join(CONFIG_PATH, "twitter_users.py")
    if os.path.exists(twitter_path):
        twitter_spec = importlib.util.spec_from_file_location(
            "twitter_users", twitter_path
        )
        if twitter_spec and twitter_spec.loader:
            twitter_module = importlib.util.module_from_spec(twitter_spec)
            twitter_spec.loader.exec_module(twitter_module)
            TWITTER_USERS = getattr(twitter_module, "twitter_users", [])

    logger.info("Loaded configuration modules via importlib")
    logger.info(
        f"Loaded {len(BLOG_SOURCES)} blog sources, {len(RSS_SOURCES)} RSS sources, {len(TWITTER_USERS)} Twitter users"
    )

except Exception as load_error:
    logger.warning(f"Could not load configuration modules: {load_error}")
    BLOG_SOURCES = []
    RSS_SOURCES = []
    TWITTER_USERS = []

# === N8N Configuration ===
N8N_BASE_URL = "http://n8n:5678"


# === Load sources Config ===
def load_sources_config():
    # Try multiple possible locations for sources.yaml
    possible_paths = [
        os.path.join(CONFIG_PATH, "sources.yaml"),
        os.path.join("/opt/project/cti_pipeline/config", "sources.yaml"),
        os.path.join("/app/config", "sources.yaml"),
        os.path.join(
            os.path.dirname(__file__), "../../cti_pipeline/config/sources.yaml"
        ),
        os.path.join(os.path.dirname(__file__), "../config/sources.yaml"),
    ]

    for sources_yaml_path in possible_paths:
        try:
            if os.path.exists(sources_yaml_path):
                logger.info(f"Loading sources config from: {sources_yaml_path}")
                with open(sources_yaml_path, "r") as f:
                    config = yaml.safe_load(f)
                    if config and "sources" in config:
                        return config["sources"]
                    else:
                        logger.warning(f"No 'sources' key found in {sources_yaml_path}")
                        continue
        except Exception as e:
            logger.warning(f"Failed to load from {sources_yaml_path}: {e}")
            continue

    # If no config file found, raise an error - do not use static fallback
    error_msg = "No sources.yaml found in any location. Please ensure sources.yaml exists in the config directory."
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)


class EventType(Enum):
    """Event types that can trigger CTI pipeline"""

    NEW_CONTENT = "new_content"
    HIGH_PRIORITY = "high_priority"
    THREAT_INDICATOR = "threat_indicator"
    VULNERABILITY = "vulnerability"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    MANUAL_TRIGGER = "manual_trigger"
    AUTOMATIC = "automatic"


class Priority(Enum):
    """Priority levels for events"""

    LOW = "low"
    MEDIUM = "medium"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CTIEvent:
    source_name: str
    event_type: str
    reason: str
    priority: str
    timestamp: str = None
    source_metadata: Dict[str, Any] = None

    def __post_init__(self):
        if isinstance(self.event_type, Enum):
            self.event_type = self.event_type.value
        if isinstance(self.priority, Enum):
            self.priority = self.priority.value
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.source_metadata is None:
            self.source_metadata = {}


class CTIEventService:
    _instance = None

    def __new__(
        cls,
        n8n_webhook_url: str = None,
        redis_host: str = None,
        redis_port: int = None,
        config_dir: str = CONFIG_PATH,
    ):
        if cls._instance is None:
            cls._instance = super(CTIEventService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        n8n_webhook_url: str = None,
        redis_host: str = None,
        redis_port: int = None,
        config_dir: str = CONFIG_PATH,
    ):
        # Only initialize once for singleton
        if self._initialized:
            return

        # Load configuration from environment
        self.n8n_webhook_url = n8n_webhook_url or os.getenv(
            "N8N_WEBHOOK_URL", f"{N8N_BASE_URL}/webhook/cti-event"
        )
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "redis")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", 6379))
        self.config_dir = Path(config_dir)

        # Initialize Redis connection with checks
        self.redis_client = None
        self._connect_redis()

        # Load configurations
        self.sources_config = self._load_sources_config()
        self.source_limits = self._get_source_limits()

        self._initialized = True

    def _connect_redis(self):
        """Connect to Redis with proper error handling"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def _ensure_redis_connection(self) -> bool:
        """Ensure Redis connection is active, attempt reconnection if needed"""
        if self.redis_client is None:
            self._connect_redis()

        if self.redis_client is not None:
            try:
                self.redis_client.ping()
                return True
            except Exception as e:
                logger.warning(f"Redis connection lost, attempting reconnection: {e}")
                self.redis_client = None
                self._connect_redis()
                return self.redis_client is not None

        return False

    def _load_sources_config(self) -> Dict[str, Any]:
        """Load sources configuration from YAML"""
        try:
            sources = load_sources_config()
            # If sources is already a list (which it should be from the YAML), wrap it in a dict
            if isinstance(sources, list):
                return {"sources": sources}
            elif isinstance(sources, dict) and "sources" in sources:
                return sources
            else:
                logger.error("Invalid sources configuration format")
                return {"sources": []}
        except Exception as e:
            logger.error(f"Error loading sources config: {e}")
            return {"sources": []}

    def _get_source_limits(self) -> Dict[str, Dict[str, int]]:
        """Get rate limiting configuration for each source"""
        limits = {}

        # Load limits from sources config if available
        for source in self.sources_config.get("sources", []):
            source_name = source.get("name")
            if source_name:
                limits[source_name] = {
                    "cooldown_minutes": source.get("cooldown_minutes", 30),
                    "max_concurrent": source.get("max_concurrent", 2),
                }

        # Fallback defaults if no config loaded
        if not limits:
            limits = {
                "otx": {"cooldown_minutes": 60, "max_concurrent": 2},
                "rss": {"cooldown_minutes": 30, "max_concurrent": 3},
                "tuncert": {"cooldown_minutes": 120, "max_concurrent": 1},
                "twitter": {"cooldown_minutes": 15, "max_concurrent": 5},
                "blog": {"cooldown_minutes": 45, "max_concurrent": 2},
            }

        return limits

    def _check_rate_limit(self, source_name: str) -> bool:
        """Check if source can be triggered based on rate limits"""
        if not self._ensure_redis_connection():
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
        if self._ensure_redis_connection():
            try:
                cooldown_key = f"last_trigger_{source_name}"
                self.redis_client.set(cooldown_key, datetime.utcnow().isoformat())
            except Exception as e:
                logger.error(f"Error updating trigger time for {source_name}: {e}")
        else:
            logger.warning(
                f"Cannot update trigger time for {source_name}: Redis not available"
            )

    def trigger_event(self, event: CTIEvent) -> Dict[str, Any]:
        valid_sources = [s["name"] for s in self.sources_config.get("sources", [])]
        if event.source_name not in valid_sources:
            logger.error(f"Unknown source: {event.source_name}")
            return {
                "status": "error",
                "message": f"Unknown source: {event.source_name}",
                "valid_sources": valid_sources,
            }

        if not self._check_rate_limit(event.source_name):
            limits = self.source_limits.get(event.source_name, {})
            return {
                "status": "rate_limited",
                "source": event.source_name,
                "message": "Source triggered too recently, ignoring event",
                "cooldown_minutes": limits.get("cooldown_minutes", 30),
            }

        payload = asdict(event)
        try:
            response = requests.post(
                self.n8n_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            if response.status_code == 200:
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
        if not self._ensure_redis_connection():
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

    def get_available_sources(self) -> List[str]:
        """Get list of available sources from configuration"""
        try:
            if self.sources_config and "sources" in self.sources_config:
                sources = self.sources_config["sources"]
                if isinstance(sources, list):
                    # If sources is a list of dictionaries with 'name' key
                    return [
                        s.get("name", s) if isinstance(s, dict) else str(s)
                        for s in sources
                    ]
                elif isinstance(sources, dict):
                    # If sources is a dictionary, return keys
                    return list(sources.keys())

            # Fallback to source limits keys
            return list(self.source_limits.keys())
        except Exception as e:
            logger.error(f"Error getting available sources: {e}")
            return list(self.source_limits.keys())


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
        if self.event_service._ensure_redis_connection():
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
        if self.event_service._ensure_redis_connection():
            try:
                redis_key = f"{self.redis_key_prefix}{source_key}"
                self.event_service.redis_client.set(
                    redis_key, hash_value, ex=86400
                )  # 24 hour expiry
            except Exception as e:
                logger.error(f"Error saving hash for {source_key}: {e}")
        else:
            logger.warning(f"Cannot save hash for {source_key}: Redis not available")

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
        # First try to use imported RSS_SOURCES
        if RSS_SOURCES:
            return RSS_SOURCES

        # Fallback: check if RSS is configured in sources.yaml
        config = self.event_service.sources_config.get("sources", [])
        rss_sources = [s for s in config if s.get("name") == "rss"]
        if rss_sources:
            # Return default RSS configuration
            return [
                {
                    "name": "default_rss",
                    "url": "https://feeds.feedburner.com/eset/blog",
                    "description": "Default RSS feed monitoring",
                    "source_type": "rss_feed",
                }
            ]
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
        # First try to use imported BLOG_SOURCES
        if BLOG_SOURCES:
            return BLOG_SOURCES

        # Fallback: check if blog is configured in sources.yaml
        config = self.event_service.sources_config.get("sources", [])
        blog_sources = [s for s in config if s.get("name") == "blog"]
        if blog_sources:
            # Return default blog configuration
            return [
                {
                    "name": "default_security_blog",
                    "url": "https://www.welivesecurity.com/",
                }
            ]
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

    def __init__(self, event_service: CTIEventService):
        super().__init__(event_service)
        self.twitter_users = self._load_twitter_config()

    async def monitor(self):
        """Monitor Twitter accounts for new security content"""

        if not self.twitter_users:
            logger.debug("Twitter configuration not found, skipping Twitter monitoring")
            return

        # Check each configured Twitter user
        new_content_detected = False
        users_with_updates = []

        for username in self.twitter_users:
            try:
                # Check for new content from this user
                has_new_content = await self._check_user_for_updates(username)

                if has_new_content:
                    new_content_detected = True
                    users_with_updates.append(username)
                    logger.info(f"New content detected for Twitter user: {username}")

            except Exception as e:
                logger.error(f"Error checking Twitter user {username}: {e}")
                continue

        # If any user has new content, trigger the Twitter ingestion pipeline
        if new_content_detected:
            event = CTIEvent(
                source_name="twitter",
                event_type=EventType.NEW_CONTENT.value,
                reason=f"New tweets detected from {len(users_with_updates)} users",
                priority=Priority.MEDIUM.value,
                source_metadata={
                    "users_with_updates": users_with_updates,
                    "total_users_checked": len(self.twitter_users),
                    "update_type": "new_tweets",
                },
            )

            result = self.event_service.trigger_event(event)
            logger.info(f"Twitter trigger result: {result.get('status')}")

    async def _check_user_for_updates(self, username: str) -> bool:
        """Check if a specific Twitter user has new content"""
        try:
            # Use a lightweight approach to check for new content
            # We'll simulate scraping by getting basic timeline info
            latest_tweet_data = await self._get_latest_tweet_info(username)

            if not latest_tweet_data:
                logger.debug(f"No tweet data retrieved for {username}")
                return False

            # Create a hash key for this user
            source_key = f"twitter_user_{username}"

            # Create hash of latest tweet info
            tweet_hash = self._create_tweet_hash(latest_tweet_data)

            # Check if this is different from last check
            if source_key in self.last_check_hashes:
                if tweet_hash != self.last_check_hashes[source_key]:
                    # New content detected
                    self.last_check_hashes[source_key] = tweet_hash
                    self._save_hash(source_key, tweet_hash)
                    return True
                else:
                    # No change
                    return False
            else:
                # First time checking this user
                self.last_check_hashes[source_key] = tweet_hash
                self._save_hash(source_key, tweet_hash)
                # Don't trigger on first check to avoid false positives
                return False

        except Exception as e:
            logger.error(f"Error checking updates for user {username}: {e}")
            return False

    async def _get_latest_tweet_info(self, username: str) -> Optional[Dict]:
        """Get latest tweet information for a user using a lightweight method"""
        try:
            # Using aiohttp to make async HTTP requests
            timeout = aiohttp.ClientTimeout(total=30)

            # Twitter's public timeline (no auth required, but limited)
            # This is a simplified approach - in production you'd want to use Twitter API v2
            url = f"https://twitter.com/{username}"

            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()

                        # Extract basic info from the page
                        # This is a simplified approach - in a real implementation,
                        # you'd want to parse the HTML properly or use Twitter API

                        # Look for tweet timestamps or content changes
                        import re

                        # Try to find recent timestamp patterns
                        timestamp_patterns = [
                            r'"created_at":"([^"]+)"',
                            r'data-time="(\d+)"',
                            r'datetime="([^"]+)"',
                        ]

                        timestamps = []
                        for pattern in timestamp_patterns:
                            matches = re.findall(pattern, content)
                            timestamps.extend(matches)

                        if timestamps:
                            # Use the first/most recent timestamp found
                            latest_timestamp = timestamps[0]

                            return {
                                "username": username,
                                "latest_timestamp": latest_timestamp,
                                "content_length": len(
                                    content[:5000]
                                ),  # Use first 5k chars
                                "check_time": datetime.utcnow().isoformat(),
                            }
                        else:
                            # Fallback: use content hash of a portion of the page
                            return {
                                "username": username,
                                "content_sample": content[:2000],  # First 2k characters
                                "content_length": len(content),
                                "check_time": datetime.utcnow().isoformat(),
                            }
                    else:
                        logger.warning(
                            f"HTTP {response.status} when checking {username}"
                        )
                        return None

        except asyncio.TimeoutError:
            logger.warning(f"Timeout when checking Twitter user {username}")
            return None
        except Exception as e:
            logger.error(f"Error getting latest tweet info for {username}: {e}")
            return None

    def _create_tweet_hash(self, tweet_data: Dict) -> str:
        """Create a hash from tweet data to detect changes"""
        # Create a string from the key data points
        hash_content = ""

        if "latest_timestamp" in tweet_data:
            hash_content += tweet_data["latest_timestamp"]

        if "content_sample" in tweet_data:
            hash_content += tweet_data["content_sample"]

        if "content_length" in tweet_data:
            hash_content += str(tweet_data["content_length"])

        # Add username to make hash unique per user
        hash_content += tweet_data.get("username", "")

        return hashlib.md5(hash_content.encode()).hexdigest()

    def _load_twitter_config(self) -> Optional[List[str]]:
        """Load Twitter configuration from sources config"""
        # First try to use imported TWITTER_USERS
        if TWITTER_USERS:
            return TWITTER_USERS

        # Fallback: check if twitter is configured in sources.yaml
        config = self.event_service.sources_config.get("sources", [])
        twitter_sources = [s for s in config if s.get("name") == "twitter"]
        if twitter_sources:
            # Return default Twitter users for monitoring
            return [
                "vxunderground",
                "CERT_FR",
                "CISACyber",
                "shadowserver",
                "malware_traffic",
                "USCERT_gov",
            ]
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
