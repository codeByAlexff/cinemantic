# Cinemantic

Natural-language semantic movie search over ~4,800 TMDB films. Search by what a movie is _about_, not by keyword.

## How it works

Plot overviews are embedded with OpenAI's `text-embedding-3-small` and stored in Postgres via pgvector. At query time the search string is embedded, then matched by cosine distance in a single SQL statement that also applies hard filters on year, runtime, and rating.

At ~4.8k rows exact search runs in a few milliseconds, so there's no ANN index — approximate search would trade recall for speed the dataset doesn't need.

## Results

Precision@10 against a hand-written set of 40 query/expected-title pairs:

| Method                         | Precision@10 |
| ------------------------------ | ------------ |
| Keyword baseline (SQL `ILIKE`) | —            |
| Semantic search                | —            |
| Semantic + LLM rerank          | —            |

## Stack

FastAPI · PostgreSQL + pgvector · Redis · React + Vite · OpenAI API

## Setup

```bash
# Postgres
createdb moviedb
psql moviedb -f api/schema.sql

# API
cd api
pip install -r requirements.txt
cp ../.env.example ../.env    # add your OPENAI_API_KEY
python ingest.py              # embeds ~4.8k movies (~2 min, ~$0.02)
uvicorn main:app --reload

# Frontend
cd web && npm install && npm run dev
```

Requires a running Redis (`brew services start redis`).

## Notes

Embeddings are cached in Redis by content hash with a 30-day TTL, so repeat queries skip the API round trip entirely. The cache fails open — if Redis is unreachable, searches still work, just slower.

Known limitation: embeddings ignore negation. "a comedy that isn't romantic" returns romantic comedies.
