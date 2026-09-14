"""Local SQLite store for trend signal snapshots. Kept deliberately simple (one file,
tikdrop.db, at the repo root) - it exists so growth can be measured across repeated runs
(development_guide.pdf section 6: keep origin + timestamp of every signal, for audit and
reprocessing) without needing Postgres/an API yet.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Sequence

from tikdrop.schemas.score import ProductScoreInput, ProductScoreResult
from tikdrop.schemas.trend import RawSignal, TrendInput

DEFAULT_DB_PATH = str(Path(__file__).resolve().parents[3] / "tikdrop.db")

# A week only counts toward "sustained" if it had real average engagement, not just one row
# from a single quiet day - otherwise backfilled history would count every week regardless of
# whether the product actually showed up that week.
_SUSTAINED_WEEK_ENGAGEMENT_THRESHOLD = 0.15

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trend_signal_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_key TEXT NOT NULL,
    source TEXT NOT NULL,
    metric_value REAL NOT NULL,
    engagement_proxy REAL NOT NULL,
    raw_text TEXT,
    url TEXT,
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS opportunities (
    candidate_key TEXT PRIMARY KEY,
    total_score REAL NOT NULL,
    recommendation TEXT NOT NULL,
    recommendation_reason TEXT NOT NULL,
    status TEXT NOT NULL,
    scored_at TEXT NOT NULL,
    result_json TEXT NOT NULL,
    input_json TEXT
);
"""


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class SignalStore:
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def save(self, candidate_key: str, signals: Sequence[RawSignal], captured_at: datetime = None) -> None:
        default_captured_at = captured_at or datetime.now(timezone.utc)
        rows = [
            (
                candidate_key,
                s.source,
                s.metric_value,
                s.engagement_proxy,
                s.raw_text,
                s.url,
                _fmt(s.captured_at or default_captured_at),
            )
            for s in signals
        ]
        self._conn.executemany(
            "INSERT INTO trend_signal_snapshots "
            "(candidate_key, source, metric_value, engagement_proxy, raw_text, url, captured_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        self._conn.commit()

    def build_trend_input(self, candidate_key: str, now: datetime = None) -> TrendInput:
        now = now or datetime.now(timezone.utc)
        window_start = _fmt(now - timedelta(days=7))
        prior_window_start = _fmt(now - timedelta(days=14))

        cur = self._conn.execute(
            "SELECT source, engagement_proxy, captured_at FROM trend_signal_snapshots "
            "WHERE candidate_key = ? AND captured_at >= ?",
            (candidate_key, prior_window_start),
        )
        rows = cur.fetchall()

        recent = [r for r in rows if r[2] >= window_start]
        prior = [r for r in rows if r[2] < window_start]

        distinct_sources = len({r[0] for r in recent})
        avg_engagement = (sum(r[1] for r in recent) / len(recent)) if recent else 0.0

        cur = self._conn.execute(
            "SELECT strftime('%Y-%W', captured_at) AS wk, AVG(engagement_proxy) AS avg_eng "
            "FROM trend_signal_snapshots WHERE candidate_key = ? "
            "GROUP BY wk HAVING avg_eng >= ?",
            (candidate_key, _SUSTAINED_WEEK_ENGAGEMENT_THRESHOLD),
        )
        weeks_sustained = len(cur.fetchall())

        return TrendInput(
            signal_count_7d=len(recent),
            signal_count_prior_7d=len(prior),
            avg_engagement_rate=min(avg_engagement, 1.0),
            distinct_sources=min(distinct_sources, 4),
            weeks_sustained=weeks_sustained,
        )

    def save_score_result(
        self,
        candidate_key: str,
        result: ProductScoreResult,
        product_input: Optional[ProductScoreInput] = None,
        now: datetime = None,
    ) -> None:
        now = now or datetime.now(timezone.utc)
        status = {"test": "queued_for_store", "watch": "watching", "reject": "rejected"}[result.recommendation]
        self._conn.execute(
            "INSERT INTO opportunities "
            "(candidate_key, total_score, recommendation, recommendation_reason, status, scored_at, result_json, input_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(candidate_key) DO UPDATE SET "
            "total_score=excluded.total_score, recommendation=excluded.recommendation, "
            "recommendation_reason=excluded.recommendation_reason, status=excluded.status, "
            "scored_at=excluded.scored_at, result_json=excluded.result_json, input_json=excluded.input_json",
            (
                candidate_key,
                result.total_score,
                result.recommendation,
                result.recommendation_reason,
                status,
                _fmt(now),
                result.model_dump_json(),
                product_input.model_dump_json() if product_input else None,
            ),
        )
        self._conn.commit()

    def list_opportunities(self, status: str = None) -> List[dict]:
        if status:
            cur = self._conn.execute(
                "SELECT candidate_key, total_score, recommendation, recommendation_reason, status, scored_at "
                "FROM opportunities WHERE status = ? ORDER BY total_score DESC",
                (status,),
            )
        else:
            cur = self._conn.execute(
                "SELECT candidate_key, total_score, recommendation, recommendation_reason, status, scored_at "
                "FROM opportunities ORDER BY total_score DESC"
            )
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_opportunity_detail(self, candidate_key: str) -> Optional[ProductScoreResult]:
        cur = self._conn.execute(
            "SELECT result_json FROM opportunities WHERE candidate_key = ?", (candidate_key,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        return ProductScoreResult.model_validate_json(row[0])

    def get_candidate_input(self, candidate_key: str) -> Optional[ProductScoreInput]:
        cur = self._conn.execute(
            "SELECT input_json FROM opportunities WHERE candidate_key = ?", (candidate_key,)
        )
        row = cur.fetchone()
        if row is None or row[0] is None:
            return None
        return ProductScoreInput.model_validate_json(row[0])

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SignalStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
