from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ThemeOut, ThemeTrend, TrendPoint
from app.services.analytics import get_all_themes_with_counts, get_theme_trend

router = APIRouter(prefix="/themes", tags=["themes"])

RECENTLY_DISCOVERED_WINDOW_DAYS = 7


@router.get("", response_model=list[ThemeOut])
def list_themes(db: Session = Depends(get_db)):
    themes = get_all_themes_with_counts(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=RECENTLY_DISCOVERED_WINDOW_DAYS)

    result = []
    for t in themes:
        created = t.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        result.append(
            ThemeOut(
                id=t.id,
                label=t.label,
                summary=t.summary,
                entry_count=t.entry_count,
                created_at=t.created_at,
                is_recently_discovered=created >= cutoff,
            )
        )
    return result


@router.get("/{theme_id}/trend", response_model=ThemeTrend)
def theme_trend(
    theme_id: int,
    granularity: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    db: Session = Depends(get_db),
):
    from app.models import Theme

    theme = db.get(Theme, theme_id)
    points = get_theme_trend(db, theme_id, granularity)

    return ThemeTrend(
        theme_id=theme_id,
        label=theme.label if theme else "e panjohur",
        granularity=granularity,
        points=[TrendPoint(period_start=p[0], count=p[1]) for p in points],
    )