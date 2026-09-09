from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import FeedbackEntry, Theme


def semantic_search(
    db: Session,
    query_embedding: list[float],
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    top_k: int = 8,
) -> list[FeedbackEntry]:
    q = db.query(FeedbackEntry)

    if date_from is not None:
        q = q.filter(FeedbackEntry.feedback_at >= date_from)
    if date_to is not None:
        q = q.filter(FeedbackEntry.feedback_at <= date_to)

    q = q.order_by(FeedbackEntry.embedding.cosine_distance(query_embedding)).limit(top_k)

    return q.all()


_GRANULARITY_TO_SQL = {
    "daily": "day",
    "weekly": "week",
    "monthly": "month",
}


def get_theme_trend(db: Session, theme_id: int, granularity: str) -> list[tuple[datetime, int]]:
    unit = _GRANULARITY_TO_SQL.get(granularity, "day")

    bucket = func.date_trunc(unit, FeedbackEntry.feedback_at).label("bucket")

    rows = (
        db.query(bucket, func.count(FeedbackEntry.id))
        .filter(FeedbackEntry.theme_id == theme_id)
        .group_by(bucket)
        .order_by(bucket)
        .all()
    )
    return [(row[0], row[1]) for row in rows]


def get_all_themes_with_counts(db: Session) -> list[Theme]:
    return db.query(Theme).order_by(Theme.entry_count.desc()).all()