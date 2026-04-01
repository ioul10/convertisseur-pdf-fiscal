import pdfplumber
from utils import clean_number, extract_identification_from_text, classify_row

class FiscalPDFExtractor:
    def __init__(self, pdf_path, doc_type):
        self.pdf_path = pdf_path
        self.doc_type = doc_type  # "AMMC" ou "DGI"
        self.identification = {}
        self.actif = []
        self.passif = []
        self.cpc = []
        self.stats = {"pages": 0, "tables": 0, "errors": []}
    
    def extract_all(self):
        """Extrait toutes les données"""
        with pdfplumber.open(self.pdf_path) as pdf:
            # 1. Extraction identification
            first_text = pdf.pages[0].extract_text()
            self.identification = extract_identification_from_text(first_text)
            self.stats["pages"] += 1
            
            # 2. Extraction des tableaux
            for page in pdf.pages:
                self.stats["pages"] += 1
                
                if self.doc_type == "AMMC":
                    self._extract_ammc_page(page)
                else:
                    self._extract_dgi_page(page)
        
        return {
            "identification": self.identification,
            "actif": self.actif,
            "passif": self.passif,
            "cpc": self.cpc,
            "stats": self.stats
        }
    
    def _extract_ammc_page(self, page):
        """Extrait une page au format AMMC"""
        table = page.extract_table({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 5,
        })
        
        if not table:
            return
        
        self.stats["tables"] += 1
        
        for row in table:
            if not row or all(c is None or str(c).strip() == "" for c in row):
                continue
            
            clean_row = [str(c).strip() if c else "" for c in row]
            
            # Bilan Actif (5 colonnes)
            if len(clean_row) >= 5 and any(x in clean_row[0] for x in ["Immobilisations", "Stocks", "Créances", "Trésorerie", "Terrains", "Constructions"]):
                item = {
                    "DÉSIGNATION": clean_row[0],
                    "BRUT": clean_number(clean_row[1]) if len(clean_row) > 1 else "",
                    "AMORT. & PROV.": clean_number(clean_row[2]) if len(clean_row) > 2 else "",
                    "NET N": clean_number(clean_row[3]) if len(clean_row) > 3 else "",
                    "NET N-1": clean_number(clean_row[4]) if len(clean_row) > 4 else ""
                }
                self.actif.append(item)
            
            # Bilan Passif (3 colonnes)
            elif len(clean_row) >= 3 and any(x in clean_row[0] for x in ["CAPITAUX", "Dettes", "Provisions", "Emprunts"]):
                item = {
                    "DÉSIGNATION": clean_row[0],
                    "EXERCICE N": clean_number(clean_row[1]),
                    "EXERCICE N-1": clean_number(clean_row[2])
                }
                self.passif.append(item)
            
            # CPC
            elif len(clean_row) >= 5 and any(x in clean_row[0] for x in ["PRODUITS", "CHARGES", "RESULTAT"]):
                item = {
                    "DÉSIGNATION": clean_row[0],
                    "PROPRES EXERCICE": clean_number(clean_row[1]),
                    "EXERCICES PRECEDENTS": clean_number(clean_row[2]),
                    "TOTAL N": clean_number(clean_row[3]),
                    "TOTAL N-1": clean_number(clean_row[4])
                }
                self.cpc.append(item)
    
    def _extract_dgi_page(self, page):
        """Extrait une page au format DGI"""
        table = page.extract_table({
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 5,
        })
        
        if not table:
            return
        
        self.stats["tables"] += 1
        
        for row in table:
            if not row or all(c is None or str(c).strip() == "" for c in row):
                continue
            
            clean_row = [str(c).strip() if c else "" for c in row]
            
            # Bilan Actif DGI (5 colonnes)
            if len(clean_row) >= 5 and any(x in str(row) for x in ["Brut exercice", "Immobilisations", "Stocks"]):
                item = {
                    "DÉSIGNATION": clean_row[0],
                    "BRUT EXERCICE": clean_number(clean_row[1]) if len(clean_row) > 1 else "",
                    "AMORT. & PROV.": clean_number(clean_row[2]) if len(clean_row) > 2 else "",
                    "NET EXERCICE": clean_number(clean_row[3]) if len(clean_row) > 3 else "",
                    "NET PRECEDENT": clean_number(clean_row[4]) if len(clean_row) > 4 else ""
                }
                self.actif.append(item)
            
            # Bilan Passif DGI (2 colonnes)
            elif len(clean_row) >= 2 and any(x in clean_row[0] for x in ["CAPITAUX", "DETTES", "FOURNISSEURS", "PASSIF"]):
                item = {
                    "DÉSIGNATION": clean_row[0],
                    "MONTANT": clean_number(clean_row[1])
                }
                self.passif.append(item)
            
            # CPC DGI
            elif len(clean_row) >= 4 and any(x in clean_row[0] for x in ["PRODUITS", "CHARGES", "RÉSULTAT"]):
                item = {
                    "DÉSIGNATION": clean_row[0],
                    "EXERCICE": clean_number(clean_row[1]),
                    "PRECEDENT": clean_number(clean_row[3]) if len(clean_row) > 3 else ""
                }
                self.cpc.append(item)
