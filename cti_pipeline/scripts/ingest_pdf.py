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


# ### Collect PDFs from a web page
# def collect_pdfs(page_url, pdf_dir="cti_pipeline/PDFs"):
#     os.makedirs(pdf_dir, exist_ok=True)
#     domain = "/".join(page_url.split("/")[:3])  # Ex: https://www.mandiant.com
#
#     try:
#         r = requests.get(page_url)
#         r.raise_for_status()
#     except Exception as e:
#         print(f"[❌] Failed to access page {page_url}: {e}")
#         return
#
#     soup = BeautifulSoup(r.text, "html.parser")
#     for link in soup.find_all("a", href=True):
#         href = link["href"]
#         if ".pdf" in href.lower():
#             pdf_url = urljoin(domain, href)
#             filename = os.path.basename(pdf_url)
#             dest_path = os.path.join(pdf_dir, filename)
#
#             if os.path.exists(dest_path):
#                 print(f"[✔] Already downloaded: {filename}")
#                 continue
#
#             try:
#                 resp = requests.get(pdf_url)
#                 resp.raise_for_status()
#                 with open(dest_path, "wb") as f:
#                     f.write(resp.content)
#                 print(f"[⬇️] Downloaded: {filename}")
#             except Exception as e:
#                 print(f"[❌] Failed to download {pdf_url}: {e}")


### Ingestion of PDF files
def ingest_pdf(file_path, output_file="raw_pdf.jsonl"):
    print(f"[📄] Processing: {file_path}")
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
        print(f"[+] PDF ingested: {file_path}")
    except Exception as e:
        print(f"[❌] Failed to write JSON for {file_path}: {e}")


### PDF Ingestion
def run_pdf_ingestion():
    # # 1. Collect all PDFs from known sources
    # for source in PDF_SOURCES:
    #     print(f"[🌐] Collecting PDFs from {source['name']}...")
    #     collect_pdfs(source["url"])

    # 2. Ingestion of downloaded PDFs
    PDF_DIR = "cti_pipeline/PDFs"
    for filename in os.listdir(PDF_DIR):
        if filename.endswith(".pdf"):
            filepath = os.path.join(PDF_DIR, filename)
            ingest_pdf(filepath, output_file="raw_pdf.jsonl")


if __name__ == "__main__":
    run_pdf_ingestion()
