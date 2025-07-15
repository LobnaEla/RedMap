import os
import json
from datetime import datetime
import requests
from typing import Dict, List, Optional

from cti_pipeline.scripts.utilities import (
    get_content_hash,
    load_processed_items,
    save_processed_items,
    is_duplicate,
    DATA_DIR,
    METADATA_DIR,
)


# Load environment variables
OTX_API_KEY = os.getenv("OTX_API_KEY")
OTX_API_URL = "https://otx.alienvault.com/api/v1/pulses/subscribed"


def fetch_otx_pulses() -> Optional[List[Dict]]:
    """Fetches pulses from OTX API"""
    if not OTX_API_KEY:
        raise ValueError("OTX_API_KEY not found in environment variables")

    try:
        response = requests.get(
            OTX_API_URL, headers={"X-OTX-API-KEY": OTX_API_KEY}, timeout=30
        )
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        print(f"[ERROR] Failed to fetch OTX pulses: {str(e)}")
        return None


def process_otx_pulse(pulse: Dict, processed_data: Dict) -> Optional[Dict]:
    """Processes a single OTX pulse, skipping duplicates"""
    content_str = json.dumps(pulse, sort_keys=True)
    pulse_id = pulse.get("id")

    if is_duplicate(content_str, pulse_id, processed_data, content_type="generic"):
        print(f"[DUPLICATE] Pulse {pulse_id} already processed, skipping.")
        return None

    content_hash = get_content_hash(content_str)

    return {
        "source": "OTX",
        "type": "cti_pulse",
        "hash": content_hash,
        "pulse_id": pulse_id,
        "title": pulse.get("name"),
        "description": pulse.get("description", ""),
        "tags": pulse.get("tags", []),
        "created": pulse.get("created"),
        "modified": pulse.get("modified"),
        "indicators": pulse.get("indicators", []),
        "tlp": pulse.get("tlp", "TLP:WHITE"),
        "date_collected": datetime.now().isoformat(),
    }


def ingest_otx_pulses(data_dir: str, metadata_dir: str) -> Dict[str, int]:
    """Main OTX ingestion function with duplicate detection"""
    stats = {"processed": 0, "total": 0}
    processed_data = load_processed_items("otx")
    pulses = fetch_otx_pulses()

    if not pulses:
        return stats

    stats["total"] = len(pulses)
    output_file = os.path.join(
        data_dir, f"raw_otx_pulses_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        for pulse in pulses:
            doc = process_otx_pulse(pulse, processed_data)
            if not doc:
                continue

            json.dump(doc, f, ensure_ascii=False)
            f.write("\n")

            processed_data.setdefault("hashes", []).append(doc["hash"])
            processed_data.setdefault("urls", []).append(doc["pulse_id"])
            stats["processed"] += 1

    save_processed_items("otx", processed_data)
    return stats


if __name__ == "__main__":
    results = ingest_otx_pulses(DATA_DIR, METADATA_DIR)
    print(f"Results: {results}")
    print("[✔] OTX pulse ingestion completed.")
