import logging
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time, json, os

from cti_pipeline.scripts.utilities import (
    get_content_hash,
    load_processed_items,
    save_processed_items,
    is_duplicate,
    METADATA_DIR,
    PDF_DIR,
)

logger = logging.getLogger(__name__)

CTI_KEYWORDS = [
    "APT",
    "CVE",
    "exploit",
    "IOC",
    "phishing",
    "ransomware",
    "malware",
    "TTP",
    "TTPs",
    "MITRE",
    "threat",
    "vulnerability",
    "attack",
]

DATA_DIR = "cti_pipeline/data/twitter"
os.makedirs(DATA_DIR, exist_ok=True)


def initialize_driver() -> webdriver.Chrome:
    """Initialise et retourne le WebDriver Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")
    return webdriver.Chrome(options=chrome_options)


def extract_tweet_data(tweet_element) -> Optional[Dict]:
    """Extrait les données d'un tweet individuel"""
    try:
        text_elem = tweet_element.find_element(
            By.XPATH, './/div[@data-testid="tweetText"]'
        )
        timestamp_elem = tweet_element.find_element(By.XPATH, ".//time")
        tweet_url = timestamp_elem.find_element(
            By.XPATH, "./ancestor::a"
        ).get_attribute("href")

        return {
            "content": text_elem.text.strip(),
            "tweet_url": tweet_url,
            "tweet_date": timestamp_elem.get_attribute("datetime"),
            "collected_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.debug(f"Failed to extract tweet data: {str(e)}")
        return None


def is_cti_relevant(text: str) -> bool:
    """Vérifie si le tweet contient des mots-clés CTI"""
    lower_text = text.lower()
    return any(keyword.lower() in lower_text for keyword in CTI_KEYWORDS)


def scrape_user_tweets(username: str, max_scrolls: int = 3) -> List[Dict]:
    """Récupère les tweets d'un utilisateur avec scroll"""
    driver = initialize_driver()
    tweets_data = []

    try:
        logger.info(f"Scraping tweets from @{username}")
        driver.get(f"https://twitter.com/{username}")
        time.sleep(5)

        for scroll in range(max_scrolls):
            logger.debug(f"Scroll {scroll + 1}/{max_scrolls}")
            tweet_blocks = driver.find_elements(
                By.XPATH, '//article[@data-testid="tweet"]'
            )

            for block in tweet_blocks:
                tweet = extract_tweet_data(block)
                if tweet and is_cti_relevant(tweet["content"]):
                    tweet["user"] = username
                    tweets_data.append(tweet)

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

    finally:
        driver.quit()

    return tweets_data


def process_user_tweets(username: str, processed_data: Dict) -> List[Dict]:
    """Traite les tweets d'un utilisateur avec gestion des doublons"""
    user_state = processed_data.get(username, {"tweet_hashes": [], "tweet_urls": []})
    new_tweets = []

    try:
        tweets = scrape_user_tweets(username)
        for tweet in tweets:
            content_str = json.dumps(tweet, sort_keys=True)
            url = tweet["tweet_url"]

            if is_duplicate(
                content_str,
                url,
                {
                    "hashes": user_state["tweet_hashes"],
                    "urls": user_state["tweet_urls"],
                },
            ):
                logger.debug(f"Tweet déjà traité: {url}")
                continue

            content_hash = get_content_hash(content_str)
            tweet["hash"] = content_hash
            new_tweets.append(tweet)
            user_state["tweet_hashes"].append(content_hash)
            user_state["tweet_urls"].append(url)

    except Exception as e:
        logger.error(f"Failed to process tweets for @{username}: {str(e)}")

    return new_tweets, user_state


def save_twitter_data(tweets: List[Dict], username: str, data_dir: str):
    """Sauvegarde les tweets dans un fichier JSONL"""
    if not tweets:
        return

    output_file = os.path.join(
        data_dir, f"twitter_{username}_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        for tweet in tweets:
            json.dump(tweet, f, ensure_ascii=False)
            f.write("\n")


def ingest_all_twitter_users(
    users: List[str], data_dir: str, metadata_dir: str
) -> Dict[str, int]:
    """Point d'entrée principal pour l'ingestion Twitter"""
    stats = {"processed": 0, "users": len(users)}
    processed_data = load_processed_items("twitter")

    for username in users:
        try:
            new_tweets, user_state = process_user_tweets(username, processed_data)
            if new_tweets:
                save_twitter_data(new_tweets, username, data_dir)
                processed_data[username] = user_state
                stats["processed"] += len(new_tweets)

            logger.info(f"Processed {len(new_tweets)} new tweets from @{username}")
        except Exception as e:
            logger.error(f"Failed to ingest tweets for @{username}: {str(e)}")
            continue

    save_processed_items("twitter", processed_data)
    return stats


if __name__ == "__main__":
    twitter_users = ["vxunderground", "CERT_FR", "CISACyber"]
    stats = ingest_all_twitter_users(twitter_users, DATA_DIR, METADATA_DIR)
    print(f"[+] Processed {stats['processed']} new tweets from {stats['users']} users.")
