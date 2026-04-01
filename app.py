import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.stats = {
            "pages_processed": 0,
            "tables_found": 0,
            "errors": []
        }
    
    def extract_identification(self):
        """Extrait les informations d'identification"""
        try:
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
                
                self.stats["pages_processed"] += 1
                
        except Exception as e:
            error_msg = f"Erreur extraction identification: {str(e)}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
        
        return self.data["identification"]
    
    def _clean_number(self, value):
        """Nettoie et convertit les nombres"""
        if not value or value.strip() == "":
            return ""
        
        try:
            # Enlever les espaces et remplacer les virgules
            cleaned = value.strip().replace(" ", "").replace(",", ".")
            
            # Gérer les nombres négatifs
            if cleaned.startswith('-'):
                cleaned = cleaned[1:]
                is_negative = True
            else:
                is_negative = False
            
            # Vérifier si c'est un nombre
            if "." in cleaned:
                result = float(cleaned)
            else:
                result = int(cleaned)
            
            return -result if is_negative else result
            
        except (ValueError, TypeError):
            return value
    
    def extract_all(self):
        """Extrait toutes les données du PDF"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Extraction identification (toujours première page)
                self.extract_identification()
                
                # Parcourir toutes les pages pour extraire les tableaux
                for page_num, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        self.stats["pages_processed"] += 1
                        
                        if self.doc_type == "AMMC":
                            # AMMC: extraire selon la structure
                            if "Bilan (Actif)" in text:
                                self.data["bilan_actif"].extend(self.extract_ammc_bilan_actif(page))
                                self.stats["tables_found"] += 1
                            elif "Bilan (Passif)" in text:
                                self.data["bilan_passif"].extend(self.extract_ammc_bilan_passif(page))
                                self.stats["tables_found"] += 1
                            elif "Compte de Produits et Charges" in text:
                                self.data["cpc"].extend(self.extract_cpc([page]))
                                self.stats["tables_found"] += 1
                        else:  # DGI
                            # DGI: extraire selon la structure spécifique
                            if "ACTIF" in text and "IMMOBILISATION" in text:
                                self.data["bilan_actif"].extend(self.extract_dgi_bilan_actif(page))
                                self.stats["tables_found"] += 1
                            elif "PASSIF" in text or "CAPITAUX PROPRES" in text:
                                self.data["bilan_passif"].extend(self.extract_dgi_bilan_passif(page))
                                self.stats["tables_found"] += 1
                            elif "PRODUITS D'EXPLOITATION" in text:
                                self.data["cpc"].extend(self.extract_cpc([page]))
                                self.stats["tables_found"] += 1
                                
                    except Exception as e:
                        error_msg = f"Erreur page {page_num + 1}: {str(e)}"
                        logger.error(error_msg)
                        self.stats["errors"].append(error_msg)
                
        except Exception as e:
            error_msg = f"Erreur lors de l'ouverture du PDF: {str(e)}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            raise
        
        return self.data
    
    def extract_ammc_bilan_actif(self, page):
        """Extraction du bilan actif pour format AMMC"""
        # ... (code complet comme avant)
        pass
    
    def extract_ammc_bilan_passif(self, page):
        """Extraction du bilan passif pour format AMMC"""
        # ... (code complet comme avant)
        pass
    
    def extract_dgi_bilan_actif(self, page):
        """Extraction du bilan actif pour format DGI"""
        # ... (code complet comme avant)
        pass
    
    def extract_dgi_bilan_passif(self, page):
        """Extraction du bilan passif pour format DGI"""
        # ... (code complet comme avant)
        pass
    
    def extract_cpc(self, pages):
        """Extraction du Compte de Produits et Charges"""
        # ... (code complet comme avant)
        pass
    
    def to_excel(self):
        """Convertit les données extraites en fichier Excel"""
        output = BytesIO()
        
        try:
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
                
                # Onglet Statistiques (optionnel)
                stats_df = pd.DataFrame([self.stats])
                stats_df.to_excel(writer, sheet_name="Statistiques", index=False)
                
        except Exception as e:
            logger.error(f"Erreur création Excel: {str(e)}")
            raise
        
        output.seek(0)
        return output


def main():
    st.set_page_config(
        page_title="Convertisseur PDF Fiscal Marocain",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 Convertisseur PDF Fiscal Marocain")
    st.markdown("---")
    
    # Sidebar
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
        - Onglet Statistiques
        """)
        
        st.markdown("---")
        st.caption(f"Version 1.0.0 | {datetime.now().strftime('%Y')}")
    
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
                
                # Métriques
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Pages traitées", extractor.stats["pages_processed"])
                with col2:
                    st.metric("Tableaux trouvés", extractor.stats["tables_found"])
                with col3:
                    st.metric("Lignes Bilan Actif", len(data["bilan_actif"]))
                with col4:
                    st.metric("Lignes CPC", len(data["cpc"]))
                
                # Aperçu des données extraites
                st.subheader("📋 Aperçu des données extraites")
                
                tab1, tab2, tab3, tab4 = st.tabs(["Identification", "Bilan Actif", "Bilan Passif", "CPC"])
                
                with tab1:
                    if data["identification"]:
                        ident_df = pd.DataFrame([data["identification"]]).T
                        ident_df.columns = ["Valeur"]
                        st.dataframe(ident_df, use_container_width=True)
                    else:
                        st.warning("Aucune donnée d'identification trouvée")
                
                with tab2:
                    if data["bilan_actif"]:
                        preview_df = pd.DataFrame(data["bilan_actif"][:20])
                        st.dataframe(preview_df, use_container_width=True)
                        if len(data["bilan_actif"]) > 20:
                            st.info(f"... et {len(data['bilan_actif']) - 20} lignes supplémentaires")
                    else:
                        st.warning("Aucune donnée de bilan actif trouvée")
                
                with tab3:
                    if data["bilan_passif"]:
                        preview_df = pd.DataFrame(data["bilan_passif"][:20])
                        st.dataframe(preview_df, use_container_width=True)
                    else:
                        st.warning("Aucune donnée de bilan passif trouvée")
                
                with tab4:
                    if data["cpc"]:
                        preview_df = pd.DataFrame(data["cpc"][:20])
                        st.dataframe(preview_df, use_container_width=True)
                    else:
                        st.warning("Aucune donnée CPC trouvée")
                
                # Export Excel
                st.markdown("---")
                excel_file = extractor.to_excel()
                
                filename = f"{data['identification'].get('Raison sociale', 'document').replace(' ', '_')}_{doc_type}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                
                st.download_button(
                    label="📥 Télécharger le fichier Excel",
                    data=excel_file,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                # Afficher les erreurs si présentes
                if extractor.stats["errors"]:
                    with st.expander("⚠️ Détails des erreurs"):
                        for error in extractor.stats["errors"]:
                            st.error(error)
                
            except Exception as e:
                st.error(f"❌ Erreur lors du traitement : {str(e)}")
                if st.checkbox("Afficher les détails techniques"):
                    st.exception(e)


if __name__ == "__main__":
    main()
