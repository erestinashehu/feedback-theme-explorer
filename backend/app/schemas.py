from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FeedbackIn(BaseModel):
    content: str = Field(..., min_length=1)
    feedback_at: datetime


class BulkFeedbackIn(BaseModel):
    entries: list[FeedbackIn]


class FeedbackOut(BaseModel):
    id: int
    content: str
    feedback_at: datetime
    theme_id: Optional[int]
    theme_label: Optional[str] = None

    class Config:
        from_attributes = True


class IngestResult(BaseModel):
    created: int
    assigned_to_existing_theme: int
    sent_to_pool: int
    newly_discovered_themes: list[str]


class ThemeOut(BaseModel):
    id: int
    label: str
    summary: Optional[str]
    entry_count: int
    created_at: datetime
    is_recently_discovered: bool = False

    class Config:
        from_attributes = True


class TrendPoint(BaseModel):
    period_start: datetime
    count: int


class ThemeTrend(BaseModel):
    theme_id: int
    label: str
    granularity: str
    points: list[TrendPoint]


class QueryRequest(BaseModel):
    question: str
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    top_k: int = 8


class CitedEntry(BaseModel):
    id: int
    content: str
    feedback_at: datetime
    theme_label: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitedEntry]