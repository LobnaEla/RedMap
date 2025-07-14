import os
import re
import json
import csv
import requests
import base64
import time
from pypdf import PdfReader
from bs4 import BeautifulSoup
from dotenv import load_dotenv
# from cti_pipeline.scripts.preprocessing.ocr_client import extract_text as extract_text_ocr
# from pdf2image import convert_from_path


# --- Récupérer la clé API depuis variable d'environnement ---
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="C:/Users/USER/Desktop/Stage ete WEVIOO/cti_pipeline/config/.env.example")
API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
print(API_KEY)

if not API_KEY:
    print("Erreur : la variable d'environnement VIRUSTOTAL_API_KEY n'est pas définie.")
    exit(1)


# --- Extraction du texte ---
def extraire_texte(fichier):
    _, extension = os.path.splitext(fichier)
    try:
        if extension.lower() == ".pdf":
            return nettoyer_texte(extraire_pdf(fichier))
        elif extension.lower() == ".txt":
            return nettoyer_texte(extraire_txt(fichier))
        elif extension.lower() == ".json":
            return nettoyer_texte(extraire_json(fichier))
        elif extension.lower() == ".html":
            return nettoyer_texte(extraire_html(fichier))
        elif extension.lower() == ".csv":
            return nettoyer_texte(extraire_csv(fichier))
        else:
            print(f"[SKIP] Format non supporté : {extension}")
            return ""
    except Exception as e:
        print(f"[ERREUR] Échec de l'extraction : {e}")
        return ""


def extraire_pdf(fichier):
    try:
        with open(fichier, "rb") as f:
            reader = PdfReader(f)
            # OCR-related code commented out for debugging/migration
            # images = convert_from_path(fichier, dpi=300)

            texte_total = ""

            for i, page in enumerate(reader.pages):
                texte_brut = page.extract_text() or ""

                # OCR processing commented out - using only direct PDF text extraction
                # temp_path = f"temp_page_{i+1}.png"
                # images[i].save(temp_path)
                # texte_ocr = extract_text_ocr(temp_path)
                # os.remove(temp_path)

                print(f"[PAGE {i+1}] Texte brut longueur : {len(texte_brut)}")
                # print(f"[PAGE {i+1}] Texte OCR longueur : {len(texte_ocr)}")

                # OCR text merging commented out - using only direct PDF text
                # if texte_brut.strip() and texte_ocr.strip():
                #     # Exemple simple : concaténation avec séparation
                #     texte_total += texte_brut + "\n--- OCR ---\n" + texte_ocr + "\n"
                # elif texte_brut.strip():
                #     texte_total += texte_brut + "\n"
                # else:
                #     texte_total += texte_ocr + "\n"
                
                # Using only direct PDF text extraction (no OCR)
                if texte_brut.strip():
                    texte_total += texte_brut + "\n"

            return texte_total

    except Exception as e:
        print(f"[ERREUR PDF] {e}")
        return ""


def extraire_txt(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        return f.read()


def extraire_json(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        contenu = json.load(f)
        return json.dumps(contenu, ensure_ascii=False)


def extraire_html(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
        return soup.get_text(separator="\n")


def extraire_csv(fichier):
    with open(fichier, newline="", encoding="utf-8") as f:
        lecteur = csv.reader(f)
        return "\n".join("; ".join(ligne) for ligne in lecteur)


def nettoyer_texte(texte):
    if not texte:
        return ""
    lignes = [ligne.strip() for ligne in texte.splitlines() if ligne.strip()]
    return "\n".join(lignes)


# --- Trouver liens ---
def trouver_liens(texte):
    regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    return re.findall(regex, texte)


# --- Vérifier lien avec VirusTotal API v3 ---
def verifier_lien_virustotal(lien):
    print(f"\n🔎 Analyse du lien : {lien}")
    url_bytes = lien.encode("utf-8")
    url_b64 = base64.urlsafe_b64encode(url_bytes).decode().strip("=")

    headers = {"x-apikey": API_KEY}

    response = requests.get(
        f"https://www.virustotal.com/api/v3/urls/{url_b64}", headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        stats = data["data"]["attributes"]["last_analysis_stats"]
        if stats["malicious"] > 0 or stats["suspicious"] > 0:
            print(f"⚠️ Lien potentiellement malveillant : {lien}")
            print(f"Malicious: {stats['malicious']}, Suspicious: {stats['suspicious']}")
        else:
            print(f"✅ Lien sûr : {lien}")
    elif response.status_code == 404:
        print(f"[INFO] Lien non trouvé dans VirusTotal : {lien}")
    else:
        print(f"[ERREUR] Code {response.status_code} pour le lien : {lien}")


# --- Programme principal ---
if __name__ == "__main__":
    fichier = "C:/Users/USER/Downloads/mixIMTEX (1).pdf"  # Change ce chemin

    print(f"📂 Analyse du fichier : {fichier}\n")
    texte_extrait = extraire_texte(fichier)

    if texte_extrait:
        print("📄 Contenu extrait:")
        print("-" * 60)
        print(texte_extrait)

        liens = trouver_liens(texte_extrait)

        if not liens:
            print("\n✅ Aucun lien détecté dans le fichier.")
        else:
            print(f"\n🔗 {len(liens)} lien(s) trouvé(s). Analyse en cours...\n")
            for lien in liens:
                verifier_lien_virustotal(lien)
    else:
        print("❌ Aucun texte extrait ou fichier vide.")
