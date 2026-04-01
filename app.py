import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Convertisseur PDF Fiscal", layout="wide")

st.title("📄 Convertisseur PDF Fiscal Marocain")

# Sidebar
with st.sidebar:
    doc_type = st.radio("Type de document", ["AMMC", "DGI"])
    st.info("Convertit les PDF fiscaux en Excel structuré")

# Fonctions d'extraction
def clean_number(value):
    """Nettoie les nombres"""
    if not value or str(value).strip() == "":
        return ""
    try:
        cleaned = str(value).strip().replace(" ", "").replace(",", ".")
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except:
        return value

def extract_identification(pdf):
    """Extrait les infos de la première page"""
    first_page = pdf.pages[0]
    text = first_page.extract_text()
    
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
    
    # Exercice
    ex_match = re.search(r"Exercice du (\d{2}/\d{2}/\d{4}) au (\d{2}/\d{2}/\d{4})", text)
    if ex_match:
        data["Exercice"] = f"Du {ex_match.group(1)} au {ex_match.group(2)}"
    
    return data

def extract_table_ammc(page):
    """Extrait les tableaux AMMC"""
    table = page.extract_table({
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 5,
    })
    
    if not table:
        return []
    
    data = []
    for row in table:
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue
        
        clean = [str(c).strip() if c else "" for c in row]
        
        # Bilan Actif (5 colonnes)
        if len(clean) >= 5 and any(x in clean[0] for x in ["Immobilisations", "Stocks", "Créances", "Trésorerie"]):
            data.append({
                "DÉSIGNATION": clean[0],
                "BRUT": clean_number(clean[1]) if len(clean) > 1 else "",
                "AMORT. & PROV.": clean_number(clean[2]) if len(clean) > 2 else "",
                "NET N": clean_number(clean[3]) if len(clean) > 3 else "",
                "NET N-1": clean_number(clean[4]) if len(clean) > 4 else ""
            })
        
        # Bilan Passif (3 colonnes)
        elif len(clean) >= 3 and any(x in clean[0] for x in ["CAPITAUX", "Dettes", "Provisions"]):
            data.append({
                "DÉSIGNATION": clean[0],
                "EXERCICE N": clean_number(clean[1]),
                "EXERCICE N-1": clean_number(clean[2])
            })
        
        # CPC
        elif len(clean) >= 5 and any(x in clean[0] for x in ["PRODUITS", "CHARGES", "RESULTAT"]):
            data.append({
                "DÉSIGNATION": clean[0],
                "PROPRES EXERCICE": clean_number(clean[1]),
                "EXERCICES PRECEDENTS": clean_number(clean[2]),
                "TOTAL N": clean_number(clean[3]),
                "TOTAL N-1": clean_number(clean[4])
            })
    
    return data

def extract_table_dgi(page):
    """Extrait les tableaux DGI"""
    table = page.extract_table({
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 5,
    })
    
    if not table:
        return []
    
    data = []
    for row in table:
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue
        
        clean = [str(c).strip() if c else "" for c in row]
        
        # Bilan Actif DGI
        if len(clean) >= 5 and "Brut exercice" in str(row):
            data.append({
                "DÉSIGNATION": clean[0],
                "BRUT EXERCICE": clean_number(clean[1]),
                "AMORT. & PROV.": clean_number(clean[2]),
                "NET EXERCICE": clean_number(clean[3]),
                "NET PRECEDENT": clean_number(clean[4])
            })
        
        # Bilan Passif DGI
        elif len(clean) >= 2 and any(x in clean[0] for x in ["CAPITAUX", "DETTES", "FOURNISSEURS"]):
            data.append({
                "DÉSIGNATION": clean[0],
                "MONTANT": clean_number(clean[1])
            })
        
        # CPC DGI
        elif len(clean) >= 4 and any(x in clean[0] for x in ["PRODUITS", "CHARGES"]):
            data.append({
                "DÉSIGNATION": clean[0],
                "EXERCICE": clean_number(clean[1]),
                "PRECEDENT": clean_number(clean[3]) if len(clean) > 3 else ""
            })
    
    return data

# Interface principale
uploaded_file = st.file_uploader("Choisissez un fichier PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Extraction en cours..."):
        # Lecture du PDF
        with pdfplumber.open(uploaded_file) as pdf:
            # Extraction identification
            ident_data = extract_identification(pdf)
            
            # Extraction des tableaux
            actif_data = []
            passif_data = []
            cpc_data = []
            
            for page in pdf.pages:
                if doc_type == "AMMC":
                    tables = extract_table_ammc(page)
                else:
                    tables = extract_table_dgi(page)
                
                # Classification selon le contenu
                for item in tables:
                    if any(k in item.get("DÉSIGNATION", "") for k in ["Immobilisations", "Stocks", "Créances", "Trésorerie", "BRUT"]):
                        actif_data.append(item)
                    elif any(k in item.get("DÉSIGNATION", "") for k in ["CAPITAUX", "Dettes", "Fournisseurs", "MONTANT"]):
                        passif_data.append(item)
                    else:
                        cpc_data.append(item)
            
            # Création de l'Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Onglet Identification
                ident_df = pd.DataFrame([ident_data]).T.reset_index()
                ident_df.columns = ["Champ", "Valeur"]
                ident_df.to_excel(writer, sheet_name="Identification", index=False)
                
                # Onglets
                if actif_data:
                    pd.DataFrame(actif_data).to_excel(writer, sheet_name="Bilan Actif", index=False)
                if passif_data:
                    pd.DataFrame(passif_data).to_excel(writer, sheet_name="Bilan Passif", index=False)
                if cpc_data:
                    pd.DataFrame(cpc_data).to_excel(writer, sheet_name="CPC", index=False)
            
            output.seek(0)
            
            # Affichage
            st.success("✅ Extraction terminée !")
            
            # Aperçu
            st.subheader("📋 Aperçu")
            col1, col2, col3 = st.columns(3)
            col1.metric("Lignes Actif", len(actif_data))
            col2.metric("Lignes Passif", len(passif_data))
            col3.metric("Lignes CPC", len(cpc_data))
            
            if ident_data:
                with st.expander("Identification"):
                    for k, v in ident_data.items():
                        st.write(f"**{k}:** {v}")
            
            # Bouton de téléchargement
            st.download_button(
                label="📥 Télécharger Excel",
                data=output,
                file_name=f"{ident_data.get('Raison sociale', 'document').replace(' ', '_')}_{doc_type}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
