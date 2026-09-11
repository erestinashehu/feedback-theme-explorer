# Customer Feedback Theme Explorer

A system that ingests customer feedback as free text with timestamps, automatically discovers recurring themes without a predefined category list, and answers analytical questions ("what are the top complaints this month?") grounded in real feedback quotes with citations.

## Architecture, briefly

frontend (React + Vite) --HTTP--> backend (FastAPI) --SQL/vector--> Postgres + pgvector
                                       |
                                       |-- sentence-transformers (embeddings, local)
                                       `-- Groq API (theme discovery, labeling, grounded Q&A)

Backend: Python / FastAPI
Database: PostgreSQL with the pgvector extension (embeddings + cosine search directly in SQL)
Embeddings: sentence-transformers (all-MiniLM-L6-v2) - local, free, runs on CPU
LLM: Groq (Llama-family open models via an OpenAI-compatible API) - used for (1) discovering and labeling themes from unclassified feedback, and (2) generating grounded analytical answers
Frontend: React + Vite + Tailwind CSS v4 + Recharts

### Why this stack (trade-offs)

- Local embeddings vs. API-based: sentence-transformers is free, runs offline, and needs no API key to ingest data - good for local development and demos. The LLM stays API-based (Groq) because it reasons about topic boundaries and natural language far better than distance-based methods on a small embedding model, while Groq's free tier and LPU-based inference keep it fast and cost-free.
- PostgreSQL + pgvector vs. a dedicated vector DB: allows semantic search (ORDER BY embedding <=> query_embedding) to be combined directly with normal SQL filters (date range, theme), without needing a separate vector database.

## How themes are discovered (no predefined list)

1. New feedback entry -> an embedding is generated (sentence-transformers, local model) -> compared (cosine similarity, via pgvector) against every existing theme's centroid.
2. If the similarity passes a threshold (CLUSTER_SIMILARITY_THRESHOLD, default 0.62) -> the entry joins that theme and its centroid is updated in place using a running-mean formula - O(1), never recomputing clusters from scratch (bonus requirement: incremental update).
3. If no theme is similar enough -> the entry stays unclassified, in a "pool".
4. When the pool has enough entries, discover_new_themes() asks the LLM (Groq) to group the pool directly into coherent themes by reading the actual text - this gives materially better topic separation than distance-based clustering on a small embedding model, since a language model understands semantic boundaries (e.g. distinguishing "billing complaints" from "shipping complaints") far more reliably than raw vector geometry. Large pools are first pre-grouped with K-Means on their embeddings so each batch sent to the LLM only contains related entries. Before creating a new theme, its label is checked against existing theme labels to avoid creating near-duplicate themes for the same underlying topic. The dashboard marks any theme created in the last 7 days with a small dot (bonus requirement: new theme detection).

This avoids two common problems: (a) recomputing the full clustering on every new entry (expensive), and (b) forcing every new entry into an existing theme even when it's genuinely something new.

Embeddings remain the backbone of the incremental-update path (steps 1-2 above) - the LLM is used specifically where semantic judgment matters most: deciding topic boundaries when discovering themes for the first time.

## Grounded analytical answers

POST /query takes a question plus an optional date range:
1. Embeds the question.
2. Finds the most semantically similar entries in Postgres, within the requested date range, in a single SQL query (WHERE feedback_at BETWEEN ... ORDER BY embedding <=> :q).
3. Sends only those entries to Groq as context, which is instructed (via the prompt) to cite specific [id]s for every claim - so the answer can't invent facts that aren't in the data. If the question asks specifically about complaints or praise, the prompt also instructs the model to cite only entries genuinely matching that sentiment.
4. The backend parses out exactly which [id]s were actually cited and returns only those as citations (not every entry that was retrieved for context).
5. The frontend renders citations as full quotes, linked to the [id] markers in the text.

## Resilience

If the LLM call fails (rate limits, timeouts) during ingest, the feedback entries and any existing-theme assignments are still committed - only the new-theme-discovery step is rolled back and retried on the next ingest call. A submission never loses data just because the LLM step had a bad moment.

## Repo structure

backend/
  app/
    main.py              FastAPI app + CORS
    config.py             .env settings
    models.py              Theme, FeedbackEntry (SQLAlchemy + pgvector)
    schemas.py              Pydantic request/response
    routers/
      feedback.py            POST /feedback/bulk, GET /feedback, POST /feedback/retry-discovery
      themes.py                GET /themes, GET /themes/{id}/trend
      query.py                  POST /query
    services/
      embeddings.py            sentence-transformers wrapper
      clustering.py             assign_entry, discover_new_themes
      analytics.py               semantic_search, get_theme_trend
      llm.py                      theme discovery, labeling, grounded Q&A (Groq)
frontend/
  src/
    pages/                UploadPage, DashboardPage, SearchPage
    components/           TrendChart, QuoteCard
    api.js                 HTTP client for the backend
docker-compose.yml

## Running it

cp .env.example .env
add your GROQ_API_KEY to .env (free, no card required - console.groq.com)

Option A: everything in Docker
docker compose up --build

Option B: run locally (recommended for development)
docker run -d --name feedback_db -e POSTGRES_USER=feedback -e POSTGRES_PASSWORD=feedback -e POSTGRES_DB=feedback_explorer -p 5432:5432 ankane/pgvector
docker exec -it feedback_db psql -U feedback -d feedback_explorer -c "CREATE EXTENSION IF NOT EXISTS vector;"

cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload

in a second terminal
cd frontend
npm install
npm run dev

Backend: http://localhost:8000 (Swagger docs at /docs)
Frontend: http://localhost:5173

## Main endpoints

POST /feedback/bulk - Ingest a list of entries {content, feedback_at}; returns how many were assigned to existing themes vs. sent to the pool, and any newly discovered themes
GET /feedback - List recent entries
GET /themes - List discovered themes with entry counts and an is_recently_discovered flag
GET /themes/{id}/trend?granularity=daily|weekly|monthly - Time trend for a theme
POST /feedback/retry-discovery - Re-run theme discovery over the existing unclassified pool, without ingesting new entries (useful if the LLM call failed earlier)
POST /query - {question, date_from?, date_to?} -> grounded answer + citations

## What I'd add with more time

- A periodic full re-clustering job (e.g. weekly) as a safety net alongside the incremental update, to correct any slow centroid drift.
- Authentication + multi-tenancy (currently a single-tenant demo).
- Automated tests (pytest for clustering/analytics, Vitest for the frontend).