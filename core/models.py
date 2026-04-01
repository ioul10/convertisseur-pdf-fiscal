"""Modèles de données"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    """Type de document fiscal"""
    AMMC = "AMMC"
    DGI = "DGI"
    UNKNOWN = "UNKNOWN"


class TableType(Enum):
    """Type de tableau extrait"""
    BILAN_ACTIF = "bilan_actif"
    BILAN_PASSIF = "bilan_passif"
    CPC = "cpc"
    UNKNOWN = "unknown"


@dataclass
class IdentificationData:
    """Données d'identification de l'entreprise"""
    raison_sociale: Optional[str] = None
    identifiant_fiscal: Optional[str] = None
    taxe_professionnelle: Optional[str] = None
    ice: Optional[str] = None
    adresse: Optional[str] = None
    exercice_debut: Optional[datetime] = None
    exercice_fin: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "Raison sociale": self.raison_sociale,
            "Identifiant fiscal": self.identifiant_fiscal,
            "Taxe professionnelle": self.taxe_professionnelle,
            "ICE": self.ice,
            "Adresse": self.adresse,
            "Exercice début": self.exercice_debut.strftime("%d/%m/%Y") if self.exercice_debut else None,
            "Exercice fin": self.exercice_fin.strftime("%d/%m/%Y") if self.exercice_fin else None
        }


@dataclass
class BilanActifLine:
    """Ligne du bilan actif"""
    designation: str
    brut: Optional[float] = None
    amortissements: Optional[float] = None
    net_n: Optional[float] = None
    net_n_1: Optional[float] = None
    level: int = 0  # Niveau d'indentation
    is_total: bool = False
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "DÉSIGNATION": self.designation,
            "BRUT": self.brut,
            "AMORT. & PROV.": self.amortissements,
            "NET N": self.net_n,
            "NET N-1": self.net_n_1
        }


@dataclass
class BilanPassifLine:
    """Ligne du bilan passif"""
    designation: str
    exercice_n: Optional[float] = None
    exercice_n_1: Optional[float] = None
    level: int = 0
    is_total: bool = False
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "DÉSIGNATION": self.designation,
            "EXERCICE N": self.exercice_n,
            "EXERCICE N-1": self.exercice_n_1
        }


@dataclass
class CPCLine:
    """Ligne du compte de produits et charges"""
    designation: str
    propres_exercice: Optional[float] = None
    exercices_precedents: Optional[float] = None
    total_n: Optional[float] = None
    total_n_1: Optional[float] = None
    level: int = 0
    is_total: bool = False
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "DÉSIGNATION": self.designation,
            "PROPRES À L'EXERCICE": self.propres_exercice,
            "EXERCICES PRÉCÉDENTS": self.exercices_precedents,
            "TOTAUX EXERCICE N": self.total_n,
            "TOTAUX EXERCICE N-1": self.total_n_1
        }


@dataclass
class ExtractionResult:
    """Résultat complet de l'extraction"""
    document_type: DocumentType
    identification: IdentificationData
    bilan_actif: List[BilanActifLine] = field(default_factory=list)
    bilan_passif: List[BilanPassifLine] = field(default_factory=list)
    cpc: List[CPCLine] = field(default_factory=list)
    
    # Métadonnées
    extraction_time: float = 0.0
    pages_processed: int = 0
    tables_found: int = 0
    confidence_score: float = 0.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_excel_data(self) -> Dict[str, List[Dict]]:
        """Convertit les données pour l'export Excel"""
        return {
            "Identification": [{"Champ": k, "Valeur": v} for k, v in self.identification.to_dict().items() if v],
            "Bilan Actif": [line.to_dict() for line in self.bilan_actif],
            "Bilan Passif": [line.to_dict() for line in self.bilan_passif],
            "CPC": [line.to_dict() for line in self.cpc],
            "Métadonnées": [
                {"Champ": "Type de document", "Valeur": self.document_type.value},
                {"Champ": "Pages traitées", "Valeur": self.pages_processed},
                {"Champ": "Tableaux trouvés", "Valeur": self.tables_found},
                {"Champ": "Score de confiance", "Valeur": f"{self.confidence_score:.2%}"}
            ]
        }
    
    def is_valid(self) -> bool:
        """Vérifie si l'extraction est valide"""
        return (
            self.identification.raison_sociale is not None and
            len(self.bilan_actif) > 0 and
            len(self.bilan_passif) > 0 and
            self.confidence_score > 0.5
        )
