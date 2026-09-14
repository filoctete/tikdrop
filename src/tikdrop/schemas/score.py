from typing import Dict, Literal

from pydantic import BaseModel

from tikdrop.schemas.compliance import RiskComplianceInput
from tikdrop.schemas.creative import CreativeInput
from tikdrop.schemas.logistics import LogisticsInput
from tikdrop.schemas.market import PortugalOpportunityInput
from tikdrop.schemas.profit import CostInputs
from tikdrop.schemas.supplier import SupplierInput
from tikdrop.schemas.trend import TrendInput

Recommendation = Literal["test", "watch", "reject"]


class ProductScoreInput(BaseModel):
    """Everything the ProductScoringEngine needs for one product candidate."""

    product_name: str
    trend: TrendInput
    portugal_opportunity: PortugalOpportunityInput
    costs: CostInputs
    supplier: SupplierInput
    creative: CreativeInput
    logistics: LogisticsInput
    risk_compliance: RiskComplianceInput


class DimensionScore(BaseModel):
    raw_score: float  # 0-10, before weighting
    weight: float  # 0-1
    weighted_contribution: float  # raw_score * weight


class ProductScoreResult(BaseModel):
    product_name: str
    dimensions: Dict[str, DimensionScore]
    total_score: float  # 0-10
    recommendation: Recommendation
    recommendation_reason: str
