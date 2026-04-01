"""Configuration du projet"""

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ExtractionConfig:
    """Configuration de l'extraction"""
    
    # Stratégies d'extraction
    VERTICAL_STRATEGY: str = "lines"
    HORIZONTAL_STRATEGY: str = "lines"
    SNAP_TOLERANCE: int = 5
    SNAP_X_TOLERANCE: int = 3
    SNAP_Y_TOLERANCE: int = 3
    
    # Seuils de confiance
    MIN_TABLE_ROWS: int = 3
    MIN_TABLE_COLS: int = 2
    CONFIDENCE_THRESHOLD: float = 0.7
    
    # Patterns regex pour l'identification
    IDENTIFICATION_PATTERNS: Dict[str, str] = {
        "raison_sociale": r"Raison sociale\s*:\s*(.+?)(?:\n|$)",
        "identifiant_fiscal": r"Identifiant fiscal\s*:\s*(\d+)",
        "taxe_professionnelle": r"Taxe professionnelle\s*:\s*(\d+)",
        "adresse": r"Adresse\s*:\s*(.+?)(?:\n|$)",
        "ice": r"ICE\s*:\s*(\d+)",
        "exercice_debut": r"Exercice du (\d{2}/\d{2}/\d{4})",
        "exercice_fin": r"au (\d{2}/\d{2}/\d{4})"
    }
    
    # Mapping des colonnes par type de document
    COLUMN_MAPPING: Dict[str, Dict[str, List[str]]] = {
        "AMMC": {
            "actif": ["BRUT", "AMORTISSEMENTS", "NET_N", "NET_N-1"],
            "passif": ["EXERCICE_N", "EXERCICE_N-1"],
            "cpc": ["PROPRES_EXERCICE", "EXERCICES_PRECEDENTS", "TOTAL_N", "TOTAL_N-1"]
        },
        "DGI": {
            "actif": ["BRUT_EXERCICE", "AMORTISSEMENTS", "NET_EXERCICE", "NET_PRECEDENT"],
            "passif": ["MONTANT"],
            "cpc": ["EXERCICE", "PRECEDENT"]
        }
    }
    
    # Postes comptables obligatoires
    REQUIRED_ACCOUNTS: Dict[str, List[str]] = {
        "actif": [
            "Immobilisations en non valeurs",
            "Immobilisations incorporelles",
            "Immobilisations corporelles",
            "Stocks",
            "Créances de l'actif circulant",
            "Trésorerie-Actif"
        ],
        "passif": [
            "Capital social",
            "Résultat net",
            "Dettes de financement",
            "Dettes du passif circulant"
        ]
    }


@dataclass
class ValidationRules:
    """Règles de validation des données"""
    
    # Formats attendus
    DATE_FORMAT: str = "%d/%m/%Y"
    AMOUNT_PRECISION: int = 2
    
    # Seuils de validité
    MIN_CAPITAL: float = 0
    MAX_AMOUNT: float = 1e12
    
    # Patterns de validation
    ID_FISCAL_PATTERN: str = r"^\d{7}$"
    TP_PATTERN: str = r"^\d{9}$"
    ICE_PATTERN: str = r"^\d{15}$"
