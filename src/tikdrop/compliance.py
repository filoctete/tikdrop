"""Static risk flags from idea.pdf section 12 ("Categorias a evitar inicialmente"): plain
keyword matching, deterministic, no AI - a cheap first pass a human should still confirm before
trusting it (it will miss anything not in this list, and can false-positive on loose matches).
"""

import unicodedata
from typing import List, Tuple

from tikdrop.schemas.compliance import RiskComplianceInput

# Stems (not full words), matched with accents stripped, to catch Portuguese gender/number
# variants (e.g. "ortoped" matches ortopédico/ortopédica/ortopedia) without listing every
# inflection or accent variant.
_HIGH_RISK_CATEGORIES: List[Tuple[str, List[str]]] = [
    ("supplements", ["suplement", "supplement", "vitamin", "proteina", "protein powder"]),
    ("cosmetics", ["cosmet", "creme facial", "skincare", "serum"]),
    ("medical_device", ["dispositivo medic", "medical device", "ortoped", "terapeut", "therapeut"]),
    ("toys", ["brinquedo", "toy", "boneca", "doll"]),
    ("kids_products", ["bebe", "baby", "infantil", "kids", "crianc", "child"]),
    ("electronics_regulated", ["carregador", "charger", "bateria", "battery", "powerbank", "power bank"]),
]


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def suggest_risk_compliance(product_name: str) -> RiskComplianceInput:
    text = _strip_accents(product_name.lower())
    matched = [label for label, keywords in _HIGH_RISK_CATEGORIES if any(_strip_accents(k) in text for k in keywords)]

    if not matched:
        return RiskComplianceInput(category_risk_level="low")

    return RiskComplianceInput(
        category_risk_level="high",
        is_regulated_category=True,
        requires_technical_documentation="medical_device" in matched or "electronics_regulated" in matched,
    )
