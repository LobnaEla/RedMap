import os
import json
from pypdf import PdfReader
from bs4 import BeautifulSoup

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
                print(f"Page {i+1} : aucun texte détecté.")
        return texte_complet

def extraire_txt(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        return f.read()

def extraire_json(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        contenu = json.load(f)
        return json.dumps(contenu, ensure_ascii=False, indent=2)

def extraire_html(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
        return soup.get_text(separator="\n")

def nettoyer_texte(texte):
    if not texte:
        return texte
    # Découper le texte en lignes
    lignes = texte.splitlines()
    # Filtrer les lignes vides ou composées uniquement d'espaces
    lignes_non_vides = [ligne.strip() for ligne in lignes]
    lignes_nettoyees = [ligne for ligne in lignes_non_vides if ligne]
    # Recoller les lignes avec un seul saut de ligne
    return "\n".join(lignes_nettoyees)


# Exemple d'utilisation
if __name__ == "__main__":
    chemin_fichier = ""
    texte = extraire_texte(chemin_fichier)
    if texte:
        print("Contenu nettoyé :")
        print(texte)