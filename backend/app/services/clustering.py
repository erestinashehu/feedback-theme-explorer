import numpy as np
from sklearn.cluster import AgglomerativeClustering
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


def _cluster_pass(pool: list[FeedbackEntry], embeddings: np.ndarray) -> list[np.ndarray]:
    """One clustering + purification pass. Returns a list of boolean masks,
    one per accepted theme, into the given pool/embeddings arrays."""

    # Cluster loosely first (linkage chaining catches distant-but-related
    # items), then purify each group against its own true centroid so
    # members that don't actually belong get excluded rather than forcing
    # an impure label on the whole group.
    clusterer = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.75,
        linkage="average",
        metric="cosine",
    )
    labels = clusterer.fit_predict(embeddings)

    accepted_masks = []

    for cluster_id in sorted(set(labels)):
        member_mask = labels == cluster_id
        if member_mask.sum() < settings.min_entries_for_new_theme:
            continue

        cluster_embeddings = embeddings[member_mask]
        rough_centroid = cluster_embeddings.mean(axis=0)

        norms = np.linalg.norm(cluster_embeddings, axis=1) * np.linalg.norm(rough_centroid)
        norms[norms == 0] = 1e-9
        similarities = (cluster_embeddings @ rough_centroid) / norms

        keep = similarities >= settings.cluster_similarity_threshold
        if keep.sum() < settings.min_entries_for_new_theme:
            continue

        full_mask = np.zeros(len(embeddings), dtype=bool)
        full_mask[np.where(member_mask)[0][keep]] = True
        accepted_masks.append(full_mask)

    return accepted_masks


def discover_new_themes(db: Session) -> list[Theme]:
    new_themes: list[Theme] = []

    for _ in range(5):  # safety cap: at most 5 refinement rounds per call
        pool = db.query(FeedbackEntry).filter(FeedbackEntry.theme_id.is_(None)).all()
        if len(pool) < settings.min_entries_for_new_theme:
            break

        embeddings = np.array([list(e.embedding) for e in pool])
        masks = _cluster_pass(pool, embeddings)

        if not masks:
            break

        for mask in masks:
            members = [m for m, keep in zip(pool, mask) if keep]
            member_embeddings = embeddings[mask]
            centroid = member_embeddings.mean(axis=0)

            label_info = generate_theme_label([m.content for m in members])

            theme = Theme(
                label=label_info.get("label", "new theme"),
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

        db.flush()

    return new_themes