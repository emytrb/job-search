import re
from typing import Optional


def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def extract_salary_range(text: str) -> tuple[Optional[int], Optional[int], Optional[str]]:
    currency = "GBP" if "£" in text else "EUR" if "€" in text else "USD"

    cleaned = text.replace(",", "").replace("K", "000").replace("k", "000")

    patterns = [
        r"(\d+)\s*(?:-|to)\s*(\d+)",
        r"(\d+)\+",
        r"up\s+to\s+(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return int(groups[0]), int(groups[1]), currency
            elif len(groups) == 1:
                return int(groups[0]), None, currency

    return None, None, None


def normalize_location(location: Optional[str]) -> Optional[str]:
    if not location:
        return None

    location = location.strip()

    replacements = {
        "United Kingdom": "UK",
        "Greater London": "London",
        "Central London": "London",
        "City of London": "London",
    }

    for old, new in replacements.items():
        location = location.replace(old, new)

    return location
