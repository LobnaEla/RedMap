import os
import requests
import json
import pandas as pd

os.environ["TOKENIZERS_PARALLELISM"] = "false"
URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json"
OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "enterprise-attack150.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("🔄 Téléchargement et traitement du dataset MITRE ATT&CK Enterprise...")

try:
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    print("✅ Données téléchargées")

    data = response.json()
    techniques = [obj for obj in data["objects"] if obj["type"] == "attack-pattern"]
    print(f"📁 {len(techniques)} techniques trouvées")

    rows = []
    for tech in techniques:
        tech_id = next((ref["external_id"] for ref in tech.get("external_references", []) 
                        if ref.get("source_name") == "mitre-attack"), None)
        description = tech.get("description", "").strip()
        if tech_id and description:
            rows.append({"id": tech_id, "description": description})
        if len(rows) >= 900:
            break  # Stop après 200 techniques valides

    df = pd.DataFrame(rows)
    print(f"✅ {len(df)} techniques valides extraites")

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"💾 Dataset sauvegardé : '{OUTPUT_FILE}'")
    print(f"🔍 Exemple : {df.iloc[0]['id']} → {df.iloc[0]['description'][:100]}...")

except requests.exceptions.RequestException as e:
    print(f"❌ Erreur réseau / URL invalide : {e}")
except json.JSONDecodeError as e:
    print(f"❌ Erreur parsing JSON : {e}")
except Exception as e:
    print(f"❌ Erreur inattendue : {e}")

print("✨ Préparation du dataset terminée !")
