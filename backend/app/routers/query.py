import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import QueryRequest, QueryResponse, CitedEntry
from app.services.embeddings import embed_text
from app.services.analytics import semantic_search
from app.services.llm import answer_grounded_question

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def ask_question(payload: QueryRequest, db: Session = Depends(get_db)):
    query_embedding = embed_text(payload.question)

    entries = semantic_search(
        db,
        query_embedding,
        date_from=payload.date_from,
        date_to=payload.date_to,
        top_k=payload.top_k,
    )

    context_entries = [
        {
            "ref_id": e.id,
            "content": e.content,
            "feedback_at": e.feedback_at.isoformat(),
            "theme_label": e.theme.label if e.theme else None,
        }
        for e in entries
    ]

    answer = answer_grounded_question(payload.question, context_entries)

    cited_ids = {int(m) for m in re.findall(r"\[(\d+)\]", answer)}
    cited_entries = [e for e in entries if e.id in cited_ids]
    if not cited_entries:
        cited_entries = entries

    citations = [
        CitedEntry(
            id=e.id,
            content=e.content,
            feedback_at=e.feedback_at,
            theme_label=e.theme.label if e.theme else None,
        )
        for e in cited_entries
    ]

    return QueryResponse(answer=answer, citations=citations)