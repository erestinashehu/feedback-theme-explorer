import numpy as np
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Theme, FeedbackEntry
from app.services.embeddings import cosine_similarity
from app.services.llm import cluster_pool_directly


def find_best_matching_theme(db: Session, embedding: list[float]) -> tuple[Theme | None, float]:
    theme = (
        db.query(Theme)
        .order_by(Theme.centroid.cosine_distance(embedding))
        .first()
    )
    if theme is None:
        return None, 0.0

    similarity = cosine_similarity(embedding, list(theme.centroid))
    return theme, similarity


def _update_centroid_incremental(theme: Theme, new_embedding: list[float]) -> None:
    old_centroid = np.array(theme.centroid, dtype=np.float64)
    x = np.array(new_embedding, dtype=np.float64)
    n = theme.entry_count

    new_centroid = old_centroid + (x - old_centroid) / (n + 1)
    theme.centroid = new_centroid.tolist()
    theme.entry_count = n + 1


def assign_entry(db: Session, entry: FeedbackEntry) -> bool:
    theme, similarity = find_best_matching_theme(db, list(entry.embedding))

    if theme is not None and similarity >= settings.cluster_similarity_threshold:
        entry.theme_id = theme.id
        _update_centroid_incremental(theme, list(entry.embedding))
        db.add(theme)
        db.add(entry)
        return True

    return False


def discover_new_themes(db: Session) -> list[Theme]:
    pool = db.query(FeedbackEntry).filter(FeedbackEntry.theme_id.is_(None)).all()

    if len(pool) < settings.min_entries_for_new_theme:
        return []

    pool_by_id = {e.id: e for e in pool}
    payload = [{"ref_id": e.id, "content": e.content} for e in pool]

    proposed_themes = cluster_pool_directly(payload)

    new_themes: list[Theme] = []

    for proposed in proposed_themes:
        entry_ids = proposed.get("entry_ids", [])
        members = [pool_by_id[i] for i in entry_ids if i in pool_by_id]

        if len(members) < settings.min_entries_for_new_theme:
            continue

        proposed_label = proposed.get("label", "new theme")

        # If a theme with this exact label already exists, merge into it
        # instead of creating a duplicate - the LLM can independently
        # arrive at the same name for a group that embeddings judged
        # "not quite similar enough" to auto-merge on its own.
        existing = (
            db.query(Theme)
            .filter(Theme.label.ilike(proposed_label))
            .first()
        )

        member_embeddings = np.array([list(m.embedding) for m in members])

        if existing is not None:
            for member in members:
                member.theme_id = existing.id
                _update_centroid_incremental(existing, list(member.embedding))
                db.add(member)
            db.add(existing)
            continue

        centroid = member_embeddings.mean(axis=0)

        theme = Theme(
            label=proposed_label,
            summary=proposed.get("summary"),
            centroid=centroid.tolist(),
            entry_count=len(members),
        )
        db.add(theme)
        db.flush()

        for member in members:
            member.theme_id = theme.id
            db.add(member)

        new_themes.append(theme)

    db.flush()

    if new_themes:
        leftover = db.query(FeedbackEntry).filter(FeedbackEntry.theme_id.is_(None)).all()
        for entry in leftover:
            assign_entry(db, entry)

    return new_themes