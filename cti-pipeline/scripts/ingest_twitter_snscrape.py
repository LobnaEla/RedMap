import snscrape.modules.twitter as sntwitter
import json
import os
from datetime import datetime

DATA_DIR = "cti-pipeline/data/twitter"
os.makedirs(DATA_DIR, exist_ok=True)


def scrape_and_save(query, filename, max_results=100):
    tweets = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= max_results:
            break
        tweets.append(
            {
                "date": tweet.date.isoformat(),
                "username": tweet.user.username,
                "content": tweet.content,
                "url": tweet.url,
            }
        )

    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        for t in tweets:
            json.dump(t, f)
            f.write("\n")
    print(f"[✔] {len(tweets)} tweets enregistrés dans : {filepath}")


def main():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Mots-clés
    keyword_query = (
        '("APT" OR "CVE" OR "ransomware" OR "exploit" OR "malware") since:2025-07-01'
    )
    scrape_and_save(keyword_query, f"twitter_keywords_{now}.json")

    # Utilisateurs
    users = ["vxunderground", "CERT_FR", "CISACyber"]
    for user in users:
        user_query = f"from:{user} since:2025-07-01"
        scrape_and_save(user_query, f"twitter_{user}_{now}.json")


if __name__ == "__main__":
    main()
