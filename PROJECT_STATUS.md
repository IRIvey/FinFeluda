# FinFeluda — AI Due Diligence Copilot: Project Status

An AI-powered platform that investigates a company from public sources and/or uploaded
documents, then produces a financial health score, risk analysis, executive summary,
recommendations, timeline, and a downloadable due diligence report — no login required.

Last updated: 2026-07-07

---

## Tech stack (as actually deployed)

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS v4, React Router 7, TanStack Query, Recharts, Axios |
| Backend | FastAPI, Python |
| AI | Groq API (Llama 3.3 70B) |
| Vector DB | Qdrant Cloud (hybrid dense + sparse/BM25 search) |
| Database | PostgreSQL (Supabase) |
| File storage | Cloudinary |
| PDF report generation | `reportlab` (not `weasyprint` — see [Notable deviations](#notable-deviations-from-the-original-spec)) |

Every cloud service is configured via `backend/.env` and falls back to a local
alternative (SQLite, embedded Qdrant) when not configured, so the app can still run
end-to-end for local dev without any cloud credentials. See
[Local dev fallbacks](#local-dev-fallbacks).

---

## What's built

### Frontend pages
| Page | Route | Status |
|---|---|---|
| Dashboard | `/` | Lists all investigations with health/risk score, status, date |
| New Investigation | `/new` | Upload PDF(s) and/or a website URL |
| Processing | `/investigations/:id/processing` | Live status polling with honest progress copy |
| Investigation Dashboard | `/investigations/:id` | Company overview, financial charts, health score, risk summary, red flags, executive summary, recommendations, timeline |
| Financial / Operational / Business Risk | `/investigations/:id/risks/:category` | Dedicated deep-dive page per risk category with score + full finding detail |
| Sources | `/investigations/:id/sources` | Every source the AI actually fetched from (grouped by confidence tier, with links), plus "Explore more" quick-links to Facebook/X/LinkedIn/Instagram/Crunchbase/Glassdoor |
| Compare | `/compare` | Side-by-side metrics table + chart + AI-generated comparison for two completed investigations |
| Report | `/investigations/:id/report` | Full report sections + PDF download |
| AI Chat | `/investigations/:id/chat` | UI fully built; **backend intentionally not implemented** (see below) |

### Design system
Light-mode, professional fintech look (Fraunces display serif + IBM Plex Sans/Mono),
built around an "evidence ledger" signature: every AI-derived claim is visually tagged
with its confidence tier (1=Authoritative … 4=Unverified signal) via a colored left-edge
bar and mono-caps badge — drawn directly from the backend's real source-provenance model,
not decorative.

### Backend pipeline
```
POST /upload  (PDFs and/or website URL)
   ↓
GATHER    — pulls from uploaded PDFs, company website, and public sources:
            SEC EDGAR, Wikipedia, GitHub, Reddit, News, Google Maps, YouTube,
            Google Search, Glassdoor (deliberately stubbed, see below)
   ↓
NORMALIZE — boundary-aware chunking, dense + sparse (BM25) embeddings,
            stored in Qdrant with full source provenance
   ↓
REASON    — Groq-powered: structured financial extraction, risk analysis
            (with cross-referencing between company claims and independent
            signal — genuinely detects contradictions), executive summary,
            recommendations
   ↓
PERSIST   — writes Company/Financial/Risk/Report rows to Postgres,
            investigation status → completed
```
This whole chain runs automatically in one background task after upload — no manual
trigger needed. `POST /analyze/{id}` exists as a standalone re-run path (re-reads
already-stored Qdrant chunks) for retrying failed/interrupted analyses without
re-uploading anything.

### Backend endpoints
| Endpoint | Status |
|---|---|
| `POST /upload/` | Full pipeline, real |
| `POST /analyze/{id}` | Real — standalone re-run of the REASON stage |
| `GET /investigations/` | Real |
| `GET /investigations/{id}` | Real — full nested detail (company, financials, risk analysis, executive summary, recommendations, health subscores) |
| `GET /investigations/{id}/status` | Real |
| `GET /investigations/{id}/sources` | Real — deduped list of every fetched source |
| `GET /compare/` | Real — Groq-generated comparison |
| `GET /report/{id}` | Real |
| `GET /report/{id}/download` | Real — generates PDF via `reportlab`, uploads to Cloudinary |
| `GET /dashboard/stats` | Real — live counts from the DB |
| `POST /chat/` | **Stub only** — `{"answer": "Not implemented yet", "sources": []}`, out of scope by explicit request |

### Scoring
- **Financial Health Score** (0–100): deterministic average of 5 subscores — Growth,
  Liquidity, Profitability, Debt, Efficiency — computed from extracted financial ratios
  (profit margin, debt ratio, ROA; ROE where equity is positive).
- **Risk Score**: Groq-generated overall + Financial/Operational/Business sub-scores,
  each backed by concrete red flags (reason, severity, recommendation, supporting
  sources, contradiction flag).

---

## Notable deviations from the original spec

- **PDF report generation uses `reportlab`, not `weasyprint`.** `weasyprint` requires
  native GTK/Pango/Cairo libraries not available on this Windows dev machine (and a
  common pain point on other platforms too). `reportlab` is pure-Python with no native
  dependencies and produces the same result.
- **Glassdoor is not scraped.** No free public API exists, and scraping violates their
  ToS. The fetcher exists and reports this explicitly rather than silently omitting
  Glassdoor — shows up on the Sources page as a manual "Explore more" link instead.
- **Facebook, X/Twitter, LinkedIn, Instagram, Crunchbase are not scraped.** All either
  require a paid API tier or app-review access for search. These appear as direct
  search-URL "Explore more" links on the Sources page instead, clearly labeled as
  unanalyzed.
- **Current ratio is not computed.** The financial extraction schema captures total
  assets/liabilities, not the current-vs-non-current split a real current ratio needs —
  deliberately omitted rather than mislabeling a wrong number.

## Local dev fallbacks

These only activate when the corresponding `backend/.env` value is missing/still the
`.env.example` placeholder — real credentials always take priority:
- `DATABASE_URL` unset → local SQLite file (`backend/dev.db`)
- `QDRANT_URL` unset → qdrant-client's embedded local mode (`backend/qdrant_data/`)
- No Alembic migrations exist yet — an idempotent startup step diffs each SQLAlchemy
  model's columns against the live database and adds anything missing, so schema
  changes don't require a manual migration step (verified safe against the real
  Supabase instance without losing existing rows).

## Known open items
- **AI Chat backend** — explicitly out of scope for now (frontend UI is done, waiting
  for RAG wiring: embed question → hybrid search in Qdrant → rerank → Groq).
- **Cloudinary raw-file delivery** — uploaded/generated PDFs upload successfully but the
  public URL can return `401 Unauthorized` depending on the Cloudinary account's
  "Restricted media types" security setting — a dashboard toggle on the Cloudinary side,
  not a code issue.
- **Groq free-tier daily token cap** (100k tokens/day on the on-demand tier) — heavy
  testing can exhaust it; investigations fail cleanly with the quota error recorded in
  `error_message`, and `/analyze/{id}` can retry once the quota resets without
  re-uploading anything.

## Sample test data
`sample-documents/` contains two generated PDFs (Annual Report + Investor Pitch Deck)
for a fictional company ("Fenwick Grid Systems") with a deliberate multi-year financial
arc (growth → debt-funded acquisition → two years of revenue decline with rising costs)
designed to exercise every dashboard feature: health score subscores, financial charts,
timeline, and a red flag matching the spec's own example almost verbatim. Not committed
to git (local-only test fixtures).

---

## Repo / branch history
- `main` — production branch, everything below merged in
- `landing-page` — superseded, initial frontend scaffolding work
- `frontend-polish` — superseded, merged into main (full backend pipeline wiring)
- `detailed-analysis-pages` — superseded, merged into main (risk category pages, Sources page)
- `frontend-design` — current working branch (page design changes, new pages)
