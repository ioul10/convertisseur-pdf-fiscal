import re
from typing import List, Optional
import pdfplumber

from .models import BilanActifLine, BilanPassifLine, CPCLine, IdentificationData
from .utils import clean_number, clean_text, normalize_designation, parse_french_date
from config.settings import ExtractionConfig


class AMMCParser:
    def __init__(self, config: ExtractionConfig = None):
        self.config = config or ExtractionConfig()
    
    def parse_identification(self, page: pdfplumber.Page) -> IdentificationData:
        text = page.extract_text()
        if not text:
            return IdentificationData()
        
        data = IdentificationData()
        
        patterns = {
            "raison_sociale": r"Raison sociale\s*:\s*(.+?)(?:\n|$)",
            "identifiant_fiscal": r"Identifiant fiscal\s*:\s*(\d+)",
            "taxe_professionnelle": r"Taxe professionnelle\s*:\s*(\d+)",
            "adresse": r"Adresse\s*:\s*(.+?)(?:\n|$)"
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if field == "raison_sociale":
                    data.raison_sociale = clean_text(value)
                elif field == "identifiant_fiscal":
                    data.identifiant_fiscal = value
                elif field == "taxe_professionnelle":
                    data.taxe_professionnelle = value
                elif field == "adresse":
                    data.adresse = clean_text(value)
        
        ex_match = re.search(r"Exercice du (\d{2}/\d{2}/\d{4}) au (\d{2}/\d{2}/\d{4})", text)
        if ex_match:
            data.exercice_debut = parse_french_date(ex_match.group(1))
            data.exercice_fin = parse_french_date(ex_match.group(2))
        
        return data
    
    def parse_bilan_actif(self, page: pdfplumber.Page) -> List[BilanActifLine]:
        table = self._extract_table(page)
        if not table:
            return []
        
        lines = []
        for row in table:
            if not row or len(row) < 5:
                continue
            designation = clean_text(row[0])
            if not designation:
                continue
            designation = normalize_designation(designation)
            
            line = BilanActifLine(
                designation=designation,
                brut=clean_number(row[1]) if len(row) > 1 else None,
                amortissements=clean_number(row[2]) if len(row) > 2 else None,
                net_n=clean_number(row[3]) if len(row) > 3 else None,
                net_n_1=clean_number(row[4]) if len(row) > 4 else None,
                is_total="TOTAL" in designation.upper()
            )
            lines.append(line)
        return lines
    
    def parse_bilan_passif(self, page: pdfplumber.Page) -> List[BilanPassifLine]:
        table = self._extract_table(page)
        if not table:
            return []
        
        lines = []
        for row in table:
            if not row or len(row) < 3:
                continue
            designation = clean_text(row[0])
            if not designation:
                continue
            designation = normalize_designation(designation)
            
            line = BilanPassifLine(
                designation=designation,
                exercice_n=clean_number(row[1]),
                exercice_n_1=clean_number(row[2]) if len(row) > 2 else None,
                is_total="TOTAL" in designation.upper()
            )
            lines.append(line)
        return lines
    
    def parse_cpc(self, page: pdfplumber.Page) -> List[CPCLine]:
        table = self._extract_table(page)
        if not table:
            return []
        
        lines = []
        for row in table:
            if not row or len(row) < 5:
                continue
            designation = clean_text(row[0])
            if not designation:
                continue
            designation = normalize_designation(designation)
            
            line = CPCLine(
                designation=designation,
                propres_exercice=clean_number(row[1]),
                exercices_precedents=clean_number(row[2]),
                total_n=clean_number(row[3]),
                total_n_1=clean_number(row[4]) if len(row) > 4 else None,
                is_total="TOTAL" in designation.upper()
            )
            lines.append(line)
        return lines
    
    def _extract_table(self, page: pdfplumber.Page) -> List[List[str]]:
        try:
            table = page.extract_table({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 5,
            })
            return table if table else []
        except Exception:
            return []
