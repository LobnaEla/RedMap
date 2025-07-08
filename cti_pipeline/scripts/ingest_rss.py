import json
import logging
import os
import feedparser
from datetime import datetime
from typing import Dict, List, Optional
from cti_pipeline.scripts.utilities import (
    load_processed_items,
    save_processed_items,
    is_duplicate,
    get_content_hash,
    DATA_DIR,
    METADATA_DIR,
)

logger = logging.getLogger(__name__)

CERT_FR_RSS_URL = "https://www.cert.ssi.gouv.fr/feed/"


def fetch_rss_feed() -> Optional[feedparser.FeedParserDict]:
    """Fetches and parses the CERT-FR RSS feed"""
    try:
        return feedparser.parse(CERT_FR_RSS_URL)
    except Exception as e:
        logger.error(f"Failed to fetch RSS feed: {str(e)}")
        return None


def process_rss_entry(entry: Dict, processed_data: Dict) -> Optional[Dict]:
    """Processes single RSS entry with duplicate check"""
    content = entry.get("summary", "")
    url = entry.link

    if is_duplicate(content, url, processed_data, "rss"):
        logger.debug(f"Skipping duplicate entry: {url}")
        return None

    return {
        "source": "CERT-FR RSS",
        "type": "rss_bulletin",
        "title": entry.title,
        "link": url,
        "date_published": entry.published,
        "content": content,
        "date_collected": datetime.now().isoformat(),
    }


def ingest_certfr_rss(data_dir: str, metadata_dir: str) -> Dict[str, int]:
    """Main RSS ingestion function with state management"""
    stats = {"processed": 0, "total": 0}
    processed_data = load_processed_items("rss_certfr", metadata_dir)
    feed = fetch_rss_feed()

    if not feed or not feed.entries:
        return stats

    stats["total"] = len(feed.entries)
    output_file = f"raw_rss_certfr_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"

    with open(os.path.join(data_dir, output_file), "w", encoding="utf-8") as f:
        for entry in feed.entries:
            doc = process_rss_entry(entry, processed_data)
            if not doc:
                continue

            json.dump(doc, f, ensure_ascii=False)
            f.write("\n")

            # Update processed items
            processed_data.setdefault("hashes", []).append(
                get_content_hash(doc["content"], "rss")
            )
            processed_data.setdefault("urls", []).append(doc["link"])
            stats["processed"] += 1

    save_processed_items("rss_certfr", processed_data, metadata_dir)
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = ingest_certfr_rss(DATA_DIR, METADATA_DIR)
    print("[✔] RSS feed ingestion completed.")
