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
    """Extraction complète d'une page TunCERT structurée"""
    try:
        response = session.get(url, timeout=30, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")

        content = soup.find("div", class_="node-content")
        if not content:
            logger.error("Div node-content non trouvée")
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
        logger.error(f"Erreur d'extraction depuis {url}: {str(e)}", exc_info=True)
        return None


def extract_section_text(section):
    if not section:
        logger.debug("Section vide ou None reçue.")
        return None

    container = section.find(class_="field-items")
    if not container:
        container = section.find(class_="field-item")
        if not container:
            logger.debug("Pas de div.field-item trouvée dans la section.")
            return None

    texts = []

    div_items = container.find_all("div", class_="field-item")
    for item in div_items:
        logger.debug("Traitement d'un div.field-item")
        ps = item.find_all("p")
        if ps:
            logger.debug(f"  ➤ {len(ps)} paragraphe(s) trouvé(s) dans le div.")
            for p in ps:
                text = p.get_text(strip=True)
                if text:
                    texts.append(text)
            continue
        links = item.find_all("a", href=True)
        if links:
            logger.debug(f"  ➤ {len(links)} lien(s) <a> trouvé(s).")
            for a in links:
                text = a.get_text(strip=True)
                href = a["href"]
                texts.append(f"{text} ({href})")
            continue
        spans = item.find_all("span")
        if spans:
            logger.debug(f"  ➤ {len(spans)} span(s) trouvé(s) dans le div.")
            for span in spans:
                text = span.get_text(strip=True)
                if text:
                    texts.append(text)
            continue
        raw = item.get_text(strip=True)
        if raw:
            logger.debug("  ➤ Texte brut extrait du div.field-item")
            texts.append(raw)

    li_items = container.find_all("li", class_="field-item")
    if li_items:
        logger.debug(f"{len(li_items)} élément(s) <li.field-item> trouvé(s).")
        for li in li_items:
            text = li.get_text(strip=True)
            if text:
                texts.append(text)

    if not texts:
        logger.debug("Aucun contenu textuel extrait de la section.")

    return "\n".join(texts).strip() if texts else None


def extract_section_by_label(content, label):
    for section in content.find_all("section", class_="field"):
        if (
            section.find("h2", class_="field-label")
            and label in section.find("h2", class_="field-label").get_text()
        ):
            logger.debug(f"Section {label} trouvée")
            return extract_section_text(section)
    logger.debug(f"❌ Section {label} non trouvée")
    return None


def ingest_tuncert_vulnerabilities(data_dir, metadata_dir):
    processed_data = load_processed_items("tuncert")
    output_file = os.path.join(
        data_dir, f"tuncert_vulns_{datetime.now().strftime('%Y%m%d')}.jsonl"
    )

    try:
        vuln_urls = fetch_vulnerability_list()
        if not vuln_urls:
            logger.warning("Aucune vulnérabilité trouvée")
            return 0

        new_count = 0
        with open(output_file, "a", encoding="utf-8") as f:
            for url in vuln_urls:
                vuln_details = extract_vulnerability_details(url)
                if not vuln_details:
                    continue

                content_str = json.dumps(vuln_details, sort_keys=True)

                if is_duplicate(
                    content_str, url, processed_data, content_type="generic"
                ):
                    logger.debug(f"Doublon détecté pour : {url}")
                    continue

                content_hash = get_content_hash(content_str)

                vuln_details["hash"] = content_hash
                json.dump(vuln_details, f, ensure_ascii=False)
                f.write("\n")

                processed_data.setdefault("hashes", []).append(content_hash)
                processed_data.setdefault("urls", []).append(url)
                new_count += 1

        save_processed_items("tuncert", processed_data)
        return new_count
    except Exception as e:
        logger.error(f"Erreur majeure: {str(e)}")
        return 0


if __name__ == "__main__":
    debug_mode = "--debug" in sys.argv
    logger = setup_logging(debug=debug_mode)
    count = ingest_tuncert_vulnerabilities(DATA_DIR, METADATA_DIR)
    logger.info(f"Traitement terminé. {count} nouvelles vulnérabilités ingérées.")
else:
    logger = setup_logging()
