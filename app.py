import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO
import numpy as np

class FiscalPDFExtractor:
    """Classe pour extraire les données des PDF fiscaux marocains"""
    
    def __init__(self, pdf_path, doc_type):
        self.pdf_path = pdf_path
        self.doc_type = doc_type  # "AMMC" ou "DGI"
        self.data = {
            "identification": {},
            "bilan_actif": [],
            "bilan_passif": [],
            "cpc": []
        }
        
    def extract_identification(self):
        """Extrait les informations d'identification"""
        with pdfplumber.open(self.pdf_path) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            
            # Patterns communs
            patterns = {
                "Raison sociale": r"Raison sociale\s*:\s*(.+?)(?:\n|$)",
                "Identifiant fiscal": r"Identifiant fiscal\s*:\s*(\d+)",
                "Taxe professionnelle": r"Taxe professionnelle\s*:\s*(\d+)",
                "Adresse": r"Adresse\s*:\s*(.+?)(?:\n|$)"
            }
            
            # Extraction
            for key, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    self.data["identification"][key] = match.group(1).strip()
            
            # Extraction de l'exercice
            exercice_match = re.search(r"Exercice du (\d{2}/\d{2}/\d{4}) au (\d{2}/\d{2}/\d{4})", text)
            if exercice_match:
                self.data["identification"]["Exercice"] = f"Du {exercice_match.group(1)} au {exercice_match.group(2)}"
            
            return self.data["identification"]
    
    def extract_ammc_bilan_actif(self, page):
        """Extraction du bilan actif pour format AMMC"""
        # Structure AMMC : DÉSIGNATION | BRUT | AMORT. & PROV. | NET N | NET N-1
        table = page.extract_table({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 5,
        })
        
        if not table:
            return []
        
        # Nettoyer et structurer
        data = []
        current_section = ""
        
        for row in table:
            if not row or all(cell is None or cell.strip() == "" for cell in row):
                continue
                
            # Nettoyer les cellules
            cleaned_row = [cell.strip() if cell else "" for cell in row]
            
            # Identifier les sections
            if any(keyword in cleaned_row[0] for keyword in ["ACTIF", "IMMOBILISATIONS", "STOCKS", "CREANCES", "TRESORERIE"]):
                current_section = cleaned_row[0]
                continue
            
            # Extraire les valeurs
            if len(cleaned_row) >= 5:
                data.append({
                    "DÉSIGNATION": cleaned_row[0] or current_section,
                    "BRUT": self._clean_number(cleaned_row[1]),
                    "AMORT. & PROV.": self._clean_number(cleaned_row[2]),
                    "NET EXERCICE N": self._clean_number(cleaned_row[3]),
                    "NET EXERCICE N-1": self._clean_number(cleaned_row[4])
                })
        
        return data
    
    def extract_dgi_bilan_actif(self, page):
        """Extraction du bilan actif pour format DGI"""
        # Structure DGI : DÉSIGNATION | BRUT EXERCICE | AMORT. & PROV. | NET EXERCICE | NET EXERCICE PRÉCÉDENT
        table = page.extract_table({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 5,
        })
        
        if not table:
            return []
        
        data = []
        current_section = ""
        
        for row in table:
            if not row or all(cell is None or cell.strip() == "" for cell in row):
                continue
                
            cleaned_row = [cell.strip() if cell else "" for cell in row]
            
            # Identifier les sections
            if any(keyword in cleaned_row[0] for keyword in ["ACTIF", "IMMOBILISATION", "STOCKS", "CREANCES", "TRESORERIE"]):
                current_section = cleaned_row[0]
                continue
            
            if len(cleaned_row) >= 5:
                data.append({
                    "DÉSIGNATION": cleaned_row[0] or current_section,
                    "BRUT EXERCICE": self._clean_number(cleaned_row[1]),
                    "AMORT. & PROV.": self._clean_number(cleaned_row[2]),
                    "NET EXERCICE": self._clean_number(cleaned_row[3]),
                    "NET EXERCICE PRÉCÉDENT": self._clean_number(cleaned_row[4])
                })
        
        return data
    
    def extract_ammc_bilan_passif(self, page):
        """Extraction du bilan passif pour format AMMC"""
        table = page.extract_table({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 5,
        })
        
        if not table:
            return []
        
        data = []
        current_section = ""
        
        for row in table:
            if not row or all(cell is None or cell.strip() == "" for cell in row):
                continue
                
            cleaned_row = [cell.strip() if cell else "" for cell in row]
            
            if any(keyword in cleaned_row[0] for keyword in ["PASSIF", "CAPITAUX", "DETTES"]):
                current_section = cleaned_row[0]
                continue
            
            if len(cleaned_row) >= 3:
                data.append({
                    "DÉSIGNATION": cleaned_row[0] or current_section,
                    "EXERCICE N": self._clean_number(cleaned_row[1]),
                    "EXERCICE N-1": self._clean_number(cleaned_row[2])
                })
        
        return data
    
    def extract_dgi_bilan_passif(self, page):
        """Extraction du bilan passif pour format DGI"""
        table = page.extract_table({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 5,
        })
        
        if not table:
            return []
        
        data = []
        current_section = ""
        
        for row in table:
            if not row or all(cell is None or cell.strip() == "" for cell in row):
                continue
                
            cleaned_row = [cell.strip() if cell else "" for cell in row]
            
            if any(keyword in cleaned_row[0] for keyword in ["PASSIF", "CAPITAUX", "DETTES"]):
                current_section = cleaned_row[0]
                continue
            
            if len(cleaned_row) >= 2:
                data.append({
                    "DÉSIGNATION": cleaned_row[0] or current_section,
                    "MONTANT": self._clean_number(cleaned_row[1])
                })
        
        return data
    
    def extract_cpc(self, pages):
        """Extraction du Compte de Produits et Charges pour les deux formats"""
        all_data = []
        
        for page in pages:
            table = page.extract_table({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 5,
            })
            
            if not table:
                continue
            
            for row in table:
                if not row or all(cell is None or cell.strip() == "" for cell in row):
                    continue
                
                cleaned_row = [cell.strip() if cell else "" for cell in row]
                
                # Détection automatique de la structure
                if self.doc_type == "AMMC":
                    if len(cleaned_row) >= 5:
                        all_data.append({
                            "DÉSIGNATION": cleaned_row[0],
                            "PROPRES À L'EXERCICE": self._clean_number(cleaned_row[1]),
                            "EXERCICES PRÉCÉDENTS": self._clean_number(cleaned_row[2]),
                            "TOTAUX EXERCICE N": self._clean_number(cleaned_row[3]),
                            "TOTAUX EXERCICE N-1": self._clean_number(cleaned_row[4])
                        })
                else:  # DGI
                    if len(cleaned_row) >= 4:
                        all_data.append({
                            "DÉSIGNATION": cleaned_row[0],
                            "OPÉRATIONS PROPRES À L'EXERCICE": self._clean_number(cleaned_row[1]),
                            "OPÉRATIONS EXERCICES PRÉCÉDENTS": self._clean_number(cleaned_row[2]),
                            "TOTAUX EXERCICE": self._clean_number(cleaned_row[3]),
                            "TOTAUX EXERCICE PRÉCÉDENT": self._clean_number(cleaned_row[4]) if len(cleaned_row) > 4 else ""
                        })
        
        return all_data
    
    def _clean_number(self, value):
        """Nettoie et convertit les nombres"""
        if not value or value.strip() == "":
            return ""
        
        # Enlever les espaces et remplacer les virgules
        cleaned = value.strip().replace(" ", "").replace(",", ".")
        
        # Vérifier si c'est un nombre
        try:
            # Si c'est un nombre avec des décimales
            if "." in cleaned:
                return float(cleaned)
            else:
                return int(cleaned)
        except (ValueError, TypeError):
            return value
    
    def extract_all(self):
        """Extrait toutes les données du PDF"""
        with pdfplumber.open(self.pdf_path) as pdf:
            # Extraction identification (toujours première page)
            self.extract_identification()
            
            # Parcourir toutes les pages pour extraire les tableaux
            for page_num, page in enumerate(pdf.pages):
                if self.doc_type == "AMMC":
                    # AMMC: extraire selon la structure
                    if "Bilan (Actif)" in page.extract_text():
                        self.data["bilan_actif"].extend(self.extract_ammc_bilan_actif(page))
                    elif "Bilan (Passif)" in page.extract_text():
                        self.data["bilan_passif"].extend(self.extract_ammc_bilan_passif(page))
                    elif "Compte de Produits et Charges" in page.extract_text():
                        self.data["cpc"].extend(self.extract_cpc([page]))
                else:  # DGI
                    # DGI: extraire selon la structure spécifique
                    text = page.extract_text()
                    if "ACTIF" in text and "IMMOBILISATION" in text:
                        self.data["bilan_actif"].extend(self.extract_dgi_bilan_actif(page))
                    elif "PASSIF" in text or "CAPITAUX PROPRES" in text:
                        self.data["bilan_passif"].extend(self.extract_dgi_bilan_passif(page))
                    elif "PRODUITS D'EXPLOITATION" in text:
                        self.data["cpc"].extend(self.extract_cpc([page]))
        
        return self.data
    
    def to_excel(self):
        """Convertit les données extraites en fichier Excel"""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Onglet Identification
            ident_df = pd.DataFrame([
                {"Champ": k, "Valeur": v} for k, v in self.data["identification"].items()
            ])
            ident_df.to_excel(writer, sheet_name="Identification", index=False)
            
            # Onglet Bilan Actif
            if self.data["bilan_actif"]:
                actif_df = pd.DataFrame(self.data["bilan_actif"])
                actif_df.to_excel(writer, sheet_name="Bilan Actif", index=False)
            
            # Onglet Bilan Passif
            if self.data["bilan_passif"]:
                passif_df = pd.DataFrame(self.data["bilan_passif"])
                passif_df.to_excel(writer, sheet_name="Bilan Passif", index=False)
            
            # Onglet CPC
            if self.data["cpc"]:
                cpc_df = pd.DataFrame(self.data["cpc"])
                cpc_df.to_excel(writer, sheet_name="CPC", index=False)
        
        output.seek(0)
        return output


