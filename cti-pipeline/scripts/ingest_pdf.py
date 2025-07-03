import os
import json
from datetime import datetime
from PyPDF2 import PdfReader

DATA_DIR = "cti-pipeline/data/"


### Ingestion des fichiers PDF
def ingest_pdf(file_path, output_file="raw_pdf.json"):
    reader = PdfReader(file_path)
    full_text = ""
    ############### extraction du texte du PDF

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
