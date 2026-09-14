from pydantic import BaseModel, Field


class CostInputs(BaseModel):
    """Per-unit economics inputs, matching the formula in development_guide.pdf section 9."""

    sale_price: float = Field(gt=0)
    product_cost: float = Field(ge=0)
    shipping_cost: float = Field(ge=0)
    payment_fees: float = Field(ge=0, description="Payment processor / platform fees per unit")
    ad_cost_per_unit: float = Field(ge=0, description="CAC allocated to this unit")
    returns_cost_estimate: float = Field(ge=0, description="Expected returns/defects cost, amortized per unit")
    other_costs: float = Field(default=0, ge=0, description="Taxes, customs, or other applicable costs")


class MarginResult(BaseModel):
    gross_margin: float
    contribution_margin: float
    contribution_margin_pct: float
    net_contribution: float
    net_contribution_pct: float
    is_viable: bool
