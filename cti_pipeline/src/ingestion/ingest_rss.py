import json
import os
import feedparser
from datetime import datetime
from typing import Dict, List, Optional
from ..utilities import (
    load_processed_items,
    save_processed_items,
    is_duplicate,
    get_content_hash,
    DATA_DIR,
    METADATA_DIR,
)
from config.rss_sources import RSS_SOURCES


def get_source_by_name(name: str) -> Optional[Dict]:
    """Returns a specific RSS source by name"""
    return next((source for source in RSS_SOURCES if source["name"] == name), None)


def fetch_rss_feed(rss_url: str) -> Optional[feedparser.FeedParserDict]:
    """Fetches and parses an RSS feed from the given URL"""
    try:
        return feedparser.parse(rss_url)
    except Exception as e:
        print(f"Error fetching RSS feed from {rss_url}: {str(e)}")
        return None


def process_rss_entry(
    entry: Dict, processed_data: Dict, source_config: Dict
) -> Optional[Dict]:
    """Processes single RSS entry with duplicate check"""
    content = entry.get("summary", "")
    url = entry.link

    if is_duplicate(content, url, processed_data, "rss"):
        return None

    return {
        "source": source_config.get("description", source_config["name"]),
        "source_name": source_config["name"],
        "source_type": source_config.get("source_type", "rss_feed"),
        "type": "rss_bulletin",
        "title": entry.title,
        "link": url,
        "date_published": entry.published,
        "content": content,
        "date_collected": datetime.now().isoformat(),
    }


def ingest_single_rss_source(
    source_config: Dict, data_dir: str, metadata_dir: str
) -> Dict[str, int]:
    """Ingest RSS data from a single source"""
    stats = {"processed": 0, "total": 0, "source": source_config["name"]}

    # Load processed items for this specific source
    processed_data = load_processed_items(f"rss_{source_config['name']}")

    # Fetch the RSS feed
    feed = fetch_rss_feed(source_config["url"])

    if not feed or not feed.entries:
        print(f"No entries found for RSS source: {source_config['name']}")
        return stats

    stats["total"] = len(feed.entries)

    # Create structured directory for RSS data
    rss_dir = os.path.join(data_dir, "raw_scraped_data", "rss")
    os.makedirs(rss_dir, exist_ok=True)

    # First pass: collect valid documents
    valid_docs = []
    for entry in feed.entries:
        doc = process_rss_entry(entry, processed_data, source_config)
        if doc:
            valid_docs.append(doc)
            # Update processed items
            processed_data.setdefault("hashes", []).append(
                get_content_hash(doc["content"], "rss")
            )
            processed_data.setdefault("urls", []).append(doc["link"])
            stats["processed"] += 1

    # Only create file if we have valid documents to save
    if valid_docs:
        output_file = f"raw_rss_{source_config['name']}_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"
        
        with open(os.path.join(rss_dir, output_file), "w", encoding="utf-8") as f:
            for doc in valid_docs:
                json.dump(doc, f, ensure_ascii=False)
                f.write("\n")
        
        print(f"[RSS] Saved {len(valid_docs)} new entries from {source_config['name']}")
    else:
        print(f"[RSS] No new entries to save from {source_config['name']} - all were duplicates or invalid")

    # Only save processed items if we actually processed something new
    if stats["processed"] > 0:
        save_processed_items(f"rss_{source_config['name']}", processed_data)
    return stats


def ingest_rss(
    data_dir: str = DATA_DIR,
    metadata_dir: str = METADATA_DIR,
) -> Dict:
    """
    Main RSS ingestion function for Airflow DAG

    Args:
        data_dir: Directory to store scraped data (defaults to DATA_DIR from utilities)
        metadata_dir: Directory to store metadata (defaults to METADATA_DIR from utilities)

    Returns:
        Dict with ingestion statistics and results
    """
    all_stats = {
        "sources": [],
        "total_processed": 0,
        "total_entries": 0,
        "success": True,
        "errors": [],
    }

    # If no specific sources provided, use all sources
    sources_to_process = RSS_SOURCES

    # Process each RSS source
    for source_config in sources_to_process:
        try:
            stats = ingest_single_rss_source(source_config, data_dir, metadata_dir)
            all_stats["sources"].append(stats)
            all_stats["total_processed"] += stats["processed"]
            all_stats["total_entries"] += stats["total"]
            print(
                f"✓ {source_config['name']}: {stats['processed']}/{stats['total']} entries processed"
            )
        except Exception as e:
            error_stats = {
                "processed": 0,
                "total": 0,
                "source": source_config["name"],
                "error": str(e),
            }
            all_stats["sources"].append(error_stats)
            all_stats["errors"].append(f"{source_config['name']}: {str(e)}")
            all_stats["success"] = False
            print(f"✗ {source_config['name']}: Error - {str(e)}")

    return all_stats


if __name__ == "__main__":
    print("Starting RSS ingestion...")

    try:
        results = ingest_rss()
        print(
            f"RSS ingestion completed: {results['total_processed']}/{results['total_entries']} entries processed"
        )
    except Exception as e:
        print(f"RSS ingestion failed: {str(e)}")

    print("Done.")
