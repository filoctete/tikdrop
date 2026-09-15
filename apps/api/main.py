"""FastAPI backend for the TikDrop Admin Dashboard (development_guide.pdf section 4/15).

This is the "internal decision platform" only - product/opportunity management, no customer
checkout or payments (per section 23: use an existing platform for that, don't build it here).

Run locally: uvicorn apps.api.main:app --reload --app-dir D:/TikDrop
"""

import os
from typing import Generator, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from tikdrop.ingestion import SignalStore, ViesError, check_vat, fetch_google_trends_signal
from tikdrop.schemas.score import ProductScoreInput, ProductScoreResult
from tikdrop.scoring import ProductScoringEngine, build_quick_score_input

app = FastAPI(title="TikDrop Admin API", version="0.1.0")

_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_store() -> Generator[SignalStore, None, None]:
    store = SignalStore()
    try:
        yield store
    finally:
        store.close()


class OpportunitySummary(BaseModel):
    candidate_key: str
    total_score: float
    recommendation: str
    recommendation_reason: str
    status: str
    scored_at: str


class OpportunityDetail(BaseModel):
    result: ProductScoreResult
    input: Optional[ProductScoreInput] = None


class QuickScoreRequest(BaseModel):
    name: str
    product_cost: float = Field(gt=0)
    sale_price: float = Field(gt=0)
    weight_grams: float = Field(gt=0)
    demo_video_feasibility: float = Field(default=5.0, ge=0, le=10)
    ugc_potential: float = Field(default=5.0, ge=0, le=10)
    avg_shipping_days: float = Field(default=10.0, gt=0)


class VatCheckRequest(BaseModel):
    country_code: str
    vat_number: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/opportunities", response_model=List[OpportunitySummary])
def list_opportunities(status: Optional[str] = None, store: SignalStore = Depends(get_store)):
    return store.list_opportunities(status=status)


@app.get("/opportunities/{candidate_key}", response_model=OpportunityDetail)
def get_opportunity(candidate_key: str, store: SignalStore = Depends(get_store)):
    result = store.get_opportunity_detail(candidate_key)
    if result is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return OpportunityDetail(result=result, input=store.get_candidate_input(candidate_key))


@app.post("/opportunities/quick-score", response_model=ProductScoreResult)
def quick_score(req: QuickScoreRequest, store: SignalStore = Depends(get_store)):
    """Real worldwide Google Trends + a quick placeholder-based score, matching
    examples/batch_score.py. PT competition/differentiation stay neutral placeholders until a
    human confirms them - re-run examples/discover.py for a fully manual pass on this candidate.
    """
    try:
        signals = fetch_google_trends_signal(req.name, geo="")
    except Exception:
        signals = []

    if signals:
        store.save(req.name, signals)
    trend_input = store.build_trend_input(req.name)

    product_input = build_quick_score_input(
        name=req.name,
        trend_input=trend_input,
        product_cost=req.product_cost,
        sale_price=req.sale_price,
        weight_grams=req.weight_grams,
        demo_video_feasibility=req.demo_video_feasibility,
        ugc_potential=req.ugc_potential,
        avg_shipping_days=req.avg_shipping_days,
    )

    result = ProductScoringEngine.score(product_input)
    store.save_score_result(req.name, result, product_input=product_input)
    return result


@app.post("/suppliers/vat-check")
def vat_check(req: VatCheckRequest):
    try:
        return check_vat(req.country_code, req.vat_number)
    except ViesError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
