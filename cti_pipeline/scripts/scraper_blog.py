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
    """Récupère tous les liens d'articles depuis la page d'accueil du blog."""
    try:
        r = requests.get(index_url)
        r.raise_for_status()
    except Exception as e:
        print(f"[❌] Échec accès {index_url} : {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#"):
            continue
        full_url = urljoin(index_url, href)
        if any(bad in full_url for bad in IGNORED_SUBSTRINGS):
            continue  # 🔥 lien à ignorer
        if domain_filter and domain_filter not in full_url:
            continue
        if not any(
            kw in full_url.lower() for kw in ["threat", "report", "malware", "blog"]
        ):
            continue
        links.append(full_url)

    return list(set(links))  # Suppression doublons


def extract_text_from_url(url, source_name="generic"):
    """Extrait le texte brut d’un article, avec filtrage Medium ou par mots-clés."""
    try:
        r = requests.get(url)
        r.raise_for_status()
    except Exception as e:
        print(f"[❌] Erreur récupération article {url} : {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # 📌 Filtrage par titre UNIQUEMENT pour Medium
    if "medium.com" in url or "medium" in source_name.lower():
        title_tag = soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else ""
        if "cti report" not in title_text.lower():
            print(f"[⏩] Ignoré (titre Medium non pertinent) : {title_text}")
            return None
    else:
        # 📌 Pour les autres : extraire texte et filtrer par mots-clés
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
            print(f"[⏩] Ignoré (aucun mot-clé CTI trouvé dans l'article) : {url}")
            return None

        return cleaned

    # 👇 Si c’est Medium et a passé le filtre de titre
    article = soup.find("article") or soup.find("main") or soup.find("body")
    text = (
        article.get_text(separator="\n") if article else soup.get_text(separator="\n")
    )
    cleaned = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    return cleaned


def scrape_blog(index_url, blog_name="generic"):
    """Scrape les articles d’un blog CTI et sauvegarde dans un fichier JSONL."""
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    out_file = os.path.join(DATA_DIR, f"{blog_name}_{now}.jsonl")
    links = extract_article_links(index_url)

    print(f"[🔎] {len(links)} liens détectés sur {index_url}")

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

    print(f"[✅] {count} articles enregistrés dans {out_file}")
