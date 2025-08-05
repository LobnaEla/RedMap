import requests
import os
import json
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from ..utilities import (
    get_content_hash,
    load_processed_items,
    save_processed_items,
    is_duplicate,
    DATA_DIR,
    METADATA_DIR,
)

import requests
import ssl
from urllib3.util.ssl_ import create_urllib3_context

# Configuration SSL corrigée
ctx = create_urllib3_context()
ctx.load_default_certs()

# Création de la session - Version corrigée
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=3)
session.mount("https://", adapter)

# Appliquez le contexte SSL à la session
session.verify = True  # Ou le chemin vers votre certificat .pem

import sys


requests.packages.urllib3.disable_warnings(
    InsecureRequestWarning
)  # Désactive uniquement les warnings SSL

BASE_URL = "https://www.ancs.tn"
VULN_LIST_URL = BASE_URL + "/fr/tuncert/liste-vulnerabilites"

# Nouvelle configuration de session sécurisée
session = requests.Session()
session.verify = False  # À remplacer par le chemin du certificat en production
session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
)


def safe_get_request(url):
    """Effectue une requête HTTPS sécurisée avec fallback"""
    try:
        # Essai avec vérification SSL normale
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response
    except requests.exceptions.SSLError:
        return session.get(url, timeout=30, verify=False)
    except Exception as e:
        return None


def fetch_vulnerability_list():
    try:
        response = safe_get_request(VULN_LIST_URL)
        if not response:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        vuln_links = []
        tables = soup.find_all("table", class_="views-table")

        for table in tables:
            tbody = table.find("tbody")
            if not tbody:
                continue

            rows = tbody.find_all("tr")

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                second_cell = cells[1]
                link = second_cell.find("a", href=True)
                if link:
                    href = link["href"]
                    if "/fr/tuncert/" in href:
                        full_url = urljoin(BASE_URL, href)
                        vuln_links.append(full_url)

        return list(set(vuln_links))

    except Exception as e:
        return []


def extract_vulnerability_details(url):
    """Extraction complète d'une page TunCERT structurée"""
    try:
        response = session.get(url, timeout=30, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")

        content = soup.find("div", class_="node-content")
        if not content:
            return None

        details = {
            "source": "TUNCERT",
            "source_url": url,
            "title": (
                soup.find("h1", class_="title").get_text(strip=True)
                if soup.find("h1", class_="title")
                else "Sans titre"
            ),
            "technical_details": {
                "impact": extract_section_by_label(content, "Impact"),
                "platform": extract_section_by_label(content, "Plateforme"),
                "consequences": extract_section_by_label(content, "Conséquence"),
                "Affected Software": extract_section_by_label(
                    content, "Logiciels impactés"
                ),
                "description": extract_section_by_label(content, "Description"),
                "problem_identifiers": extract_section_by_label(
                    content, "Identificants du problème"
                ),
                "solution": extract_section_by_label(content, "Solution"),
            },
            "additional_documentation": extract_section_by_label(
                content, "Documentation additionnelle"
            ),
            "publish_date": extract_section_by_label(content, "Date de publication"),
            "reference": extract_section_by_label(content, "Référence"),
        }

        return details

    except Exception as e:
        return None


def extract_section_text(section):
    if not section:
        return None

    container = section.find(class_="field-items")
    if not container:
        container = section.find(class_="field-item")
        if not container:
            return None

    texts = []

    div_items = container.find_all("div", class_="field-item")
    for item in div_items:
        ps = item.find_all("p")
        if ps:
            for p in ps:
                text = p.get_text(strip=True)
                if text:
                    texts.append(text)
            continue
        links = item.find_all("a", href=True)
        if links:
            for a in links:
                text = a.get_text(strip=True)
                href = a["href"]
                texts.append(f"{text} ({href})")
            continue
        spans = item.find_all("span")
        if spans:
            for span in spans:
                text = span.get_text(strip=True)
                if text:
                    texts.append(text)
            continue
        raw = item.get_text(strip=True)
        if raw:
            texts.append(raw)

    li_items = container.find_all("li", class_="field-item")
    if li_items:
        for li in li_items:
            text = li.get_text(strip=True)
            if text:
                texts.append(text)

    if not texts:
        pass

    return "\n".join(texts).strip() if texts else None


def extract_section_by_label(content, label):
    for section in content.find_all("section", class_="field"):
        if (
            section.find("h2", class_="field-label")
            and label in section.find("h2", class_="field-label").get_text()
        ):
            return extract_section_text(section)
    return None


def ingest_tuncert_vulnerabilities(data_dir, metadata_dir):
    processed_data = load_processed_items("tuncert")

    # Create structured directory for TUNCERT data
    tuncert_dir = os.path.join(data_dir, "raw_scraped_data", "tuncert")
    os.makedirs(tuncert_dir, exist_ok=True)

    try:
        vuln_urls = fetch_vulnerability_list()
        if not vuln_urls:
            return 0

        # First pass: collect valid documents
        valid_docs = []
        for url in vuln_urls:
            vuln_details = extract_vulnerability_details(url)
            if not vuln_details:
                continue

            content_str = json.dumps(vuln_details, sort_keys=True)

            if is_duplicate(
                content_str, url, processed_data, content_type="generic"
            ):
                continue

            content_hash = get_content_hash(content_str)
            vuln_details["hash"] = content_hash
            
            valid_docs.append(vuln_details)
            processed_data.setdefault("hashes", []).append(content_hash)
            processed_data.setdefault("urls", []).append(url)

        # Only create file if we have valid documents to save
        if valid_docs:
            output_file = os.path.join(
                tuncert_dir, f"tuncert_vulns_{datetime.now().strftime('%Y%m%d')}.jsonl"
            )
            
            with open(output_file, "w", encoding="utf-8") as f:
                for doc in valid_docs:
                    json.dump(doc, f, ensure_ascii=False)
                    f.write("\n")
            
            print(f"[TUNCERT] Saved {len(valid_docs)} new vulnerabilities")
            save_processed_items("tuncert", processed_data)
            return len(valid_docs)
        else:
            print("[TUNCERT] No new vulnerabilities to save - all were duplicates or invalid")
            return 0

    except Exception as e:
        print(f"[ERROR] TunCERT ingestion failed: {str(e)}")
        return 0


if __name__ == "__main__":
    debug_mode = "--debug" in sys.argv
    try:
        count = ingest_tuncert_vulnerabilities(DATA_DIR, METADATA_DIR)
        print(f"[OK] Processed {count} TUNCERT vulnerabilities.")
    except Exception as e:
        print(f"[ERROR] An error occurred during TUNCERT ingestion: {str(e)}")
