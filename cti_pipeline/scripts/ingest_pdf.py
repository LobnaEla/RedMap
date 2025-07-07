import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from cti_pipeline.scripts.ExtractionTexte import extraire_texte

DATA_DIR = "cti_pipeline/data/"
PDF_DIR = "cti_pipeline/PDFs"


# ### Collecte des PDF depuis une page web
# def collect_pdfs(page_url, pdf_dir="cti_pipeline/PDFs"):
#     os.makedirs(pdf_dir, exist_ok=True)
#     domain = "/".join(page_url.split("/")[:3])  # Ex: https://www.mandiant.com

#     try:
#         r = requests.get(page_url)
#         r.raise_for_status()
#     except Exception as e:
#         print(f"[❌] Erreur d'accès à la page {page_url}: {e}")
#         return

#     soup = BeautifulSoup(r.text, "html.parser")
#     for link in soup.find_all("a", href=True):
#         href = link["href"]
#         if ".pdf" in href.lower():
#             pdf_url = urljoin(domain, href)
#             filename = os.path.basename(pdf_url)
#             dest_path = os.path.join(pdf_dir, filename)

#             if os.path.exists(dest_path):
#                 print(f"[✔] Déjà téléchargé : {filename}")
#                 continue

#             try:
#                 resp = requests.get(pdf_url)
#                 resp.raise_for_status()
#                 with open(dest_path, "wb") as f:
#                     f.write(resp.content)
#                 print(f"[⬇️] Téléchargé : {filename}")
#             except Exception as e:
#                 print(f"[❌] Échec pour {pdf_url} : {e}")


### Ingestion des fichiers PDF
def ingest_pdf(file_path, output_file="raw_pdf.jsonl"):
    print(f"[📄] Traitement de : {file_path}")
    full_text = extraire_texte(file_path) or ""

    doc = {
        "source": os.path.basename(file_path),
        "type": "report",
        "content": full_text.strip(),
        "date": str(datetime.now()),
        "format": "PDF",
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, output_file)

    try:
        with open(path, "a", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
            f.write("\n")
        print(f"[+] PDF ingéré : {file_path}")
    except Exception as e:
        print(f"[❌] Échec d’écriture JSON pour {file_path} : {e}")


### PDF Ingestion
def run_pdf_ingestion():
    # # 1. Collecter tous les PDFs depuis les sources connues
    # for source in PDF_SOURCES:
    #     print(f"[🌐] Collecte des PDFs depuis {source['name']}...")
    #     collect_pdfs(source["url"])

    # 2. Ingestion des PDFs téléchargés
    PDF_DIR = "cti_pipeline/PDFs"
    for filename in os.listdir(PDF_DIR):
        if filename.endswith(".pdf"):
            filepath = os.path.join(PDF_DIR, filename)
            ingest_pdf(filepath, output_file="raw_pdf.jsonl")


if __name__ == "__main__":
    run_pdf_ingestion()
