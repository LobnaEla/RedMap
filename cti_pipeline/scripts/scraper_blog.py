import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

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


def extract_article_links(index_url, domain_filter=None):
    """Retrieves all article links from the blog's homepage."""
    try:
        r = requests.get(index_url)
        r.raise_for_status()
    except Exception as e:
        print(f"[❌] Failed to access {index_url}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#"):
            continue
        full_url = urljoin(index_url, href)
        if any(bad in full_url for bad in IGNORED_SUBSTRINGS):
            continue  # 🔥 link to ignore
        if domain_filter and domain_filter not in full_url:
            continue
        if not any(
            kw in full_url.lower() for kw in ["threat", "report", "malware", "blog"]
        ):
            continue
        links.append(full_url)

    return list(set(links))  # Remove duplicates


def extract_text_from_url(url, source_name="generic"):
    """Extracts raw text from an article, with Medium or keyword filtering."""
    try:
        r = requests.get(url)
        r.raise_for_status()
    except Exception as e:
        print(f"[❌] Failed to retrieve article {url}: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # 📌 Title filtering ONLY for Medium
    if "medium.com" in url or "medium" in source_name.lower():
        title_tag = soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else ""
        if "cti report" not in title_text.lower():
            print(f"[⏩] Skipped (irrelevant Medium title): {title_text}")
            return None
    else:
        # 📌 For others: extract text and filter by keywords
        article = soup.find("article") or soup.find("main") or soup.find("body")
        text = (
            article.get_text(separator="\n")
            if article
            else soup.get_text(separator="\n")
        )
        cleaned = "\n".join(
            [line.strip() for line in text.splitlines() if line.strip()]
        )
        lowered_text = cleaned.lower()

        if not any(keyword in lowered_text for keyword in CTI_KEYWORDS):
            print(f"[⏩] Skipped (no CTI keyword found in article): {url}")
            return None

        return cleaned

    # 👇 If it's Medium and title filter passed
    article = soup.find("article") or soup.find("main") or soup.find("body")
    text = (
        article.get_text(separator="\n") if article else soup.get_text(separator="\n")
    )
    cleaned = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    return cleaned


def scrape_blog(index_url, blog_name="generic"):
    """Scrapes CTI blog articles and saves them in a JSONL file."""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    out_file = os.path.join(DATA_DIR, f"{blog_name}_{now}.jsonl")
    links = extract_article_links(index_url)

    print(f"[🔎] {len(links)} links detected on {index_url}")

    count = 0
    with open(out_file, "w", encoding="utf-8") as f:
        for url in links:
            text = extract_text_from_url(url, source_name=blog_name)
            if text:
                doc = {
                    "url": url,
                    "source": blog_name,
                    "format": "HTML",
                    "date": str(datetime.now()),
                    "content": text,
                }
                json.dump(doc, f, ensure_ascii=False)
                f.write("\n")
                count += 1

    print(f"[✅] {count} articles saved in {out_file}")


if __name__ == "__main__":
    from cti_pipeline.blog_sources import BLOG_SOURCES

    for source in BLOG_SOURCES:
        print(f"[🌐] Scraping {source['name']}...")
        scrape_blog(source["url"], blog_name=source["name"])
    print("[✔] Blog scraping completed.")
