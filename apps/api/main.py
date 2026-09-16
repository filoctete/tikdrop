"""FastAPI backend for the TikDrop Admin Dashboard (development_guide.pdf section 4/15).

This is the "internal decision platform" only - product/opportunity management, no customer
checkout or payments (per section 23: use an existing platform for that, don't build it here).

Run locally: uvicorn apps.api.main:app --reload --app-dir D:/TikDrop
"""

import os
from pathlib import Path
from typing import Generator, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from tikdrop.ai import StubAIProvider
from tikdrop.ai.provider import AIProvider
from tikdrop.ingestion import SignalStore, ViesError, check_vat, fetch_google_trends_signal
from tikdrop.schemas.score import ProductScoreInput, ProductScoreResult
from tikdrop.scoring import ProductScoringEngine, build_quick_score_input


def _load_dotenv_if_present() -> None:
    # Local dev convenience only - deployed platforms (Render, etc.) set real env vars, so this
    # is a no-op there since no .env file exists in that environment.
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv_if_present()

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


class StoreProductSummary(BaseModel):
    candidate_key: str
    title: str
    sale_price: float


class StoreProductDetail(BaseModel):
    candidate_key: str
    title: str
    tagline: str
    description: str
    benefits: List[str]
    sale_price: float


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


def _get_ai_provider() -> AIProvider:
    if os.environ.get("GROQ_API_KEY"):
        from tikdrop.ai.groq_provider import GroqAIProvider

        return GroqAIProvider()
    return StubAIProvider()


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
    store.mark_discovered_candidate_completed(req.name)
    return result


class DiscoveredCandidate(BaseModel):
    candidate_key: str
    discovered_at: str
    trend_days: int
    weeks_sustained: int
    research_links: List[dict]
    status: str


class DiscoveryRunResult(BaseModel):
    discovered: List[str]


@app.get("/discovery/candidates", response_model=List[DiscoveredCandidate])
def list_discovered_candidates(status: str = "needs_input", store: SignalStore = Depends(get_store)):
    return store.list_discovered_candidates(status=status)


@app.post("/discovery/run", response_model=DiscoveryRunResult)
def run_discovery(store: SignalStore = Depends(get_store)):
    """Hourly-cron entry point (see .github/workflows/discover.yml) - finds real, evidence-backed
    trend candidates and queues them for a human to add cost/price/weight. Never auto-scores or
    auto-publishes anything (see tikdrop/discovery.py docstring for why).
    """
    from tikdrop.discovery import discover_candidates

    discovered = discover_candidates(store)
    return DiscoveryRunResult(discovered=discovered)


@app.post("/suppliers/vat-check")
def vat_check(req: VatCheckRequest):
    try:
        return check_vat(req.country_code, req.vat_number)
    except ViesError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# --- Public storefront (development_guide.pdf section 12, Store Generator) ---
# Read-only product presentation only - no checkout/payments here, see apps/web/src/app/store.


@app.get("/store/products", response_model=List[StoreProductSummary])
def list_store_products(store: SignalStore = Depends(get_store)):
    items = []
    for o in store.list_opportunities(status="queued_for_store"):
        key = o["candidate_key"]
        candidate_input = store.get_candidate_input(key)
        if candidate_input is None:
            continue
        copy = store.get_store_copy(key)
        title = copy.title if copy else key.title()
        items.append(StoreProductSummary(candidate_key=key, title=title, sale_price=candidate_input.costs.sale_price))
    return items


@app.get("/store/products/{candidate_key}", response_model=StoreProductDetail)
def get_store_product(candidate_key: str, store: SignalStore = Depends(get_store)):
    candidate_input = store.get_candidate_input(candidate_key)
    opportunity = store.get_opportunity_detail(candidate_key)
    if candidate_input is None or opportunity is None or opportunity.recommendation != "test":
        raise HTTPException(status_code=404, detail="Product not found")

    copy = store.get_store_copy(candidate_key)
    if copy is None:
        ai = _get_ai_provider()
        try:
            copy = ai.generate_store_copy(candidate_key)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Could not generate store copy: {exc}")
        finally:
            close = getattr(ai, "close", None)
            if close:
                close()
        store.save_store_copy(candidate_key, copy)

    return StoreProductDetail(
        candidate_key=candidate_key,
        title=copy.title,
        tagline=copy.tagline,
        description=copy.description,
        benefits=copy.benefits,
        sale_price=candidate_input.costs.sale_price,
    )


@app.post("/store/products/{candidate_key}/checkout", response_model=CheckoutSessionResponse)
def create_checkout_session(candidate_key: str, store: SignalStore = Depends(get_store)):
    """Creates a Stripe-hosted Checkout Session and returns its URL. Card data goes straight to
    Stripe's own page - it never touches this server (per development_guide.pdf section 23:
    don't build checkout from scratch; this keeps us out of PCI-DSS scope almost entirely).
    """
    stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payments are not configured yet (STRIPE_SECRET_KEY missing).")

    candidate_input = store.get_candidate_input(candidate_key)
    opportunity = store.get_opportunity_detail(candidate_key)
    if candidate_input is None or opportunity is None or opportunity.recommendation != "test":
        raise HTTPException(status_code=404, detail="Product not found")

    copy = store.get_store_copy(candidate_key)
    title = copy.title if copy else candidate_key.title()

    import stripe

    stripe.api_key = stripe_secret_key
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "unit_amount": round(candidate_input.costs.sale_price * 100),
                        "product_data": {"name": title},
                    },
                    "quantity": 1,
                }
            ],
            success_url=f"{frontend_url}/store/{candidate_key}?success=true",
            cancel_url=f"{frontend_url}/store/{candidate_key}?canceled=true",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not start checkout: {exc}")

    return CheckoutSessionResponse(checkout_url=session.url)
