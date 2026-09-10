from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FeedbackEntry
from app.schemas import BulkFeedbackIn, FeedbackOut, IngestResult
from app.services.embeddings import embed_batch
from app.services.clustering import assign_entry, discover_new_themes

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/bulk", response_model=IngestResult)
def ingest_bulk_feedback(payload: BulkFeedbackIn, db: Session = Depends(get_db)):
    texts = [e.content for e in payload.entries]
    embeddings = embed_batch(texts)

    created_entries: list[FeedbackEntry] = []
    for entry_in, embedding in zip(payload.entries, embeddings):
        entry = FeedbackEntry(
            content=entry_in.content,
            feedback_at=entry_in.feedback_at,
            embedding=embedding,
        )
        db.add(entry)
        created_entries.append(entry)

    db.flush()

    assigned_count = 0
    for entry in created_entries:
        if assign_entry(db, entry):
            assigned_count += 1

    # Commit now: entries + existing-theme assignments are always saved,
    # regardless of whether the LLM labeling step below succeeds.
    db.commit()

    new_theme_labels: list[str] = []
    try:
        new_themes = discover_new_themes(db)
        db.commit()
        new_theme_labels = [t.label for t in new_themes]
    except Exception:
        # Theme discovery/labeling failed (e.g. LLM rate limit). The
        # entries themselves are already safely committed above and
        # remain in the pool - the next ingest call will retry
        # discovery over the larger pool.
        db.rollback()

    return IngestResult(
        created=len(created_entries),
        assigned_to_existing_theme=assigned_count,
        sent_to_pool=len(created_entries) - assigned_count,
        newly_discovered_themes=new_theme_labels,
    )


@router.get("", response_model=list[FeedbackOut])
def list_feedback(limit: int = 100, db: Session = Depends(get_db)):
    entries = (
        db.query(FeedbackEntry)
        .order_by(FeedbackEntry.feedback_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for e in entries:
        out.append(
            FeedbackOut(
                id=e.id,
                content=e.content,
                feedback_at=e.feedback_at,
                theme_id=e.theme_id,
                theme_label=e.theme.label if e.theme else None,
            )
        )
    return out




@router.post("/retry-discovery", response_model=IngestResult)
def retry_theme_discovery(db: Session = Depends(get_db)):
    new_themes = discover_new_themes(db)
    db.commit()
    return IngestResult(
        created=0,
        assigned_to_existing_theme=0,
        sent_to_pool=0,
        newly_discovered_themes=[t.label for t in new_themes],
    )