from typing import Literal

from pydantic import BaseModel, Field

SizeCategory = Literal["small", "medium", "large"]


class LogisticsInput(BaseModel):
    weight_grams: float = Field(gt=0)
    fragile: bool = False
    avg_shipping_days: float = Field(gt=0)
    size_category: SizeCategory = "small"
