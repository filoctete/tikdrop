import pytest

from tikdrop.ingestion.vies import ViesError, check_vat


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def test_check_vat_parses_a_valid_result(monkeypatch):
    monkeypatch.setattr(
        "tikdrop.ingestion.vies.httpx.post",
        lambda url, json, timeout: _FakeResponse(
            200,
            {
                "countryCode": "PT",
                "vatNumber": "123456789",
                "valid": True,
                "name": "ACME LDA",
                "address": "Rua Exemplo 1",
                "requestDate": "2026-09-15",
            },
        ),
    )

    result = check_vat("pt", "123 456 789")

    assert result.valid is True
    assert result.name == "ACME LDA"
    assert result.country_code == "PT"


def test_check_vat_parses_an_invalid_result(monkeypatch):
    monkeypatch.setattr(
        "tikdrop.ingestion.vies.httpx.post",
        lambda url, json, timeout: _FakeResponse(
            200, {"countryCode": "PT", "vatNumber": "000000000", "valid": False}
        ),
    )

    result = check_vat("PT", "000000000")

    assert result.valid is False
    assert result.name is None


def test_check_vat_treats_placeholder_dashes_as_no_data(monkeypatch):
    monkeypatch.setattr(
        "tikdrop.ingestion.vies.httpx.post",
        lambda url, json, timeout: _FakeResponse(
            200, {"countryCode": "PT", "vatNumber": "123456789", "valid": True, "name": "---", "address": "---"}
        ),
    )

    result = check_vat("PT", "123456789")

    assert result.valid is True
    assert result.name is None
    assert result.address is None


def test_check_vat_raises_on_service_error(monkeypatch):
    monkeypatch.setattr(
        "tikdrop.ingestion.vies.httpx.post",
        lambda url, json, timeout: _FakeResponse(503, text="Service unavailable"),
    )

    with pytest.raises(ViesError):
        check_vat("PT", "123456789")


def test_check_vat_strips_leading_country_prefix(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured.update(json)
        return _FakeResponse(200, {"countryCode": "PT", "vatNumber": "123456789", "valid": True})

    monkeypatch.setattr("tikdrop.ingestion.vies.httpx.post", fake_post)

    check_vat("PT", "PT123456789")

    assert captured["vatNumber"] == "123456789"


def test_check_vat_strips_prefix_regardless_of_case(monkeypatch):
    # regression: country_code lowercase + vat_number prefixed uppercase used to fail to strip,
    # because the old code replaced using the raw (lowercase) country_code instead of the
    # normalized uppercase one.
    captured = {}

    def fake_post(url, json, timeout):
        captured.update(json)
        return _FakeResponse(200, {"countryCode": "PT", "vatNumber": "123456789", "valid": True})

    monkeypatch.setattr("tikdrop.ingestion.vies.httpx.post", fake_post)

    check_vat("pt", "PT123456789")

    assert captured["vatNumber"] == "123456789"
    assert captured["countryCode"] == "PT"
