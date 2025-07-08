import requests
import os
import json
from datetime import datetime
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from cti_pipeline.scripts.utilities import (
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

# Configuration initiale
import logging
import sys


# Configuration du logger principale
def setup_logging(debug=False):
    """Configure le logging pour tout le module"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Handler pour la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # Handler pour le fichier
    file_handler = logging.FileHandler("cti_pipeline.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Ajout des handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


requests.packages.urllib3.disable_warnings(
    InsecureRequestWarning
)  # Désactive uniquement les warnings SSL

BASE_URL = "https://www.ancs.tn"
VULN_LIST_URL = BASE_URL + "/fr/tuncert/liste-vulnerabilites"
os.makedirs(DATA_DIR, exist_ok=True)

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
        # Fallback pour les certificats problématiques
        logger.warning(
            f"Problème de certificat SSL pour {url}, tentative sans vérification"
        )
        return session.get(url, timeout=30, verify=False)
    except Exception as e:
        logger.error(f"Échec de la requête: {str(e)}")
        return None


def fetch_vulnerability_list():
    try:
        response = safe_get_request(VULN_LIST_URL)
        if not response:
            logger.warning("Aucune réponse de %s", VULN_LIST_URL)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        vuln_links = []
        tables = soup.find_all("table", class_="views-table")

        logger.debug("Nombre de tables trouvées: %d", len(tables))

        for table in tables:
            tbody = table.find("tbody")
            if not tbody:
                logger.debug("tbody non trouvé dans la table")
                continue

            logger.debug("tbody trouvé dans la table")
            rows = tbody.find_all("tr")
            logger.debug("Nombre de lignes dans tbody: %d", len(rows))

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 2:
                    logger.debug("Ligne sans suffisamment de cellules: %s", row)
                    continue

                second_cell = cells[1]
                link = second_cell.find("a", href=True)
                if link:
                    href = link["href"]
                    if "/fr/tuncert/" in href:
                        full_url = urljoin(BASE_URL, href)
                        vuln_links.append(full_url)
                        logger.debug("Ajout du lien: %s", full_url)

        logger.info("Nombre total de liens trouvés: %d", len(vuln_links))
        return list(set(vuln_links))

    except Exception as e:
        logger.exception("Erreur lors de l'extraction de la liste des vulnérabilités")
        return []


def extract_vulnerability_details(url):
    """Version optimisée pour la structure ANCS"""
    try:
        response = session.get(url, timeout=30, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")

        # Récupération du contenu principal
        content = soup.find("div", class_="node-content")
        if not content:
            logger.error("Div node-content non trouvée")
            return None

        # Extraction des sections spécifiques
        sections = content.find_all("section", class_="field")

        # Structure de données finale
        details = {
            "source_url": url,
            "title": (
                soup.find("h1", class_="title").get_text().strip()
                if soup.find("h1", class_="title")
                else "Sans titre"
            ),
            "date_published": extract_date(soup),
            "technical_details": {
                "impact": (
                    extract_section_text(sections[0]) if len(sections) > 0 else None
                ),
                "plateforme": (
                    extract_section_text(sections[1]) if len(sections) > 1 else None
                ),
                "consequences": (
                    extract_section_text(sections[2]) if len(sections) > 2 else None
                ),
                "description": (
                    extract_section_text(sections[3]) if len(sections) > 3 else None
                ),
            },
            "solution": extract_section_by_label(content, "Solution"),
            "references": extract_references(content),
        }

        # Extraction spécifique du CVE si disponible
        cve_section = content.find(
            "section", class_="field-name-field-vulnerabilite-ref"
        )
        if cve_section:
            details["cve"] = (
                cve_section.find("div", class_="field-item").get_text().strip()
            )

        return details

    except Exception as e:
        logger.error(f"Erreur d'extraction: {str(e)}", exc_info=True)
        return None


def extract_section_text(section):
    """Extrait le texte d'une section spécifique"""
    if not section:
        return None
    item = section.find("div", class_="field-item")
    return item.get_text().strip() if item else None


def extract_section_by_label(content, label):
    """Trouve une section par son label"""
    for section in content.find_all("section", class_="field"):
        if (
            section.find("div", class_="field-label")
            and label in section.find("div", class_="field-label").get_text()
        ):
            return extract_section_text(section)
    return None


def extract_date(soup):
    """Extrait la date de publication"""
    date_div = soup.find("div", class_="field-name-post-date")
    if date_div:
        return date_div.find("div", class_="field-item").get_text().strip()
    return datetime.now().strftime("%Y-%m-%d")


def extract_publish_date(soup):
    """Extrait la date de publication"""
    # Adaptez ceci selon le format réel du site
    date_tag = soup.find("span", class_="date")
    return datetime.now().isoformat() if not date_tag else date_tag.get_text().strip()


def extract_main_content(soup):
    """Extrait le contenu principal"""
    content = soup.find("div", class_="content-body") or soup.find("article")
    return content.get_text("\n").strip() if content else ""


def extract_technical_data(soup):
    """Extrait les données techniques structurées"""
    tech_data = {}
    # Exemple d'extraction - adapter au format réel
    for row in soup.select("table.technical-data tr"):
        cells = row.find_all("td")
        if len(cells) == 2:
            tech_data[cells[0].get_text().strip()] = cells[1].get_text().strip()
    return tech_data


def extract_references(soup):
    """Extrait les références externes"""
    return [
        a["href"]
        for a in soup.find_all("a", href=True)
        if a["href"].startswith("http") and "ancs.tn" not in a["href"]
    ]


def ingest_tuncert_vulnerabilities():
    """Fonction principale"""
    processed_data = load_processed_items("tuncert")
    output_file = os.path.join(
        DATA_DIR, f"tuncert_vulns_{datetime.now().strftime('%Y%m%d')}.jsonl"
    )

    try:
        vuln_urls = fetch_vulnerability_list()
        if not vuln_urls:
            logger.warning("Aucune vulnérabilité trouvée")
            return 0

        new_count = 0
        with open(output_file, "a", encoding="utf-8") as f:
            for url in vuln_urls:
                if url in processed_data.get("processed_urls", []):
                    continue

                vuln_details = extract_vulnerability_details(url)
                if vuln_details:
                    json.dump(vuln_details, f, ensure_ascii=False)
                    f.write("\n")
                    processed_data.setdefault("processed_urls", []).append(url)
                    new_count += 1

        save_processed_items("tuncert", processed_data)
        return new_count

    except Exception as e:
        logger.error(f"Erreur majeure: {str(e)}")
        return 0


if __name__ == "__main__":
    debug_mode = "--debug" in sys.argv
    logger = setup_logging(debug=debug_mode)
    count = ingest_tuncert_vulnerabilities()
    logger.info(f"Traitement terminé. {count} nouvelles vulnérabilités ingérées.")
else:
    logger = setup_logging()
