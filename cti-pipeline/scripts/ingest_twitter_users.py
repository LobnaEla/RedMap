from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time, json, os

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

DATA_DIR = "cti-pipeline/data/twitter"
os.makedirs(DATA_DIR, exist_ok=True)


def get_tweets_from_user(username, max_scrolls=5):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")

    driver = webdriver.Chrome(options=chrome_options)
    print(f"[🌐] Navigation vers https://twitter.com/{username}...")
    driver.get(f"https://twitter.com/{username}")
    time.sleep(5)

    tweets_data = []
    scrolls = 0

    while scrolls < max_scrolls:
        print(f"[↪] Scroll {scrolls + 1}/{max_scrolls}")
        tweet_blocks = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        for block in tweet_blocks:
            try:
                text_elem = block.find_element(
                    By.XPATH, './/div[@data-testid="tweetText"]'
                )
                text = text_elem.text.strip()

                timestamp_elem = block.find_element(By.XPATH, ".//time")
                timestamp = timestamp_elem.get_attribute("datetime")

                tweet_url = timestamp_elem.find_element(
                    By.XPATH, "./ancestor::a"
                ).get_attribute("href")

                if is_cti_relevant(text):
                    tweets_data.append(
                        {
                            "user": username,
                            "content": text,
                            "tweet_url": tweet_url,
                            "tweet_date": timestamp,
                            "collected_at": datetime.utcnow().isoformat(),
                        }
                    )

            except Exception:
                continue

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        scrolls += 1

    driver.quit()
    return tweets_data


def save_tweets(username, tweets):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    path = os.path.join(DATA_DIR, f"twitter_{username}_{now}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for tweet in tweets:
            json.dump(tweet, f, ensure_ascii=False)
            f.write("\n")
    print(f"[✔] {len(tweets)} tweets enregistrés dans {path}")


def is_cti_relevant(tweet_text):
    text = tweet_text.lower()
    return any(keyword.lower() in text for keyword in CTI_KEYWORDS)


if __name__ == "__main__":
    users = ["vxunderground", "CERT_FR", "CISACyber"]
    for user in users:
        print(f"[🔍] Collecte depuis @{user}...")
        tweets = get_tweets_from_user(user)
        save_tweets(user, tweets)
