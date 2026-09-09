import json
import time
import requests

from app.config import settings

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def _call_gemini(prompt: str, max_retries: int = 6) -> str:
    url = _GEMINI_URL.format(model=settings.gemini_model)

    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                headers={"x-goog-api-key": settings.gemini_api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=90,
            )
        except requests.exceptions.RequestException as exc:
            last_error = exc
            time.sleep(3 * (2 ** attempt))
            continue

        if response.status_code in (503, 429, 500):
            last_error = response
            time.sleep(3 * (2 ** attempt))
            continue

        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

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

    text = _call_gemini(prompt)
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
- If the data isn't sufficient, say so plainly.
- Answer in ENGLISH, even if the feedback entries above are in another language.
- Do NOT use markdown formatting (no **bold**, no bullet points with *, no headers). Plain sentences only, separated naturally.
"""

    return _call_gemini(prompt)