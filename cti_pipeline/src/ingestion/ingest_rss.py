import json
import os
import feedparser
from datetime import datetime
from typing import Dict, List, Optional
from cti_pipeline.src.utilities import (
    load_processed_items,
    save_processed_items,
    is_duplicate,
    get_content_hash,
    DATA_DIR,
    METADATA_DIR,
)


CERT_FR_RSS_URL = "https://www.cert.ssi.gouv.fr/feed/"


def fetch_rss_feed() -> Optional[feedparser.FeedParserDict]:
    """Fetches and parses the CERT-FR RSS feed"""
    try:
        return feedparser.parse(CERT_FR_RSS_URL)
    except Exception as e:
        return None


def process_rss_entry(entry: Dict, processed_data: Dict) -> Optional[Dict]:
    """Processes single RSS entry with duplicate check"""
    content = entry.get("summary", "")
    url = entry.link

    if is_duplicate(content, url, processed_data, "rss"):
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
    processed_data = load_processed_items("rss_certfr")
    feed = fetch_rss_feed()

    if not feed or not feed.entries:
        return stats

    stats["total"] = len(feed.entries)
    
    # Create structured directory for RSS data
    rss_dir = os.path.join(data_dir, "raw_scraped_data", "rss")
    os.makedirs(rss_dir, exist_ok=True)
    
    output_file = f"raw_rss_certfr_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"

    with open(os.path.join(rss_dir, output_file), "w", encoding="utf-8") as f:
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

    save_processed_items("rss_certfr", processed_data)
    return stats


if __name__ == "__main__":
    results = ingest_certfr_rss(DATA_DIR, METADATA_DIR)
    print("[✔] RSS feed ingestion completed.")
