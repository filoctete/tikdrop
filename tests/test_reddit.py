import pytest

from tikdrop.ingestion.reddit import RedditConnectorError, fetch_reddit_signals


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_missing_credentials_raises(monkeypatch):
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)

    with pytest.raises(RedditConnectorError):
        fetch_reddit_signals("pet hair roller")


def test_fetch_reddit_signals_parses_posts(monkeypatch):
    def fake_post(url, data, auth, headers, timeout):
        return _FakeResponse(200, {"access_token": "tok123"})

    def fake_get(url, params, headers, timeout):
        assert headers["Authorization"] == "Bearer tok123"
        return _FakeResponse(
            200,
            {
                "data": {
                    "children": [
                        {
                            "data": {
                                "score": 120,
                                "num_comments": 30,
                                "upvote_ratio": 0.92,
                                "title": "This roller is amazing",
                                "permalink": "/r/test/comments/abc",
                            }
                        }
                    ]
                }
            },
        )

    monkeypatch.setattr("tikdrop.ingestion.reddit.httpx.post", fake_post)
    monkeypatch.setattr("tikdrop.ingestion.reddit.httpx.get", fake_get)

    signals = fetch_reddit_signals("pet hair roller", client_id="id", client_secret="secret")

    assert len(signals) == 1
    signal = signals[0]
    assert signal.source == "reddit"
    assert signal.metric_value == 150  # score + num_comments
    assert signal.engagement_proxy == 0.92
    assert signal.raw_text == "This roller is amazing"
    assert signal.url == "https://reddit.com/r/test/comments/abc"


def test_fetch_reddit_signals_defaults_missing_upvote_ratio(monkeypatch):
    def fake_post(url, data, auth, headers, timeout):
        return _FakeResponse(200, {"access_token": "tok123"})

    def fake_get(url, params, headers, timeout):
        return _FakeResponse(
            200,
            {"data": {"children": [{"data": {"title": "no ratio here", "permalink": "/r/x"}}]}},
        )

    monkeypatch.setattr("tikdrop.ingestion.reddit.httpx.post", fake_post)
    monkeypatch.setattr("tikdrop.ingestion.reddit.httpx.get", fake_get)

    signals = fetch_reddit_signals("widget", client_id="id", client_secret="secret")

    assert signals[0].engagement_proxy == 0.5
    assert signals[0].metric_value == 0


def test_auth_failure_raises_connector_error(monkeypatch):
    def fake_post(url, data, auth, headers, timeout):
        return _FakeResponse(401, text="invalid credentials")

    monkeypatch.setattr("tikdrop.ingestion.reddit.httpx.post", fake_post)

    with pytest.raises(RedditConnectorError):
        fetch_reddit_signals("widget", client_id="bad", client_secret="bad")
