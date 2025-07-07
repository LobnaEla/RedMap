import os
import json
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables from config/.env
load_dotenv(dotenv_path="cti_pipeline/config/.env")

OTX_API_KEY = os.getenv("OTX_API_KEY")

if not OTX_API_KEY:
    raise Exception("❌ OTX API Key not found. Make sure it's set in config/.env")

DATA_DIR = "cti_pipeline/data/"
OTX_API_URL = "https://otx.alienvault.com/api/v1/pulses/subscribed"


### Ingestion of OTX pulses (Open Threat Exchange)
def ingest_otx(output_file="raw_otx_pulses.jsonl"):
    headers = {"X-OTX-API-KEY": OTX_API_KEY}
    try:
        response = requests.get(OTX_API_URL, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"[-] API Error: {e}")
        return

    data = response.json()
    pulses = data.get("results", [])

    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, output_file)

    with open(file_path, "a", encoding="utf-8") as f:
        for pulse in pulses:
            doc = {
                "source": "OTX",
                "type": "cti_pulse",
                "title": pulse.get("name"),
                "description": pulse.get("description", ""),
                "tags": pulse.get("tags", []),
                "created": pulse.get("created"),
                "modified": pulse.get("modified"),
                "indicators": pulse.get("indicators", []),
                "tlp": pulse.get("tlp", "TLP:WHITE"),
                "date_collected": str(datetime.now()),
            }

            try:
                json.dump(doc, f, ensure_ascii=False)
                f.write("\n")
            except Exception as e:
                print(f"[❌] JSON write failed: {e}")
                print("[PROBLEMATIC DOC] :", doc)

    print(f"[+] {len(pulses)} CTI pulses collected into {output_file}.")


if __name__ == "__main__":
    ingest_otx()
    print("[✔] OTX pulse ingestion completed.")
