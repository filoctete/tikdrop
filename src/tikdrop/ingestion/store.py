"""Persistence for trend signal snapshots and scored opportunities, via SQLAlchemy Core so the
same code works against local SQLite (default - one file, tikdrop.db, at the repo root, zero
setup) and a real hosted Postgres (set DATABASE_URL, e.g. a free Neon/Supabase instance) once
deploying the dashboard for real. development_guide.pdf section 6: keep origin + timestamp of
every signal, for audit and reprocessing.
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Sequence

from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, Table, Text, create_engine, inspect, insert, select, text, update
from sqlalchemy.engine import Engine

from tikdrop.schemas.score import ProductScoreInput, ProductScoreResult
from tikdrop.schemas.store import StoreCopy
from tikdrop.schemas.trend import RawSignal, TrendInput

DEFAULT_SQLITE_PATH = str(Path(__file__).resolve().parents[3] / "tikdrop.db")
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"

# A week only counts toward "sustained" if it had real average engagement, not just one row
# from a single quiet day - otherwise backfilled history would count every week regardless of
# whether the product actually showed up that week.
_SUSTAINED_WEEK_ENGAGEMENT_THRESHOLD = 0.15

_STATUS_BY_RECOMMENDATION = {"test": "queued_for_store", "watch": "watching", "reject": "rejected"}

metadata = MetaData()

trend_signal_snapshots = Table(
    "trend_signal_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("candidate_key", String, nullable=False),
    Column("source", String, nullable=False),
    Column("metric_value", Float, nullable=False),
    Column("engagement_proxy", Float, nullable=False),
    Column("raw_text", Text),
    Column("url", Text),
    Column("captured_at", DateTime, nullable=False),
)

opportunities = Table(
    "opportunities",
    metadata,
    Column("candidate_key", String, primary_key=True),
    Column("total_score", Float, nullable=False),
    Column("recommendation", String, nullable=False),
    Column("recommendation_reason", Text, nullable=False),
    Column("status", String, nullable=False),
    Column("scored_at", DateTime, nullable=False),
    Column("result_json", Text, nullable=False),
    Column("input_json", Text),
    Column("store_copy_json", Text),
)


def _naive_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _make_engine(db_path: Optional[str], database_url: Optional[str]) -> Engine:
    if database_url:
        url = database_url
    elif db_path:
        url = "sqlite://" if db_path == ":memory:" else f"sqlite:///{db_path}"
    else:
        url = os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL

    kwargs: dict = {}
    connect_args: dict = {}
    if url.startswith("sqlite") and (url == "sqlite://" or ":memory:" in url):
        # in-memory SQLite is connection-local by default - without a shared pool, every new
        # connection() call would see a *different*, empty database.
        from sqlalchemy.pool import StaticPool

        kwargs["poolclass"] = StaticPool
        connect_args["check_same_thread"] = False
    elif url.startswith("postgresql+psycopg"):
        # Supabase's free tier only routes direct connections over IPv6, which most simple
        # hosts (e.g. Render) can't reach - use its PgBouncer transaction-pooler instead. That
        # pooler doesn't keep server-side state across statements, so psycopg's own prepared
        # statement cache has to be disabled or queries intermittently fail.
        connect_args["prepare_threshold"] = None

    return create_engine(url, connect_args=connect_args, **kwargs)


def _ensure_new_columns(engine: Engine) -> None:
    # metadata.create_all() only creates tables that don't exist yet - it silently skips
    # adding new columns to a table that's already there (e.g. an existing hosted Postgres
    # database from before a column was added here). This is a deliberately minimal
    # poor-man's migration for that one case, not a general schema-migration system.
    inspector = inspect(engine)
    if "opportunities" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("opportunities")}
    missing = [c for c in ("input_json", "store_copy_json") if c not in existing]
    if not missing:
        return
    with engine.begin() as conn:
        for column in missing:
            conn.execute(text(f"ALTER TABLE opportunities ADD COLUMN {column} TEXT"))


class SignalStore:
    def __init__(self, db_path: Optional[str] = None, database_url: Optional[str] = None) -> None:
        self._engine = _make_engine(db_path, database_url)
        metadata.create_all(self._engine)
        _ensure_new_columns(self._engine)

    def save(self, candidate_key: str, signals: Sequence[RawSignal], captured_at: datetime = None) -> None:
        if not signals:
            return
        default_captured_at = captured_at or datetime.now(timezone.utc)
        rows = [
            dict(
                candidate_key=candidate_key,
                source=s.source,
                metric_value=s.metric_value,
                engagement_proxy=s.engagement_proxy,
                raw_text=s.raw_text,
                url=s.url,
                captured_at=_naive_utc(s.captured_at or default_captured_at),
            )
            for s in signals
        ]
        with self._engine.begin() as conn:
            conn.execute(insert(trend_signal_snapshots), rows)

    def build_trend_input(self, candidate_key: str, now: datetime = None) -> TrendInput:
        now = now or datetime.now(timezone.utc)
        naive_now = _naive_utc(now)
        window_start = naive_now - timedelta(days=7)
        prior_window_start = naive_now - timedelta(days=14)

        with self._engine.connect() as conn:
            all_rows = conn.execute(
                select(
                    trend_signal_snapshots.c.source,
                    trend_signal_snapshots.c.engagement_proxy,
                    trend_signal_snapshots.c.captured_at,
                ).where(trend_signal_snapshots.c.candidate_key == candidate_key)
            ).fetchall()

        recent = [r for r in all_rows if r.captured_at >= window_start]
        prior = [r for r in all_rows if prior_window_start <= r.captured_at < window_start]

        distinct_sources = len({r.source for r in recent})
        avg_engagement = (sum(r.engagement_proxy for r in recent) / len(recent)) if recent else 0.0

        # Computed in Python (not SQL) on purpose - keeps this portable across SQLite/Postgres
        # instead of relying on a dialect-specific date-bucketing function like strftime.
        weekly_engagement: dict = {}
        for r in all_rows:
            week_key = r.captured_at.isocalendar()[:2]  # (ISO year, ISO week)
            weekly_engagement.setdefault(week_key, []).append(r.engagement_proxy)
        weeks_sustained = sum(
            1
            for values in weekly_engagement.values()
            if (sum(values) / len(values)) >= _SUSTAINED_WEEK_ENGAGEMENT_THRESHOLD
        )

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
        values = dict(
            total_score=result.total_score,
            recommendation=result.recommendation,
            recommendation_reason=result.recommendation_reason,
            status=_STATUS_BY_RECOMMENDATION[result.recommendation],
            scored_at=_naive_utc(now),
            result_json=result.model_dump_json(),
            input_json=product_input.model_dump_json() if product_input else None,
        )

        with self._engine.begin() as conn:
            existing = conn.execute(
                select(opportunities.c.candidate_key).where(opportunities.c.candidate_key == candidate_key)
            ).fetchone()
            if existing:
                conn.execute(
                    update(opportunities).where(opportunities.c.candidate_key == candidate_key).values(**values)
                )
            else:
                conn.execute(insert(opportunities).values(candidate_key=candidate_key, **values))

    def list_opportunities(self, status: str = None) -> List[dict]:
        cols = [
            opportunities.c.candidate_key,
            opportunities.c.total_score,
            opportunities.c.recommendation,
            opportunities.c.recommendation_reason,
            opportunities.c.status,
            opportunities.c.scored_at,
        ]
        stmt = select(*cols).order_by(opportunities.c.total_score.desc())
        if status:
            stmt = stmt.where(opportunities.c.status == status)

        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().fetchall()

        return [
            {**dict(r), "scored_at": r["scored_at"].strftime("%Y-%m-%d %H:%M:%S")}
            for r in rows
        ]

    def get_opportunity_detail(self, candidate_key: str) -> Optional[ProductScoreResult]:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(opportunities.c.result_json).where(opportunities.c.candidate_key == candidate_key)
            ).fetchone()
        if row is None:
            return None
        return ProductScoreResult.model_validate_json(row[0])

    def get_candidate_input(self, candidate_key: str) -> Optional[ProductScoreInput]:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(opportunities.c.input_json).where(opportunities.c.candidate_key == candidate_key)
            ).fetchone()
        if row is None or row[0] is None:
            return None
        return ProductScoreInput.model_validate_json(row[0])

    def save_store_copy(self, candidate_key: str, copy: StoreCopy) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                update(opportunities)
                .where(opportunities.c.candidate_key == candidate_key)
                .values(store_copy_json=copy.model_dump_json())
            )

    def get_store_copy(self, candidate_key: str) -> Optional[StoreCopy]:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(opportunities.c.store_copy_json).where(opportunities.c.candidate_key == candidate_key)
            ).fetchone()
        if row is None or row[0] is None:
            return None
        return StoreCopy.model_validate_json(row[0])

    def close(self) -> None:
        self._engine.dispose()

    def __enter__(self) -> "SignalStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
