"""
Event Monitoring Service for CTI Sources
Monitors external APIs, feeds, and triggers n8n webhooks
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import hashlib
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EventConfig:
    """Configuration for each source"""

    source_name: str
    check_interval: int  # seconds
    rate_limit: int  # minutes between triggers
    priority: str  # normal, high, critical
    enabled: bool = True


class BaseSourceMonitor(ABC):
    """Base class for source monitors"""

    def __init__(self, config: EventConfig, n8n_webhook_url: str):
        self.config = config
        self.n8n_url = n8n_webhook_url
        self.last_trigger = None
        self.last_state_hash = None

    @abstractmethod
    async def check_for_updates(self) -> Optional[Dict]:
        """Check if source has updates. Return event data if yes, None if no."""
        pass

    async def trigger_n8n_event(self, event_data: Dict) -> bool:
        """Send event to n8n webhook"""
        try:
            payload = {
                "source_name": self.config.source_name,
                "event_type": event_data.get("event_type", "data_update"),
                "reason": event_data.get("reason", "automated_check"),
                "priority": self.config.priority,
                "source_metadata": event_data.get("metadata", {}),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.n8n_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(
                            f"✅ {self.config.source_name}: Event triggered successfully"
                        )
                        self.last_trigger = datetime.now()
                        return True
                    else:
                        logger.error(
                            f"❌ {self.config.source_name}: n8n trigger failed - {response.status}"
                        )
                        return False

        except Exception as e:
            logger.error(f"❌ {self.config.source_name}: Failed to trigger n8n - {e}")
            return False

    def should_trigger(self) -> bool:
        """Check if enough time has passed since last trigger"""
        if not self.last_trigger:
            return True

        time_since_trigger = datetime.now() - self.last_trigger
        cooldown = timedelta(minutes=self.config.rate_limit)
        return time_since_trigger >= cooldown

    def get_state_hash(self, data: str) -> str:
        """Generate hash of current state for change detection"""
        return hashlib.md5(data.encode()).hexdigest()


class OTXMonitor(BaseSourceMonitor):
    """Monitor AlienVault OTX for new pulses"""

    def __init__(self, config: EventConfig, n8n_webhook_url: str, api_key: str):
        super().__init__(config, n8n_webhook_url)
        self.api_key = api_key
        self.base_url = "https://otx.alienvault.com/api/v1"

    async def check_for_updates(self) -> Optional[Dict]:
        try:
            headers = {"X-OTX-API-KEY": self.api_key}

            # Check for recent pulses (last hour)
            since = (datetime.now() - timedelta(hours=1)).isoformat()
            url = f"{self.base_url}/pulses/subscribed?modified_since={since}&limit=50"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        pulse_count = len(data.get("results", []))

                        if pulse_count > 0:
                            # Create state hash to avoid duplicate triggers
                            state_data = json.dumps(
                                data.get("results", []), sort_keys=True
                            )
                            current_hash = self.get_state_hash(state_data)

                            if current_hash != self.last_state_hash:
                                self.last_state_hash = current_hash

                                return {
                                    "event_type": "new_pulses",
                                    "reason": "otx_api_check",
                                    "metadata": {
                                        "pulse_count": pulse_count,
                                        "check_timestamp": datetime.now().isoformat(),
                                        "categories": list(
                                            {
                                                p.get("name", "").split()[0]
                                                for p in data.get("results", [])
                                            }
                                        )[:5],
                                    },
                                }

        except Exception as e:
            logger.error(f"❌ OTX check failed: {e}")

        return None


class RSSMonitor(BaseSourceMonitor):
    """Monitor RSS feeds for new security content"""

    def __init__(self, config: EventConfig, n8n_webhook_url: str, rss_feeds: List[str]):
        super().__init__(config, n8n_webhook_url)
        self.rss_feeds = rss_feeds
        self.keywords = [
            "vulnerability",
            "exploit",
            "malware",
            "apt",
            "zero-day",
            "cve",
        ]

    async def check_for_updates(self) -> Optional[Dict]:
        try:
            import feedparser

            new_articles = []
            since_time = datetime.now() - timedelta(hours=2)

            for feed_url in self.rss_feeds:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(feed_url, timeout=30) as response:
                            if response.status == 200:
                                content = await response.text()
                                feed = feedparser.parse(content)

                                for entry in feed.entries:
                                    pub_date = datetime(*entry.published_parsed[:6])

                                    if pub_date > since_time:
                                        # Check for security-related keywords
                                        title_lower = entry.title.lower()
                                        summary_lower = entry.get("summary", "").lower()

                                        matched_keywords = [
                                            kw
                                            for kw in self.keywords
                                            if kw in title_lower or kw in summary_lower
                                        ]

                                        if matched_keywords:
                                            new_articles.append(
                                                {
                                                    "title": entry.title,
                                                    "url": entry.link,
                                                    "keywords": matched_keywords,
                                                    "published": pub_date.isoformat(),
                                                }
                                            )

                except Exception as e:
                    logger.warning(f"Failed to parse RSS feed {feed_url}: {e}")

            if new_articles:
                return {
                    "event_type": "new_articles",
                    "reason": "rss_monitoring",
                    "metadata": {
                        "article_count": len(new_articles),
                        "articles": new_articles[:5],  # Limit to first 5
                        "keywords_found": list(
                            set(
                                [
                                    kw
                                    for article in new_articles
                                    for kw in article["keywords"]
                                ]
                            )
                        ),
                        "check_timestamp": datetime.now().isoformat(),
                    },
                }

        except Exception as e:
            logger.error(f"❌ RSS check failed: {e}")

        return None


class TunCERTMonitor(BaseSourceMonitor):
    """Monitor TunCERT for new vulnerability advisories"""

    def __init__(self, config: EventConfig, n8n_webhook_url: str):
        super().__init__(config, n8n_webhook_url)
        self.base_url = "https://www.tuncert.tn"  # Adjust based on actual API

    async def check_for_updates(self) -> Optional[Dict]:
        try:
            # This would need to be adapted to TunCERT's actual API/RSS
            # For now, simulate checking for new advisories

            async with aiohttp.ClientSession() as session:
                # Example: Check RSS feed or API endpoint
                url = f"{self.base_url}/api/advisories/recent"  # Hypothetical

                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        new_advisories = [
                            adv
                            for adv in data.get("advisories", [])
                            if self._is_recent(adv.get("published_date"))
                        ]

                        if new_advisories:
                            return {
                                "event_type": "new_advisories",
                                "reason": "tuncert_monitoring",
                                "metadata": {
                                    "advisory_count": len(new_advisories),
                                    "severity_levels": [
                                        adv.get("severity") for adv in new_advisories
                                    ],
                                    "cve_ids": [
                                        adv.get("cve_id")
                                        for adv in new_advisories
                                        if adv.get("cve_id")
                                    ],
                                    "check_timestamp": datetime.now().isoformat(),
                                },
                            }

        except Exception as e:
            logger.error(f"❌ TunCERT check failed: {e}")

        return None

    def _is_recent(self, date_str: str) -> bool:
        """Check if advisory is from last 24 hours"""
        try:
            pub_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return (datetime.now() - pub_date).days < 1
        except:
            return False


class TwitterMonitor(BaseSourceMonitor):
    """Monitor Twitter users for threat intelligence tweets"""

    def __init__(self, config: EventConfig, n8n_webhook_url: str, twitter_api_key: str):
        super().__init__(config, n8n_webhook_url)
        self.api_key = twitter_api_key
        self.threat_intel_keywords = [
            "IOC",
            "malware",
            "C2",
            "APT",
            "threat",
            "vulnerability",
            "exploit",
            "phishing",
            "ransomware",
            "backdoor",
        ]
        self.monitored_users = [
            "malware_traffic",
            "threatintel",
            "vxunderground",
            "bad_packets",
            "cyber_feed",
        ]

    async def check_for_updates(self) -> Optional[Dict]:
        try:
            # Note: Twitter API v2 requires different authentication
            headers = {"Authorization": f"Bearer {self.api_key}"}

            # Search for recent tweets from monitored users with threat intel keywords
            query = f"from:{' OR from:'.join(self.monitored_users)} ({' OR '.join(self.threat_intel_keywords)})"
            url = f"https://api.twitter.com/2/tweets/search/recent"

            params = {
                "query": query,
                "max_results": 50,
                "tweet.fields": "created_at,author_id,public_metrics",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, params=params, timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        tweets = data.get("data", [])

                        # Filter tweets from last 2 hours
                        recent_tweets = []
                        cutoff_time = datetime.now() - timedelta(hours=2)

                        for tweet in tweets:
                            tweet_time = datetime.fromisoformat(
                                tweet["created_at"].replace("Z", "+00:00")
                            )
                            if tweet_time > cutoff_time:
                                recent_tweets.append(tweet)

                        if recent_tweets:
                            return {
                                "event_type": "threat_intel_tweets",
                                "reason": "twitter_monitoring",
                                "metadata": {
                                    "tweet_count": len(recent_tweets),
                                    "high_engagement_tweets": [
                                        t
                                        for t in recent_tweets
                                        if t.get("public_metrics", {}).get(
                                            "retweet_count", 0
                                        )
                                        > 10
                                    ][:3],
                                    "keywords_found": self.threat_intel_keywords,
                                    "check_timestamp": datetime.now().isoformat(),
                                },
                            }

        except Exception as e:
            logger.error(f"❌ Twitter check failed: {e}")

        return None


class BlogMonitor(BaseSourceMonitor):
    """Monitor security blogs for new threat analysis"""

    def __init__(self, config: EventConfig, n8n_webhook_url: str, blog_urls: List[str]):
        super().__init__(config, n8n_webhook_url)
        self.blog_urls = blog_urls
        self.threat_keywords = [
            "mitre",
            "att&ck",
            "ttp",
            "apt",
            "threat analysis",
            "malware analysis",
            "incident response",
            "ioc",
        ]

    async def check_for_updates(self) -> Optional[Dict]:
        try:
            new_posts = []

            for blog_url in self.blog_urls:
                try:
                    async with aiohttp.ClientSession() as session:
                        # Try RSS first, then HTML scraping
                        rss_url = (
                            f"{blog_url}/rss"
                            if not blog_url.endswith("/rss")
                            else blog_url
                        )

                        async with session.get(rss_url, timeout=30) as response:
                            if response.status == 200:
                                import feedparser

                                content = await response.text()
                                feed = feedparser.parse(content)

                                cutoff_time = datetime.now() - timedelta(hours=6)

                                for entry in feed.entries:
                                    try:
                                        pub_date = datetime(*entry.published_parsed[:6])

                                        if pub_date > cutoff_time:
                                            title_lower = entry.title.lower()
                                            summary_lower = entry.get(
                                                "summary", ""
                                            ).lower()

                                            # Check for threat intel relevance
                                            matched_keywords = [
                                                kw
                                                for kw in self.threat_keywords
                                                if kw in title_lower
                                                or kw in summary_lower
                                            ]

                                            if matched_keywords:
                                                new_posts.append(
                                                    {
                                                        "title": entry.title,
                                                        "url": entry.link,
                                                        "blog_source": blog_url,
                                                        "keywords": matched_keywords,
                                                        "published": pub_date.isoformat(),
                                                    }
                                                )
                                    except:
                                        continue

                except Exception as e:
                    logger.warning(f"Failed to check blog {blog_url}: {e}")

            if new_posts:
                return {
                    "event_type": "threat_analysis",
                    "reason": "blog_monitoring",
                    "metadata": {
                        "post_count": len(new_posts),
                        "posts": new_posts[:3],  # Limit to first 3
                        "sources": list(
                            set([post["blog_source"] for post in new_posts])
                        ),
                        "check_timestamp": datetime.now().isoformat(),
                    },
                }

        except Exception as e:
            logger.error(f"❌ Blog check failed: {e}")

        return None


class EventOrchestrator:
    """Main orchestrator for all source monitors"""

    def __init__(self, n8n_webhook_url: str):
        self.n8n_url = n8n_webhook_url
        self.monitors: List[BaseSourceMonitor] = []
        self.running = False

    def add_monitor(self, monitor: BaseSourceMonitor):
        """Add a source monitor"""
        self.monitors.append(monitor)
        logger.info(f"Added monitor for {monitor.config.source_name}")

    async def run_monitor(self, monitor: BaseSourceMonitor):
        """Run a single monitor continuously"""
        while self.running:
            try:
                if not monitor.config.enabled:
                    await asyncio.sleep(monitor.config.check_interval)
                    continue

                logger.debug(f"Checking {monitor.config.source_name}...")

                # Check for updates
                event_data = await monitor.check_for_updates()

                if event_data and monitor.should_trigger():
                    logger.info(f"🎯 {monitor.config.source_name}: New event detected")
                    await monitor.trigger_n8n_event(event_data)
                elif event_data:
                    logger.info(
                        f"⏰ {monitor.config.source_name}: Event detected but rate limited"
                    )

                await asyncio.sleep(monitor.config.check_interval)

            except Exception as e:
                logger.error(f"❌ Error in {monitor.config.source_name} monitor: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def start(self):
        """Start all monitors"""
        self.running = True
        logger.info(
            f"🚀 Starting event orchestrator with {len(self.monitors)} monitors"
        )

        # Start all monitors concurrently
        tasks = [
            asyncio.create_task(self.run_monitor(monitor)) for monitor in self.monitors
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.running = False

            # Cancel all tasks
            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)


# === Configuration and Main ===


def create_orchestrator() -> EventOrchestrator:
    """Create and configure the event orchestrator"""

    N8N_WEBHOOK_URL = "http://localhost:5678/webhook/cti-event"

    orchestrator = EventOrchestrator(N8N_WEBHOOK_URL)

    # OTX Monitor
    otx_config = EventConfig(
        source_name="otx",
        check_interval=3600,  # 1 hour
        rate_limit=60,  # 1 hour cooldown
        priority="high",
    )
    if OTX_API_KEY := "your-otx-api-key":  # Set your API key
        orchestrator.add_monitor(OTXMonitor(otx_config, N8N_WEBHOOK_URL, OTX_API_KEY))

    # RSS Monitor
    rss_config = EventConfig(
        source_name="rss",
        check_interval=1800,  # 30 minutes
        rate_limit=30,  # 30 minutes cooldown
        priority="normal",
    )
    rss_feeds = [
        "https://feeds.feedburner.com/eset/blog",
        "https://www.schneier.com/blog/atom.xml",
        "https://krebsonsecurity.com/feed/",
        "https://threatpost.com/feed/",
    ]
    orchestrator.add_monitor(RSSMonitor(rss_config, N8N_WEBHOOK_URL, rss_feeds))

    # TunCERT Monitor
    tuncert_config = EventConfig(
        source_name="tuncert",
        check_interval=7200,  # 2 hours
        rate_limit=120,  # 2 hours cooldown
        priority="high",
    )
    orchestrator.add_monitor(TunCERTMonitor(tuncert_config, N8N_WEBHOOK_URL))

    # Twitter Monitor
    twitter_config = EventConfig(
        source_name="twitter",
        check_interval=900,  # 15 minutes
        rate_limit=15,  # 15 minutes cooldown
        priority="normal",
    )
    if TWITTER_API_KEY := "your-twitter-api-key":  # Set your API key
        orchestrator.add_monitor(
            TwitterMonitor(twitter_config, N8N_WEBHOOK_URL, TWITTER_API_KEY)
        )

    # Blog Monitor
    blog_config = EventConfig(
        source_name="blog",
        check_interval=2700,  # 45 minutes
        rate_limit=45,  # 45 minutes cooldown
        priority="normal",
    )
    security_blogs = [
        "https://blog.malwarebytes.com",
        "https://blog.trendmicro.com",
        "https://unit42.paloaltonetworks.com",
        "https://www.fireeye.com/blog/threat-research",
    ]
    orchestrator.add_monitor(BlogMonitor(blog_config, N8N_WEBHOOK_URL, security_blogs))

    return orchestrator


async def main():
    """Main entry point"""
    orchestrator = create_orchestrator()
    await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(main())
