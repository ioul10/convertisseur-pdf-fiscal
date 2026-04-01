import streamlit as st

st.title("📄 Convertisseur PDF Fiscal Marocain")

# Test d'imports
try:
    from core.extractor import FiscalPDFExtractor
    from core.models import DocumentType
    from config.settings import ExtractionConfig
    st.success("✅ Tous les modules sont chargés correctement")
except ImportError as e:
    st.error(f"❌ Erreur d'import: {e}")
    st.stop()

st.write("L'application est prête !")

with st.sidebar:
    doc_type = st.radio("Type", ["AMMC", "DGI"])

uploaded_file = st.file_uploader("Choisissez un PDF", type=["pdf"])

if uploaded_file:
    st.write(f"Fichier: {uploaded_file.name}")
