# FinFeluda — AI Due Diligence Copilot

An AI-powered platform that investigates a company from uploaded documents and/or its public
footprint, then produces a financial health score, a risk analysis with genuine
contradiction-detection, an executive summary, recommendations, a RAG-based chat interface, and a
downloadable report — no login required.

Point it at a company. It gathers evidence, scores it, and tells you what needs a second look —
and shows exactly where every claim came from.

---

## Table of contents

- [Why](#why)
- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [API overview](#api-overview)
- [Frontend routes](#frontend-routes)
- [Design system](#design-system)
- [Known limitations](#known-limitations)
- [Further reading](#further-reading)

---

## Why

Due diligence on a company — before an investment, a partnership, or a hire — is still largely
manual. An analyst opens a filing, searches news coverage, skims GitHub or job listings, reads the
company's own marketing, and holds all of it in their head to decide what to trust. Three problems
make this slow and unreliable, especially for companies in markets like Bangladesh where structured
financial data is sparser and public source coverage is uneven:

- **Source credibility is invisible.** A claim from an audited filing and a claim from an anonymous
  forum post are easy to conflate once both are just "text on a screen."
- **Contradictions go unnoticed.** A company's own marketing ("category leader") is rarely checked
  against independent signal (declining GitHub activity, negative reviews, an unrenewed contract)
  because doing so by hand across a dozen sources is tedious.
- **Bangladesh-specific sources are scattered.** DSE, CSE, BSEC, Bangladesh Bank, and RJSC each
  publish through different, non-uniform channels, and some serve broken TLS certificate chains
  that silently fail in standard HTTP clients.

FinFeluda automates the gather-and-judge work: it fans out to 15+ sources concurrently, tags every
fact with a confidence tier, and hands the tiered evidence to an LLM reasoning stage that is
explicitly instructed to cross-reference a company's own claims against independent evidence.

## What it does

- **Deterministic Financial Health Score** (0–100) computed from actual extracted ratios (profit
  margin, debt ratio, ROA/ROE) — reproducible, not an LLM's opinion.
- **LLM-generated Risk Score** with Financial/Operational/Business sub-scores, each backed by
  concrete, sourced red flags with a severity and a recommendation.
- **Contradiction detection** — the reasoning stage is explicitly instructed to flag where a
  company's own claims disagree with independent public signal, not just list generic risks.
- **RAG-based chat**, scoped to one investigation (or to a two-investigation comparison), grounded
  only in that investigation's gathered evidence and already-computed analysis — it will say
  "not enough evidence" rather than invent an answer.
- **Side-by-side comparison** of two investigations: a metrics table, score charts, and an
  AI-written comparison.
- **Downloadable PDF report** generated on demand and streamed directly (no dependency on a
  third-party file host being configured correctly).
- **Full source trail** — every source the AI actually fetched from, grouped by confidence tier,
  with a link back to the original.

## How it works

```
POST /upload  (PDFs and/or a company name + website URL)
   │
   ▼
GATHER      Concurrently pulls from uploaded PDFs, a live website crawl, Wayback Machine
            snapshots, and 15 independent public/regulatory fetchers — GitHub, Reddit,
            NewsAPI, Google Maps, YouTube, Google Search, and Bangladesh-specific sources
            (DSE, CSE, BSEC, Bangladesh Bank, MCCI, BDJobs, BD News). Every fetcher is
            individually fault-isolated, so one dead API never blocks the rest.
   │
   ▼
NORMALIZE   Boundary-aware chunking (tuned per source density), then dense + sparse (BM25)
            embeddings, stored in Qdrant with full source provenance attached.
   │
   ▼
REASON      Four schema-validated Groq (Llama 3.3 70B) calls: structured financial
            extraction, risk analysis with explicit tier-1/2-vs-tier-3/4
            cross-referencing, and a combined executive summary + recommendations call.
            Automatically falls back to Gemini if Groq's daily quota is exhausted —
            transparent to every caller.
   │
   ▼
PERSIST     Writes Company/Financial/Risk/Report rows to Postgres and flips investigation
            status to completed, which the frontend's polling hook picks up.
```

The whole chain runs automatically in one background task after upload — no manual trigger
needed. `POST /analyze/{id}` re-runs just the REASON stage from already-gathered evidence, so a
transient LLM failure (like a quota error) never requires re-uploading anything.

### Evidence tiers

Every chunk carries one of four confidence tiers, assigned automatically from its source type and
injected directly into every LLM prompt — the model is told explicitly how much to trust each
fact, not left to infer it from context.

| Tier | Label             | Example sources                                              |
|------|-------------------|----------------------------------------------------------------|
| 1    | Authoritative     | Uploaded filings, DSE/CSE/BSEC/Bangladesh Bank filings         |
| 2    | Official          | Company website, GitHub org, Google Maps, job listings         |
| 3    | Corroborating     | News coverage, Wikipedia, web archive, chamber directories     |
| 4    | Unverified signal | Reddit, YouTube comments, Glassdoor, forum chatter              |

### AI/ML approach, briefly

- **Structured output everywhere.** Every LLM call that produces data the app relies on is
  schema-validated against a Pydantic model; a validation failure re-prompts the model with its
  own error fed back in, up to a retry limit.
- **Dual-provider fallback.** Groq's free tier caps usage at 100k tokens/day. Both the plain and
  schema-validated call paths transparently fall back to Gemini on a Groq rate-limit error —
  callers never know which provider actually answered.
- **Hybrid retrieval for chat.** Questions are embedded with the same multilingual dense model
  used for stored chunks, plus a separate BM25 sparse embedding; the two ranked lists are merged
  with Reciprocal Rank Fusion rather than averaged raw scores.
- **Deterministic scoring, layered against LLM judgment.** The Financial Health Score is a fixed
  formula over five sub-scores (Growth, Liquidity, Profitability, Debt, Efficiency) — the same
  inputs always produce the same score. The Risk Score needs qualitative judgment a formula can't
  capture, so it's LLM-generated, but every sub-score must be backed by concrete, sourced red
  flags rather than a bare number.

For the full breakdown — including known limitations and ethical considerations of the AI
component — see the [Model & Data Card](#further-reading).

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS v4, React Router 7, TanStack Query, Recharts, Framer Motion, Axios |
| Backend | FastAPI (Python), fully async |
| AI / LLM | Groq (Llama 3.3 70B), automatic Gemini (2.5 Flash-Lite) fallback on quota exhaustion |
| Vector DB | Qdrant (hybrid dense + sparse/BM25 search) |
| Embeddings | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (multilingual — Bangla + English) via fastembed/ONNX |
| Database | PostgreSQL (Supabase), SQLite fallback for local dev |
| File storage | Cloudinary (archival), PDFs streamed directly for downloads |

Every cloud service is configured via `backend/.env` and falls back to a local alternative
(SQLite, embedded Qdrant) when not configured, so the app runs end-to-end for local dev without
any cloud credentials.

## Project structure

```
FinFeluda/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers (upload, analyze, chat, compare, report, ...)
│   │   ├── sources/         # One fetcher per public/regulatory source
│   │   ├── services/        # Embedding, Qdrant, Groq/Gemini, scoring, reasoning, chat, PDF
│   │   ├── prompts/         # Prompt builders per reasoning task
│   │   ├── schemas/         # Pydantic contracts (source docs, LLM outputs, API I/O)
│   │   └── models/          # SQLAlchemy models
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   └── src/
│       ├── pages/           # One file per route
│       ├── components/      # investigation/, layout/, charts/, chat/, ui/
│       ├── hooks/           # TanStack Query hooks
│       ├── api/             # Axios calls per resource
│       └── lib/             # Shared formatting/color/token utilities
└── README.md
```

## Getting started

### Prerequisites

- Python 3.12+
- Node.js 18+
- (Optional) API keys for Groq, Gemini, Qdrant Cloud, Supabase, Cloudinary, Serper, YouTube — the
  app runs locally without any of these, using SQLite and an embedded Qdrant instance instead.

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env          # fill in whichever keys you have; unset ones fall back locally
python main.py                # or: uvicorn main:app --reload
```

The backend starts on `http://localhost:8000`. On first run it idempotently diffs each SQLAlchemy
model's columns against the live database and adds anything missing — no manual migration step
required for schema changes.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend starts on `http://localhost:5173` and expects the backend at `http://localhost:8000`
(see `CORS_ORIGINS` in `backend/.env`).

### Environment variables

See `backend/.env.example` for the full list. Nothing is required to run locally — every
integration (Groq, Gemini, Qdrant, Postgres, Cloudinary, YouTube, Serper) degrades gracefully to a
local fallback or a "not configured, skipping" no-op when its key is missing.

## API overview

| Endpoint | Description |
|---|---|
| `POST /upload/` | Runs the full GATHER → NORMALIZE → REASON → PERSIST pipeline |
| `POST /analyze/{id}` | Re-runs just the REASON stage from already-gathered evidence |
| `GET /investigations/` | List all investigations |
| `GET /investigations/{id}` | Full nested detail: company, financials, risk analysis, scores |
| `GET /investigations/{id}/status` | Live status, polled by the frontend during processing |
| `GET /investigations/{id}/sources` | Every source actually fetched, deduped and tiered |
| `POST /chat/` | RAG chat scoped to one investigation |
| `GET /compare/` | AI-generated comparison of two investigations |
| `POST /compare/chat/` | RAG chat scoped to a two-investigation comparison |
| `GET /report/{id}` | Persisted report sections |
| `GET /report/{id}/download` | Generates and streams the report as a PDF |
| `GET /dashboard/stats` | Live counts for the dashboard |

## Frontend routes

| Route | Purpose |
|---|---|
| `/` | Landing page |
| `/dashboard` | All investigations, with health/risk score, status, date |
| `/new` | Upload PDF(s) and/or a website URL |
| `/investigations/:id/processing` | Live status polling |
| `/investigations/:id` | Company overview, financial charts, health score, risk summary |
| `/investigations/:id/risks/:category` | Deep-dive per risk category |
| `/investigations/:id/red-flags` | Every red flag, with severity/category breakdown |
| `/investigations/:id/summary` | Executive summary |
| `/investigations/:id/recommendations` | Recommendations |
| `/investigations/:id/sources` | Every fetched source, grouped by confidence tier |
| `/investigations/:id/chat` | AI chat for this investigation |
| `/investigations/:id/report` | Full report + PDF download |
| `/compare` | Side-by-side comparison of two investigations |

## Design system

Light-mode, professional fintech look (Fraunces display serif + IBM Plex Sans/Mono), built around
an "evidence ledger" signature: every AI-derived claim is visually tagged with its confidence tier
via a colored left-edge bar and a mono-caps badge — drawn directly from the backend's real
source-provenance model, not decorative.

## Known limitations

- Reranking (cross-encoder) is disabled — a third ONNX model alongside the dense+sparse embedders
  exceeded the deploy environment's memory budget, so chat retrieval ordering is RRF-only.
- RJSC (Bangladesh's company registry) is not fetched — a genuinely unfixable TLS trust issue,
  confirmed independently of the DSE/CSE certificate-chain fix.
- Facebook, X/Twitter, LinkedIn, Instagram, Crunchbase, and Glassdoor are not scraped — paid API
  tiers or app-review access required, and ToS restricts Glassdoor scraping specifically. These
  surface as labeled, unanalyzed "explore more" links instead.
- Current ratio is not computed — the extraction schema captures total assets/liabilities, not the
  current-vs-non-current split a real current ratio needs; deliberately omitted rather than
  mislabeled.
- Groq's free-tier daily token cap (100k tokens/day) can still be exhausted alongside Gemini's own
  quota under heavy testing; investigations fail with the real error recorded and a one-click
  retry that doesn't require re-uploading anything.

## Further reading

- **`PROJECT_STATUS.md`** — internal, more granular build log of what's implemented and what
  deviates from the original spec.
- **Model & Data Card** and **Project Report** — generated as standalone PDFs covering the
  datasets/models/licenses/ethical considerations and a full methodology write-up respectively;
  regenerate them from the report-generation scripts if needed, or ask for a fresh copy.
