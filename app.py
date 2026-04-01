import streamlit as st
import pandas as pd
from io import BytesIO
from extractor import FiscalPDFExtractor

st.set_page_config(page_title="Convertisseur PDF Fiscal", layout="wide")

st.title("📄 Convertisseur PDF Fiscal Marocain")
st.markdown("---")

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
    
    **Fonctionnalités:**
    - Extraction automatique
    - Bilan Actif & Passif
    - Compte de Produits et Charges
    """)

uploaded_file = st.file_uploader("📂 Déposez votre fichier PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("📊 Extraction en cours..."):
        try:
            extractor = FiscalPDFExtractor(uploaded_file, doc_type)
            data = extractor.extract_all()
            
            st.success("✅ Extraction réussie !")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Pages traitées", data["stats"]["pages"])
            with col2:
                st.metric("Tableaux trouvés", data["stats"]["tables"])
            with col3:
                st.metric("Lignes Actif", len(data["actif"]))
            with col4:
                st.metric("Lignes Passif", len(data["passif"]))
            
            st.subheader("📋 Aperçu des données")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Identification", "Bilan Actif", "Bilan Passif", "CPC"])
            
            with tab1:
                if data["identification"]:
                    ident_df = pd.DataFrame([data["identification"]]).T
                    ident_df.columns = ["Valeur"]
                    st.dataframe(ident_df, use_container_width=True)
                else:
                    st.warning("Aucune donnée d'identification")
            
            with tab2:
                if data["actif"]:
                    st.dataframe(pd.DataFrame(data["actif"][:20]), use_container_width=True)
                else:
                    st.warning("Aucune donnée Bilan Actif")
            
            with tab3:
                if data["passif"]:
                    st.dataframe(pd.DataFrame(data["passif"][:20]), use_container_width=True)
                else:
                    st.warning("Aucune donnée Bilan Passif")
            
            with tab4:
                if data["cpc"]:
                    st.dataframe(pd.DataFrame(data["cpc"][:20]), use_container_width=True)
                else:
                    st.warning("Aucune donnée CPC")
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                ident_df = pd.DataFrame([data["identification"]]).T.reset_index()
                ident_df.columns = ["Champ", "Valeur"]
                ident_df.to_excel(writer, sheet_name="Identification", index=False)
                
                if data["actif"]:
                    pd.DataFrame(data["actif"]).to_excel(writer, sheet_name="Bilan Actif", index=False)
                if data["passif"]:
                    pd.DataFrame(data["passif"]).to_excel(writer, sheet_name="Bilan Passif", index=False)
                if data["cpc"]:
                    pd.DataFrame(data["cpc"]).to_excel(writer, sheet_name="CPC", index=False)
                
                stats_df = pd.DataFrame([data["stats"]])
                stats_df.to_excel(writer, sheet_name="Statistiques", index=False)
            
            output.seek(0)
            
            filename = f"{data['identification'].get('Raison sociale', 'document').replace(' ', '_')}_{doc_type}.xlsx"
            st.download_button(
                label="📥 Télécharger Excel",
                data=output,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            if data["stats"]["errors"]:
                with st.expander("⚠️ Détails des erreurs"):
                    for err in data["stats"]["errors"]:
                        st.error(err)
        
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
            st.exception(e)
