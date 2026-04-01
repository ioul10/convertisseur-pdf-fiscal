import pdfplumber
from utils import clean_number, extract_identification_from_text

class FiscalPDFExtractor:
    def __init__(self, pdf_path, doc_type):
        self.pdf_path = pdf_path
        self.doc_type = doc_type
        self.identification = {}
        self.actif = []
        self.passif = []
        self.cpc = []
        self.stats = {"pages": 0, "tables": 0, "errors": []}
    
    def extract_all(self):
        """Extrait toutes les données"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Identification
                first_text = pdf.pages[0].extract_text()
                self.identification = extract_identification_from_text(first_text)
                self.stats["pages"] += 1
                
                # Extraction des tableaux
                for page in pdf.pages:
                    self.stats["pages"] += 1
                    
                    if self.doc_type == "AMMC":
                        self._extract_ammc_page(page)
                    else:
                        self._extract_dgi_page(page)
        except Exception as e:
            self.stats["errors"].append(str(e))
        
        return {
            "identification": self.identification,
            "actif": self.actif,
            "passif": self.passif,
            "cpc": self.cpc,
            "stats": self.stats
        }
    
    def _extract_ammc_page(self, page):
        """Extrait une page AMMC"""
        try:
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
                
                # Bilan Actif
                if len(clean_row) >= 5 and any(x in clean_row[0] for x in ["Immobilisations", "Stocks", "Créances", "Trésorerie", "Terrains", "Constructions"]):
                    self.actif.append({
                        "DÉSIGNATION": clean_row[0],
                        "BRUT": clean_number(clean_row[1]) if len(clean_row) > 1 else "",
                        "AMORT. & PROV.": clean_number(clean_row[2]) if len(clean_row) > 2 else "",
                        "NET N": clean_number(clean_row[3]) if len(clean_row) > 3 else "",
                        "NET N-1": clean_number(clean_row[4]) if len(clean_row) > 4 else ""
                    })
                
                # Bilan Passif
                elif len(clean_row) >= 3 and any(x in clean_row[0] for x in ["CAPITAUX", "Dettes", "Provisions"]):
                    self.passif.append({
                        "DÉSIGNATION": clean_row[0],
                        "EXERCICE N": clean_number(clean_row[1]),
                        "EXERCICE N-1": clean_number(clean_row[2])
                    })
                
                # CPC
                elif len(clean_row) >= 5 and any(x in clean_row[0] for x in ["PRODUITS", "CHARGES", "RESULTAT"]):
                    self.cpc.append({
                        "DÉSIGNATION": clean_row[0],
                        "PROPRES EXERCICE": clean_number(clean_row[1]),
                        "EXERCICES PRECEDENTS": clean_number(clean_row[2]),
                        "TOTAL N": clean_number(clean_row[3]),
                        "TOTAL N-1": clean_number(clean_row[4])
                    })
        except Exception as e:
            self.stats["errors"].append(f"Erreur page AMMC: {str(e)}")
    
    def _extract_dgi_page(self, page):
        """Extrait une page DGI"""
        try:
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
                
                # Bilan Actif DGI
                if len(clean_row) >= 5 and any(x in str(row) for x in ["Brut exercice", "Immobilisations"]):
                    self.actif.append({
                        "DÉSIGNATION": clean_row[0],
                        "BRUT EXERCICE": clean_number(clean_row[1]) if len(clean_row) > 1 else "",
                        "AMORT. & PROV.": clean_number(clean_row[2]) if len(clean_row) > 2 else "",
                        "NET EXERCICE": clean_number(clean_row[3]) if len(clean_row) > 3 else "",
                        "NET PRECEDENT": clean_number(clean_row[4]) if len(clean_row) > 4 else ""
                    })
                
                # Bilan Passif DGI
                elif len(clean_row) >= 2 and any(x in clean_row[0] for x in ["CAPITAUX", "DETTES", "FOURNISSEURS"]):
                    self.passif.append({
                        "DÉSIGNATION": clean_row[0],
                        "MONTANT": clean_number(clean_row[1])
                    })
                
                # CPC DGI
                elif len(clean_row) >= 4 and any(x in clean_row[0] for x in ["PRODUITS", "CHARGES"]):
                    self.cpc.append({
                        "DÉSIGNATION": clean_row[0],
                        "EXERCICE": clean_number(clean_row[1]),
                        "PRECEDENT": clean_number(clean_row[3]) if len(clean_row) > 3 else ""
                    })
        except Exception as e:
            self.stats["errors"].append(f"Erreur page DGI: {str(e)}")