def main():
    st.set_page_config(page_title="Convertisseur PDF Fiscal Marocain", layout="wide")
    
    st.title("📄 Convertisseur PDF Fiscal Marocain")
    st.markdown("---")
    
    # Sidebar pour les paramètres
    with st.sidebar:
        st.header("⚙️ Configuration")
        doc_type = st.radio(
            "Type de document fiscal",
            ["AMMC", "DGI"],
            help="Sélectionnez le type de document à convertir"
        )
        
        st.markdown("---")
        st.info("""
        **Formats supportés:**
        - AMMC: Modèle Comptable Normal
        - DGI: Déclaration fiscale IS
        
        **Structure Excel:**
        - Onglet Identification
        - Onglet Bilan Actif
        - Onglet Bilan Passif
        - Onglet CPC
        """)
    
    # Zone principale
    uploaded_file = st.file_uploader(
        "📂 Déposez votre fichier PDF fiscal",
        type=["pdf"],
        help="Glissez-déposez ou sélectionnez un fichier PDF"
    )
    
    if uploaded_file:
        with st.spinner("📊 Traitement du PDF en cours..."):
            try:
                # Extraction
                extractor = FiscalPDFExtractor(uploaded_file, doc_type)
                data = extractor.extract_all()
                
                # Affichage des résultats
                st.success("✅ Extraction réussie !")
                
                # Aperçu des données extraites
                st.subheader("📋 Aperçu des données extraites")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Identification**")
                    if data["identification"]:
                        ident_df = pd.DataFrame([data["identification"]]).T
                        ident_df.columns = ["Valeur"]
                        st.dataframe(ident_df, use_container_width=True)
                    else:
                        st.warning("Aucune donnée d'identification trouvée")
                
                with col2:
                    st.write("**Statistiques**")
                    st.metric("Lignes Bilan Actif", len(data["bilan_actif"]))
                    st.metric("Lignes Bilan Passif", len(data["bilan_passif"]))
                    st.metric("Lignes CPC", len(data["cpc"]))
                
                # Aperçu du Bilan Actif
                if data["bilan_actif"]:
                    st.write("**Bilan Actif (Aperçu)**")
                    preview_df = pd.DataFrame(data["bilan_actif"][:10])
                    st.dataframe(preview_df, use_container_width=True)
                
                # Export Excel
                st.markdown("---")
                excel_file = extractor.to_excel()
                
                st.download_button(
                    label="📥 Télécharger le fichier Excel",
                    data=excel_file,
                    file_name=f"{data['identification'].get('Raison sociale', 'document')}_{doc_type}_fiscal.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"❌ Erreur lors du traitement : {str(e)}")
                st.exception(e)


if __name__ == "__main__":
    main()
