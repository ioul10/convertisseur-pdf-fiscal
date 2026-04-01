import re
from typing import Optional, Any, List
from datetime import datetime

def clean_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value_str = str(value).strip()
    if not value_str or value_str == "":
        return None
    cleaned = value_str.replace(" ", "").replace(",", ".")
    is_negative = cleaned.startswith("-")
    if is_negative:
        cleaned = cleaned[1:]
    match = re.search(r"[\d.]+", cleaned)
    if not match:
        return None
    try:
        result = float(match.group())
        return -result if is_negative else result
    except ValueError:
        return None

def clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", text.strip())
    cleaned = re.sub(r"[^\w\s\-:éèêëàâäôöûüç]", "", cleaned)
    return cleaned if cleaned else None

def parse_french_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
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
    text_upper = text.upper()
    ammc_indicators = ["MODÈLE COMPTABLE NORMAL", "AMMC", "BILAN (ACTIF)"]
    dgi_indicators = ["DÉCLARATION SOUSCRITE", "IMPÔTS SUR LES SOCIÉTÉS", "BRUT EXERCICE"]
    ammc_score = sum(1 for ind in ammc_indicators if ind in text_upper)
    dgi_score = sum(1 for ind in dgi_indicators if ind in text_upper)
    if ammc_score > dgi_score:
        return "AMMC"
    elif dgi_score > ammc_score:
        return "DGI"
    return "UNKNOWN"

def normalize_designation(designation: str) -> str:
    if not designation:
        return ""
    cleaned = re.sub(r"^[A-Z]\s*", "", designation)
    cleaned = re.sub(r"\[[A-Z]\]", "", cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()

def calculate_confidence(table_data: List[List]) -> float:
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
