# Phase 4 — Semantic Search (RAG + Pinecone)

## Purpose

Natural-language candidate retrieval using Sentence-Transformers embeddings stored in **Pinecone** (or a local NPZ cosine index when `PINECONE_API_KEY` is empty).

## Flow

```
CV upload → extract profile → upsert embedding (candidate id)
HR query → embed query → vector top-K → enrich from MySQL
```

## Endpoints

| Layer | Path |
|-------|------|
| AI | `POST /api/v1/embeddings/upsert` |
| AI | `POST /api/v1/search` |
| Backend | `POST /api/search` |
| Backend | `POST /api/search/sync` |
| UI | `/search` |

## Config

```
PINECONE_API_KEY=        # optional
PINECONE_INDEX_NAME=cv-screening
```

Without a Pinecone key, the AI service uses `models/vectors/local_index.npz`.
