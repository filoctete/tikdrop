from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RawSignal(BaseModel):
    """One raw observation from a Trend Hunter connector (development_guide.pdf section 6):
    always keep the source and enough context to audit/reprocess later."""

    source: str  # e.g. "google_trends", "reddit"
    metric_value: float  # source-specific raw metric (search interest, upvotes+comments, ...)
    engagement_proxy: float = Field(ge=0, le=1, description="Normalized 0-1 engagement proxy")
    raw_text: Optional[str] = None
    url: Optional[str] = None
    captured_at: Optional[datetime] = None  # when this data point actually happened, if known
    # (e.g. a historical day from Google Trends) - falls back to "now" if left unset


class TrendInput(BaseModel):
    """Aggregated TrendSignal data for one product, over two consecutive 7-day windows."""

    signal_count_7d: int = Field(ge=0, description="Distinct trend signals/mentions in the last 7 days")
    signal_count_prior_7d: int = Field(ge=0, description="Same count for the 7 days before that")
    avg_engagement_rate: float = Field(ge=0, le=1, description="Average engagement / views across signals, 0-1")
    distinct_sources: int = Field(ge=0, le=4, description="How many of TikTok/Instagram/Reddit/Google Trends show the signal")
    weeks_sustained: int = Field(ge=0, description="Consecutive weeks the product has shown signal, not just a spike")
