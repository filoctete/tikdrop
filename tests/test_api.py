import pytest

fastapi_testclient = pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from apps.api.main import app, get_store
from tikdrop.ingestion.store import SignalStore
from tikdrop.schemas.score import DimensionScore, ProductScoreResult


@pytest.fixture
def db_path(tmp_path):
    # A real (temp) file, not ":memory:" - an in-memory SQLite DB is connection-local, so a
    # fresh ":memory:" per request would silently lose state between requests within one test.
    return str(tmp_path / "test.db")


@pytest.fixture
def client(db_path):
    def _override_store():
        store = SignalStore(db_path=db_path)
        try:
            yield store
        finally:
            store.close()

    app.dependency_overrides[get_store] = _override_store
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_opportunities_empty(client):
    response = client.get("/opportunities")
    assert response.status_code == 200
    assert response.json() == []


def test_get_opportunity_not_found(client):
    response = client.get("/opportunities/does-not-exist")
    assert response.status_code == 404


def test_quick_score_creates_and_lists_an_opportunity(client, monkeypatch):
    monkeypatch.setattr("apps.api.main.fetch_google_trends_signal", lambda name, geo="": [])

    response = client.post(
        "/opportunities/quick-score",
        json={"name": "test widget", "product_cost": 5.0, "sale_price": 20.0, "weight_grams": 100},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["product_name"] == "test widget"
    assert "total_score" in body

    listed = client.get("/opportunities").json()
    assert len(listed) == 1
    assert listed[0]["candidate_key"] == "test widget"

    detail = client.get("/opportunities/test widget").json()
    assert detail["result"]["product_name"] == "test widget"
    assert detail["input"]["costs"]["sale_price"] == 20.0


def _seed_queued_for_store(db_path, candidate_key, sale_price=20.0):
    from tikdrop.schemas.score import ProductScoreInput
    from tikdrop.schemas.compliance import RiskComplianceInput
    from tikdrop.schemas.creative import CreativeInput
    from tikdrop.schemas.logistics import LogisticsInput
    from tikdrop.schemas.market import PortugalOpportunityInput
    from tikdrop.schemas.profit import CostInputs
    from tikdrop.schemas.supplier import SupplierInput
    from tikdrop.schemas.trend import TrendInput

    store = SignalStore(db_path=db_path)
    product_input = ProductScoreInput(
        product_name=candidate_key,
        trend=TrendInput(signal_count_7d=1, signal_count_prior_7d=0, avg_engagement_rate=0.5, distinct_sources=1, weeks_sustained=1),
        portugal_opportunity=PortugalOpportunityInput(pt_competitor_count=1, differentiation_score=8.0),
        costs=CostInputs(sale_price=sale_price, product_cost=2.0, shipping_cost=1.0, payment_fees=0.5, ad_cost_per_unit=2.0, returns_cost_estimate=0.5),
        supplier=SupplierInput(),
        creative=CreativeInput(demo_video_feasibility=8, ugc_potential=8),
        logistics=LogisticsInput(weight_grams=100, avg_shipping_days=5),
        risk_compliance=RiskComplianceInput(),
    )
    result = ProductScoreResult(
        product_name=candidate_key,
        dimensions={"trend": DimensionScore(raw_score=9, weight=0.2, weighted_contribution=1.8)},
        total_score=8.5,
        recommendation="test",
        recommendation_reason="strong candidate",
    )
    store.save_score_result(candidate_key, result, product_input=product_input)
    store.close()


def test_store_products_lists_only_queued_for_store(client, db_path, monkeypatch):
    monkeypatch.setattr("apps.api.main.fetch_google_trends_signal", lambda name, geo="": [])
    _seed_queued_for_store(db_path, "widget", sale_price=25.0)

    # a rejected candidate should not show up in the public store
    client.post(
        "/opportunities/quick-score",
        json={"name": "bad widget", "product_cost": 100.0, "sale_price": 10.0, "weight_grams": 5000},
    )

    response = client.get("/store/products")

    assert response.status_code == 200
    keys = [p["candidate_key"] for p in response.json()]
    assert "widget" in keys
    assert "bad widget" not in keys


def test_store_product_detail_generates_and_caches_copy(client, db_path, monkeypatch):
    from tikdrop.schemas.store import StoreCopy

    _seed_queued_for_store(db_path, "widget", sale_price=25.0)

    calls = []

    class FakeAI:
        def generate_store_copy(self, product_name):
            calls.append(product_name)
            return StoreCopy(title="Widget", tagline="Great", description="A widget.", benefits=["Fast"])

    monkeypatch.setattr("apps.api.main._get_ai_provider", lambda: FakeAI())

    first = client.get("/store/products/widget")
    assert first.status_code == 200
    assert first.json()["title"] == "Widget"
    assert first.json()["sale_price"] == 25.0
    assert len(calls) == 1

    # second call should use the cached copy, not call the AI again
    second = client.get("/store/products/widget")
    assert second.status_code == 200
    assert len(calls) == 1


def test_store_product_detail_404_for_unknown_or_unqueued(client, db_path):
    _seed_queued_for_store(db_path, "widget")

    response = client.get("/store/products/does-not-exist")
    assert response.status_code == 404


def test_checkout_requires_stripe_key(client, db_path, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    _seed_queued_for_store(db_path, "widget", sale_price=25.0)

    response = client.post("/store/products/widget/checkout")

    assert response.status_code == 503


def test_checkout_creates_stripe_session(client, db_path, monkeypatch):
    stripe = pytest.importorskip("stripe")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    _seed_queued_for_store(db_path, "widget", sale_price=25.0)

    class FakeSession:
        url = "https://checkout.stripe.com/fake-session"

    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return FakeSession()

    monkeypatch.setattr(stripe.checkout.Session, "create", fake_create)

    response = client.post("/store/products/widget/checkout")

    assert response.status_code == 200
    assert response.json()["checkout_url"] == "https://checkout.stripe.com/fake-session"
    assert captured["line_items"][0]["price_data"]["unit_amount"] == 2500  # 25.00 EUR in cents


def test_checkout_404_for_unqueued_product(client, db_path, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")

    response = client.post("/store/products/does-not-exist/checkout")

    assert response.status_code == 404


def test_vat_check_endpoint(monkeypatch):
    def fake_check_vat(country_code, vat_number):
        from tikdrop.schemas.vat import VatCheckResult
        return VatCheckResult(country_code="PT", vat_number="123456789", valid=True)

    monkeypatch.setattr("apps.api.main.check_vat", fake_check_vat)

    with TestClient(app) as client:
        response = client.post("/suppliers/vat-check", json={"country_code": "PT", "vat_number": "123456789"})

    assert response.status_code == 200
    assert response.json()["valid"] is True
