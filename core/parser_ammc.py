"""Parser spécifique pour les documents AMMC"""

import re
from typing import List, Dict, Any, Optional
import pdfplumber

from .models import (
    BilanActifLine, BilanPassifLine, CPCLine,
    IdentificationData, TableType
)
from .utils import (
    clean_number, clean_text, normalize_designation,
    calculate_confidence, parse_french_date
)
from config.settings import ExtractionConfig


class AMMCParser:
    """Parser pour les documents AMMC"""
    
    def __init__(self, config: ExtractionConfig = None):
        self.config = config or ExtractionConfig()
        
        # Mots-clés pour l'identification des sections
        self.section_keywords = {
            TableType.BILAN_ACTIF: [
                "ACTIF", "IMMOBILISATIONS", "STOCKS", "CREANCES",
                "TRESORERIE-ACTIF", "TOTAL GENERAL"
            ],
            TableType.BILAN_PASSIF: [
                "PASSIF", "CAPITAUX PROPRES", "DETTES DE FINANCEMENT",
                "DETTES DU PASSIF CIRCULANT"
            ],
            TableType.CPC: [
                "COMPTE DE PRODUITS ET CHARGES", "PRODUITS D'EXPLOITATION",
                "CHARGES D'EXPLOITATION", "RESULTAT NET"
            ]
        }
    
    def parse_identification(self, page: pdfplumber.Page) -> IdentificationData:
        """Extrait les données d'identification"""
        text = page.extract_text()
        if not text:
            return IdentificationData()
        
        data = IdentificationData()
        
        # Extraction avec regex
        for field, pattern in self.config.IDENTIFICATION_PATTERNS.items():
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
                elif field == "ice":
                    data.ice = value
        
        # Extraction des dates d'exercice
        ex_match = re.search(
            r"Exercice du (\d{2}/\d{2}/\d{4}) au (\d{2}/\d{2}/\d{4})",
            text
        )
        if ex_match:
            data.exercice_debut = parse_french_date(ex_match.group(1))
            data.exercice_fin = parse_french_date(ex_match.group(2))
        
        return data
    
    def parse_bilan_actif(self, page: pdfplumber.Page) -> List[BilanActifLine]:
        """Extrait le bilan actif"""
        table = self._extract_table(page)
        if not table:
            return []
        
        lines = []
        current_level = 0
        
        for row in table:
            if not row or len(row) < 5:
                continue
            
            designation = clean_text(row[0])
            if not designation:
                continue
            
            # Normaliser la désignation
            designation = normalize_designation(designation)
            
            # Déterminer le niveau d'indentation
            if designation.startswith("  ") or designation.startswith("\t"):
                current_level += 1
            else:
                current_level = 0
            
            # Créer la ligne
            line = BilanActifLine(
                designation=designation,
                brut=clean_number(row[1]) if len(row) > 1 else None,
                amortissements=clean_number(row[2]) if len(row) > 2 else None,
                net_n=clean_number(row[3]) if len(row) > 3 else None,
                net_n_1=clean_number(row[4]) if len(row) > 4 else None,
                level=current_level,
                is_total="TOTAL" in designation.upper(),
                confidence=0.9  # Score par défaut
            )
            
            lines.append(line)
        
        return lines
    
    def parse_bilan_passif(self, page: pdfplumber.Page) -> List[BilanPassifLine]:
        """Extrait le bilan passif"""
        table = self._extract_table(page)
        if not table:
            return []
        
        lines = []
        current_level = 0
        
        for row in table:
            if not row or len(row) < 3:
                continue
            
            designation = clean_text(row[0])
            if not designation:
                continue
            
            designation = normalize_designation(designation)
            
            if designation.startswith("  ") or designation.startswith("\t"):
                current_level += 1
            else:
                current_level = 0
            
            line = BilanPassifLine(
                designation=designation,
                exercice_n=clean_number(row[1]),
                exercice_n_1=clean_number(row[2]) if len(row) > 2 else None,
                level=current_level,
                is_total="TOTAL" in designation.upper()
            )
            
            lines.append(line)
        
        return lines
    
    def parse_cpc(self, page: pdfplumber.Page) -> List[CPCLine]:
        """Extrait le compte de produits et charges"""
        table = self._extract_table(page)
        if not table:
            return []
        
        lines = []
        current_level = 0
        
        for row in table:
            if not row or len(row) < 5:
                continue
            
            designation = clean_text(row[0])
            if not designation:
                continue
            
            designation = normalize_designation(designation)
            
            if designation.startswith("  ") or designation.startswith("\t"):
                current_level += 1
            else:
                current_level = 0
            
            line = CPCLine(
                designation=designation,
                propres_exercice=clean_number(row[1]),
                exercices_precedents=clean_number(row[2]),
                total_n=clean_number(row[3]),
                total_n_1=clean_number(row[4]) if len(row) > 4 else None,
                level=current_level,
                is_total="TOTAL" in designation.upper()
            )
            
            lines.append(line)
        
        return lines
    
    def _extract_table(self, page: pdfplumber.Page) -> List[List[str]]:
        """Extrait un tableau avec les paramètres optimisés"""
        try:
            table = page.extract_table({
                "vertical_strategy": self.config.VERTICAL_STRATEGY,
                "horizontal_strategy": self.config.HORIZONTAL_STRATEGY,
                "snap_tolerance": self.config.SNAP_TOLERANCE,
                "snap_x_tolerance": self.config.SNAP_X_TOLERANCE,
                "snap_y_tolerance": self.config.SNAP_Y_TOLERANCE,
            })
            return table if table else []
        except Exception as e:
            print(f"Erreur extraction tableau: {e}")
            return []
    
    def detect_table_type(self, page: pdfplumber.Page) -> Optional[TableType]:
        """Détecte le type de tableau sur la page"""
        text = page.extract_text()
        if not text:
            return None
        
        text_upper = text.upper()
        
        for table_type, keywords in self.section_keywords.items():
            for keyword in keywords:
                if keyword.upper() in text_upper:
                    return table_type
        
        return None
