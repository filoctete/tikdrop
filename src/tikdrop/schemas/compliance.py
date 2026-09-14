from typing import Literal

from pydantic import BaseModel

RiskLevel = Literal["low", "medium", "high"]


class RiskComplianceInput(BaseModel):
    """See idea.pdf section 12 for the categories this is meant to flag (supplements, cosmetics,
    medical devices, toys/childrens' products, some electronics, etc.)."""

    category_risk_level: RiskLevel = "low"
    requires_technical_documentation: bool = False
    is_regulated_category: bool = False
