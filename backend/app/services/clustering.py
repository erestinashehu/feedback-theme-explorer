import numpy as np
from sklearn.cluster import HDBSCAN
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Theme, FeedbackEntry
from app.services.embeddings import cosine_similarity
from app.services.llm import generate_theme_label


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

    embeddings = np.array([list(e.embedding) for e in pool])

    clusterer = HDBSCAN(
        min_cluster_size=max(settings.min_entries_for_new_theme, 3),
        min_samples=2,
        metric="cosine",
    )
    labels = clusterer.fit_predict(embeddings)

    new_themes: list[Theme] = []

    for cluster_id in sorted(set(labels)):
        if cluster_id == -1:
            continue

        member_indices = [i for i, lbl in enumerate(labels) if lbl == cluster_id]
        members = [pool[i] for i in member_indices]
        member_embeddings = embeddings[member_indices]
        centroid = member_embeddings.mean(axis=0)

        label_info = generate_theme_label([m.content for m in members])

        theme = Theme(
            label=label_info.get("label", "teme e re"),
            summary=label_info.get("summary"),
            centroid=centroid.tolist(),
            entry_count=len(members),
        )
        db.add(theme)
        db.flush()

        for member in members:
            member.theme_id = theme.id
            db.add(member)

        new_themes.append(theme)

    return new_themes