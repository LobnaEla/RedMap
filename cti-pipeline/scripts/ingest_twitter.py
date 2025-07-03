import requests
from datetime import datetime
import json
from dotenv import load_dotenv
import time
import os

# Load environment variables from config/.env
load_dotenv(dotenv_path="cti-pipeline/config/.env")

BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

if not BEARER_TOKEN:
    raise Exception(
        "❌ Twitter Bearer Token not found. Make sure it's set in config/.env"
    )


def search_tweets(query, label="keyword", max_results=20):
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    url = (
        f"https://api.twitter.com/2/tweets/search/recent?"
        f"query={query}&max_results={max_results}&tweet.fields=author_id,created_at,text"
    )

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if response.status_code == 429:
            print("[-] Rate limit reached. Waiting 60s before retry...")
            time.sleep(60)
            return
        else:
            raise

    tweets = response.json().get("data", [])
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_dir = "cti-pipeline/data/twitter"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"twitter_keyword_{label}_{now}.jsonl")

    with open(filename, "w", encoding="utf-8") as f:
        for tweet in tweets:
            json.dump(tweet, f)
            f.write("\n")

    print(f"[✅] {len(tweets)} tweets saved to {filename}")
