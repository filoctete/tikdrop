import pytest

fastapi_testclient = pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from apps.api.main import app, get_store
from tikdrop.ingestion.store import SignalStore
from tikdrop.schemas.score import DimensionScore, ProductScoreResult


@pytest.fixture
def client(tmp_path):
    # A real (temp) file, not ":memory:" - an in-memory SQLite DB is connection-local, so a
    # fresh ":memory:" per request would silently lose state between requests within one test.
    db_path = str(tmp_path / "test.db")

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


def test_vat_check_endpoint(monkeypatch):
    def fake_check_vat(country_code, vat_number):
        from tikdrop.schemas.vat import VatCheckResult
        return VatCheckResult(country_code="PT", vat_number="123456789", valid=True)

    monkeypatch.setattr("apps.api.main.check_vat", fake_check_vat)

    with TestClient(app) as client:
        response = client.post("/suppliers/vat-check", json={"country_code": "PT", "vat_number": "123456789"})

    assert response.status_code == 200
    assert response.json()["valid"] is True
