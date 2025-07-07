import os
import json
from datetime import datetime
import feedparser

DATA_DIR = "cti_pipeline/data/"


### Ingestion des flux RSS de CERT-FR
def ingest_rss(output_file="raw_rss_certfr.jsonl"):
    url = "https://www.cert.ssi.gouv.fr/feed/"
    feed = feedparser.parse(url)

    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, output_file)

    with open(path, "a", encoding="utf-8") as f:
        for entry in feed.entries:
            doc = {
                "source": "CERT-FR RSS",
                "type": "rss_bulletin",
                "title": entry.title,
                "link": entry.link,
                "date_published": entry.published,
                "content": entry.get("summary", ""),
                "date_collected": str(datetime.now()),
            }
            json.dump(doc, f, ensure_ascii=False)
            f.write("\n")

    print(f"[+] {len(feed.entries)} bulletins RSS CERT-FR collectés.")


if __name__ == "__main__":
    ingest_rss()
    print("[✔] Ingestion des flux RSS terminée.")
