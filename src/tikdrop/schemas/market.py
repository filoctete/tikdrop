from typing import Optional

from pydantic import BaseModel, Field


class PortugalOpportunityInput(BaseModel):
    """PT Market Analyzer output for one product: how saturated/differentiated is the PT market."""

    pt_competitor_count: int = Field(ge=0, description="Number of relevant PT competitors/listings found")
    competitor_price_avg: Optional[float] = Field(default=None, ge=0, description="Average price charged by PT competitors")
    our_target_price: Optional[float] = Field(default=None, ge=0, description="Price we'd plan to sell at")
    differentiation_score: float = Field(ge=0, le=10, description="How differentiated our offer/angle can be, 0-10")
