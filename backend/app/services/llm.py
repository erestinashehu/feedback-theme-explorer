import json
import time
import requests

from app.config import settings

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _call_groq(prompt: str, max_retries: int = 4) -> str:
    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.post(
                _GROQ_URL,
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                },
                timeout=30,
            )
        except requests.exceptions.RequestException as exc:
            last_error = exc
            time.sleep(2 ** attempt)
            continue

        if response.status_code in (503, 429, 500):
            last_error = response
            time.sleep(2 ** attempt)
            continue

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    if isinstance(last_error, requests.exceptions.RequestException):
        raise last_error
    last_error.raise_for_status()
    return ""


def generate_theme_label(sample_texts: list[str]) -> dict:
    joined = "\n".join(f"- {t}" for t in sample_texts[:15])

    prompt = f"""Here are some customer feedback comments that were grouped together
because they discuss the same theme:

{joined}

Return ONLY a JSON object (no other text, no markdown fences) in this exact shape:
{{"label": "a short 2-4 word label in ENGLISH, e.g. 'shipping delays'", "summary": "one sentence in ENGLISH describing the theme"}}
"""

    text = _call_groq(prompt)
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"label": sample_texts[0][:40], "summary": None}


def answer_grounded_question(question: str, entries: list[dict]) -> str:
    if not entries:
        return "I couldn't find relevant feedback for this question in the specified period/search."

    context = "\n".join(
        f"[{e['ref_id']}] ({e['feedback_at']}) theme='{e.get('theme_label', 'unclassified')}': "
        f"{e['content']}"
        for e in entries
    )

    prompt = f"""You are an analyst answering questions based ONLY on the customer feedback
given below. Do not invent anything that isn't in it.

FEEDBACK:
{context}

QUESTION: {question}

Instructions:
- Answer briefly and concretely (2-5 sentences or a short list).
- Every claim must be supported by at least one citation in the form [id].
- CRITICAL: write each citation as its own separate bracket, like [3][7], never combine ids in one bracket like [3, 7].
- If the data isn't sufficient, say so plainly.
- Answer in ENGLISH, even if the feedback entries above are in another language.
- Do NOT use markdown formatting (no **bold**, no bullet points with *, no headers). Plain sentences only, separated naturally.
- If the question asks specifically about complaints, problems, or issues, cite ONLY entries that are genuinely negative in tone. Do NOT reframe positive or neutral feedback as a complaint. If there aren't enough genuinely negative entries to answer, say so plainly instead of stretching positive ones to fit.
- Likewise, if the question asks specifically about praise, satisfaction, or what customers like, cite ONLY genuinely positive entries.
"""

    return _call_groq(prompt)


def verify_cluster_membership(label: str, entries: list[dict]) -> set[int]:
    """Ask the LLM to double-check which entries genuinely belong to a
    proposed theme. Returns the set of ref_ids that should be KEPT.
    This catches embedding-similarity false positives (e.g. two sentences
    with similar grammatical structure but unrelated topics) that a small
    embedding model can miss but an LLM immediately recognizes."""

    listed = "\n".join(f"{e['ref_id']}: {e['content']}" for e in entries)

    prompt = f"""A clustering algorithm grouped these customer feedback comments
under the proposed theme label "{label}":

{listed}

Some comments may have been grouped incorrectly (they don't actually relate
to this theme, even if the wording looks superficially similar).

Return ONLY a JSON object with this exact shape, no other text:
{{"keep_ids": [list of the numeric ids that GENUINELY belong to "{label}"]}}

Be strict: only keep an id if it truly discusses the same topic as the theme label.
"""

    text = _call_groq(prompt)
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]

    try:
        data = json.loads(text)
        return set(int(i) for i in data.get("keep_ids", []))
    except (json.JSONDecodeError, ValueError, TypeError):
        return {e["ref_id"] for e in entries}


def cluster_pool_directly(entries: list[dict]) -> list[dict]:
    """Ask the LLM to group a pool of unclassified feedback entries into
    coherent themes directly, rather than relying on embedding-distance
    thresholds. An LLM understands topic boundaries far more reliably than
    geometric clustering on a small embedding model, especially for
    correctly separating adjacent-but-distinct topics."""

    listed = "\n".join(f"{e['ref_id']}: {e['content']}" for e in entries)

    prompt = f"""Group these customer feedback comments into coherent themes.
Each theme should have at least 3 comments and cover ONE clear, specific topic.
Do not mix unrelated topics into the same theme. Leave out any comment that
doesn't clearly fit a group of at least 3 similar comments.

COMMENTS:
{listed}

Return ONLY a JSON object, no other text, in this exact shape:
{{"themes": [
  {{"label": "short 2-4 word label in ENGLISH", "summary": "one sentence in ENGLISH", "entry_ids": [list of numeric ids]}}
]}}
"""

    text = _call_groq(prompt)
    print(f"DEBUG raw Groq response:\n{text}\n---END---")
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]

    try:
        data = json.loads(text)
        return data.get("themes", [])
    except (json.JSONDecodeError, TypeError) as exc:
        print(f"DEBUG JSON parse failed: {exc}")
        return []