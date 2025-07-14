import logging
import os
import json
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

from cti_pipeline.scripts.utilities import (
    get_content_hash,
    load_processed_items,
    save_processed_items,
    is_duplicate,
    DATA_DIR,
    METADATA_DIR,
    PDF_DIR,
)

logger = logging.getLogger(__name__)
from cti_pipeline.blog_sources import BLOG_SOURCES

DATA_DIR = "cti_pipeline/data/blogs"
os.makedirs(DATA_DIR, exist_ok=True)

IGNORED_SUBSTRINGS = [
    "x.com",
    "twitter.com",
    "tv.paloaltonetworks.com",
    "youtube.com",
    "linkedin.com",
    "facebook.com",
]

CTI_KEYWORDS = [
    "advanced persistent threat",
    "malware",
    "cve",
    "ioc",
    "threat actor",
    "vulnerability",
    "phishing",
    "exploit",
    "ransomware",
    "tactics",
    "mitre",
]

logger = logging.getLogger(__name__)


def extract_article_links(
    index_url: str, domain_filter: Optional[str] = None
) -> List[str]:
    """Pure function to extract article links from a blog index page"""
    try:
        response = requests.get(index_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        return list(
            {
                urljoin(index_url, a["href"])
                for a in soup.find_all("a", href=True)
                if _is_valid_link(a["href"], index_url)
            }
        )

    except Exception as e:
        logger.error(f"Failed to extract links from {index_url}: {str(e)}")
        return []


from urllib.parse import urlparse


def _is_valid_link(href: str, base_url: str) -> bool:
    """Helper function to validate links"""
    parsed = urlparse(href)
    if parsed.scheme not in ["http", "https", ""]:
        return False

    if href.startswith("#") or href.startswith("mailto:"):
        return False

    if any(bad in href for bad in IGNORED_SUBSTRINGS):
        return False

    domain = base_url.lower()
    if "medium.com" in domain:
        return True

    return any(kw in href.lower() for kw in ["threat", "report", "malware", "blog"])


def extract_article_content(url: str, source_name: str = "generic") -> Optional[str]:
    """Pure function to extract and validate article content"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        text = _extract_main_content(soup)
        if not _contains_cti_content(text, url, source_name):
            return None

        return "\n".join(line.strip() for line in text.splitlines() if line.strip())

    except Exception as e:
        logger.error(f"Failed to extract content from {url}: {str(e)}")
        return None


def _extract_main_content(soup: BeautifulSoup) -> str:
    """Extracts main content from different HTML structures"""
    for tag in ["article", "main", "div.content", "body"]:
        element = soup.select_one(tag) if "." in tag else soup.find(tag)
        if element:
            return element.get_text(separator="\n")
    return soup.get_text(separator="\n")


def _contains_cti_content(text: str, url: str, source_name: str) -> bool:
    """Validates if content is CTI-relevant"""
    if "medium.com" in url or "medium" in source_name.lower():
        title = BeautifulSoup(text, "html.parser").title
        if title and "cti report" not in title.get_text().lower():
            return False

    lowered = text.lower()
    return any(keyword in lowered for keyword in CTI_KEYWORDS)


def process_blog_source(blog_config: Dict, data_dir: str, metadata_dir: str) -> int:
    """
    Processes a single blog source
    Returns number of new articles processed
    """
    blog_name = blog_config["name"]
    processed_data = load_processed_items("blogs")
    blog_state = processed_data.get(blog_name, {"urls": [], "hashes": []})

    new_articles = []
    links = extract_article_links(blog_config["url"])

    for url in links:
        if url in blog_state["urls"]:
            continue

        content = extract_article_content(url, blog_name)
        if not content:
            continue

        if is_duplicate(content, url, blog_state, "blog"):
            continue

        new_articles.append(
            {
                "url": url,
                "source": blog_name,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

        blog_state["urls"].append(url)
        blog_state["hashes"].append(get_content_hash(content, "blog"))

    if new_articles:
        _save_articles(new_articles, blog_name, data_dir)
        processed_data[blog_name] = blog_state
        save_processed_items("blogs", processed_data)

    return len(new_articles)


def _save_articles(articles: List[Dict], blog_name: str, output_dir: str):
    """Saves articles to a dated JSONL file"""
    filename = f"blog_{blog_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"
    with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
        for article in articles:
            json.dump(article, f, ensure_ascii=False)
            f.write("\n")


def ingest_all_blog(blog_sources: List[Dict], data_dir: str, metadata_dir: str):
    total_processed = 0
    for blog in blog_sources:
        count = process_blog_source(blog, DATA_DIR, METADATA_DIR)
        total_processed += count
        logger.info(f"Processed {count} new articles from {blog['name']}")
    logger.info(f"✅ Total: {total_processed} new blog articles collected")
    return total_processed


if __name__ == "__main__":
    ingest_all_blog(BLOG_SOURCES, DATA_DIR, METADATA_DIR)
    print("[✔] Blog scraping completed.")
