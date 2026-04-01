import re

def clean_number(value):
    """Nettoie et convertit les nombres"""
    if not value or str(value).strip() == "":
        return ""
    try:
        cleaned = str(value).strip().replace(" ", "").replace(",", ".")
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except:
        return value

def extract_identification_from_text(text):
    """Extrait les infos d'identification du texte"""
    data = {}
    
    patterns = {
        "Raison sociale": r"Raison sociale\s*:\s*(.+?)(?:\n|$)",
        "Identifiant fiscal": r"Identifiant fiscal\s*:\s*(\d+)",
        "Taxe professionnelle": r"Taxe professionnelle\s*:\s*(\d+)",
        "Adresse": r"Adresse\s*:\s*(.+?)(?:\n|$)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()
    
    # Extraction de l'exercice
    ex_match = re.search(r"Exercice du (\d{2}/\d{2}/\d{4}) au (\d{2}/\d{2}/\d{4})", text)
    if ex_match:
        data["Exercice"] = f"Du {ex_match.group(1)} au {ex_match.group(2)}"
    
    return data

def classify_row(row, doc_type):
    """Classifie une ligne selon son type (Actif/Passif/CPC)"""
    designation = row.get("DÉSIGNATION", "")
    
    # Mots-clés pour chaque catégorie
    actif_keywords = ["Immobilisations", "Stocks", "Créances", "Trésorerie", "BRUT", "ACTIF", "Terrains", "Constructions", "Matériel"]
    passif_keywords = ["CAPITAUX", "Dettes", "Fournisseurs", "PASSIF", "Emprunts", "Provisions", "Résultat"]
    
    if any(k in designation.upper() for k in [k.upper() for k in actif_keywords]):
        return "actif"
    elif any(k in designation.upper() for k in [k.upper() for k in passif_keywords]):
        return "passif"
    else:
        return "cpc"

import re

def clean_number(value):
    """Nettoie et convertit les nombres"""
    if not value or str(value).strip() == "":
        return ""
    try:
        cleaned = str(value).strip().replace(" ", "").replace(",", ".")
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except:
        return value

def extract_identification_from_text(text):
    """Extrait les infos d'identification du texte"""
    data = {}
    
    patterns = {
        "Raison sociale": r"Raison sociale\s*:\s*(.+?)(?:\n|$)",
        "Identifiant fiscal": r"Identifiant fiscal\s*:\s*(\d+)",
        "Taxe professionnelle": r"Taxe professionnelle\s*:\s*(\d+)",
        "Adresse": r"Adresse\s*:\s*(.+?)(?:\n|$)"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()
    
    # Extraction de l'exercice
    ex_match = re.search(r"Exercice du (\d{2}/\d{2}/\d{4}) au (\d{2}/\d{2}/\d{4})", text)
    if ex_match:
        data["Exercice"] = f"Du {ex_match.group(1)} au {ex_match.group(2)}"
    
    return data
