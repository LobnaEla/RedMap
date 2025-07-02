import os
import json
from pypdf import PdfReader  

def extraire_texte(fichier):
    _, extension = os.path.splitext(fichier)
    try:
        if extension.lower() == ".pdf":
            return extraire_pdf(fichier)
        elif extension.lower() == ".txt":
            return extraire_txt(fichier)
        elif extension.lower() == ".json":
            return extraire_json(fichier)
        else:
            raise ValueError(f"Format de fichier non supporté : {extension}")
    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")
        return None

def extraire_pdf(fichier):
    with open(fichier, "rb") as f:
        reader = PdfReader(f)
        texte_complet = ""
        for i, page in enumerate(reader.pages):
            texte_page = page.extract_text()
            if texte_page:
                texte_complet += texte_page + "\n"
            else:
                print(f"Page {i+1} : aucun texte détecté (image ou format non lisible).")
        return texte_complet

def extraire_txt(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        return f.read()

def extraire_json(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        contenu = json.load(f)
        return json.dumps(contenu, ensure_ascii=False, indent=2)

# Exemple d'utilisation
if __name__ == "__main__":
    chemin_fichier = "C:/Users/USER/Desktop/essai json.json"
    texte = extraire_texte(chemin_fichier)
    if texte:
        print("Contenu extrait (premiers 500 caractères) :")
        print(texte)