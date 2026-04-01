"""Fonctions utilitaires"""

import re
from typing import Optional, Any, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def clean_number(value: Any) -> Optional[float]:
    """
    Nettoie et convertit un nombre.
    
    Args:
        value: Valeur à convertir
        
    Returns:
        Nombre converti ou None
    """
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    value_str = str(value).strip()
    
    if not value_str or value_str == "":
        return None
    
    # Enlever les espaces et remplacer les virgules
    cleaned = value_str.replace(" ", "").replace(",", ".")
    
    # Gérer les nombres négatifs
    is_negative = cleaned.startswith("-")
    if is_negative:
        cleaned = cleaned[1:]
    
    # Extraire le nombre
    match = re.search(r"[\d.]+", cleaned)
    if not match:
        return None
    
    try:
        result = float(match.group())
        return -result if is_negative else result
    except ValueError:
        return None


def clean_text(text: Optional[str]) -> Optional[str]:
    """Nettoie une chaîne de caractères"""
    if not text:
        return None
    
    # Enlever les espaces multiples
    cleaned = re.sub(r"\s+", " ", text.strip())
    
    # Enlever les caractères spéciaux
    cleaned = re.sub(r"[^\w\s\-:éèêëàâäôöûüç]", "", cleaned)
    
    return cleaned if cleaned else None


def parse_french_date(date_str: str) -> Optional[datetime]:
    """
    Parse une date au format français.
    
    Args:
        date_str: Chaîne de date (ex: "31/12/2023")
        
    Returns:
        Objet datetime ou None
    """
    if not date_str:
        return None
    
    # Patterns de dates possibles
    patterns = [
        r"(\d{2})/(\d{2})/(\d{4})",
        r"(\d{2})-(\d{2})-(\d{4})",
        r"(\d{2})\s+(\d{2})\s+(\d{4})"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                day, month, year = match.groups()
                return datetime(int(year), int(month), int(day))
            except ValueError:
                continue
    
    return None


def detect_document_type(text: str) -> str:
    """
    Détecte le type de document à partir du texte.
    
    Args:
        text: Texte extrait du PDF
        
    Returns:
        "AMMC", "DGI" ou "UNKNOWN"
    """
    text_upper = text.upper()
    
    # Indicateurs AMMC
    ammc_indicators = [
        "MODÈLE COMPTABLE NORMAL",
        "AMMC",
        "BILAN (ACTIF)",
        "BILAN (PASSIF)",
        "COMPTE DE PRODUITS ET CHARGES"
    ]
    
    # Indicateurs DGI
    dgi_indicators = [
        "DÉCLARATION SOUSCRITE",
        "IMPÔTS SUR LES SOCIÉTÉS",
        "IDENTIFICATION DU CONTRIBUABLE",
        "BRUT EXERCICE"
    ]
    
    ammc_score = sum(1 for ind in ammc_indicators if ind in text_upper)
    dgi_score = sum(1 for ind in dgi_indicators if ind in text_upper)
    
    if ammc_score > dgi_score:
        return "AMMC"
    elif dgi_score > ammc_score:
        return "DGI"
    else:
        return "UNKNOWN"


def normalize_designation(designation: str) -> str:
    """Normalise une désignation comptable"""
    if not designation:
        return ""
    
    # Enlever les numéros de section
    cleaned = re.sub(r"^[A-Z]\s*", "", designation)
    
    # Enlever les crochets et leur contenu
    cleaned = re.sub(r"\[[A-Z]\]", "", cleaned)
    
    # Nettoyer les espaces
    cleaned = " ".join(cleaned.split())
    
    return cleaned.strip()


def calculate_confidence(table_data: List[List]) -> float:
    """
    Calcule un score de confiance pour un tableau extrait.
    
    Args:
        table_data: Données du tableau
        
    Returns:
        Score entre 0 et 1
    """
    if not table_data:
        return 0.0
    
    total_cells = 0
    non_empty_cells = 0
    
    for row in table_data:
        for cell in row:
            total_cells += 1
            if cell and str(cell).strip():
                non_empty_cells += 1
    
    if total_cells == 0:
        return 0.0
    
    return non_empty_cells / total_cells


def merge_multipage_tables(tables: List[List[List]]]) -> List[List]:
    """Fusionne les tableaux sur plusieurs pages"""
    if not tables:
        return []
    
    merged = []
    
    for table in tables:
        if not merged:
            merged = table
        else:
            # Vérifier si la première ligne est une continuation
            if table and len(table[0]) == len(merged[0]):
                merged.extend(table[1:] if len(table) > 1 else table)
    
    return merged


class ProgressTracker:
    """Suivi de progression pour les longues extractions"""
    
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.callback = None
    
    def set_callback(self, callback):
        self.callback = callback
    
    def update(self, step: int = 1):
        self.current += step
        if self.callback:
            self.callback(self.current, self.total)
    
    def get_progress(self) -> float:
        return self.current / self.total if self.total > 0 else 0
