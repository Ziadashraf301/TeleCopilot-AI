# TeleCopilot AI – Telecom Customer Service Agent Assist

TeleCopilot AI is a RAG copilot for telecom customer service representatives (CSRs). A CSR types the customer's
problem, and TeleCopilot searches the company's Arabic and English policy documents and live website pages, then
returns a ready-to-use resolution: the detected intent, the policy that applies, step-by-step actions, a suggested
reply to the customer, and citations to the exact sources. It also reports latency, tokens and cost for every request.

> The policy documents in `data/raw/` are sample telecom documents (Arabic and English) built for this project.
> Live pages are scraped from https://www.te.eg/.

---

## What it does

- **Multi-format ingestion.** Indexes 10 local policy documents (HTML, XML, DOCX, text PDFs and scanned PDFs) and
  4 live pages from te.eg into one Qdrant collection. Scanned and Arabic PDFs are read with **Gemini Vision OCR**.
- **Format-aware chunking.** Each format has its own LangChain splitter, so headers, steps and tables stay together.
  Every chunk is tagged with one of 12 intent categories (billing, SIM, roaming, fraud, broadband installation, and more).
- **Hybrid retrieval.** Cohere multilingual dense vectors + BM25 sparse vectors, fused in Qdrant with Reciprocal Rank
  Fusion (RRF), with optional filters on intent, source format and policy type.
- **Reranking.** Cohere Rerank v3.5 keeps the 3 most relevant chunks.
- **Grounded answers.** Gemini returns a structured JSON resolution, or streams the reply token by token over
  Server-Sent Events (SSE).
- **Observability.** Langfuse traces every stage (embedding, hybrid search, rerank, LLM) with latency, tokens and
  estimated cost.
- **Agent dashboard.** A web UI for CSRs, served by the same FastAPI app.

---

## Architecture

```mermaid
graph LR
    subgraph Sources
        RAW[data/raw<br/>HTML · XML · DOCX · PDF]
        WEB[te.eg live pages]
    end
    subgraph Ingestion
        EF[ExtractorFactory<br/>HTML · XML · DOCX · Gemini OCR · Web scraper]
        CF[ChunkerFactory<br/>format-aware splitters + intent tags]
    end
    subgraph Indexing
        DENSE[Cohere embed-multilingual-v3.0<br/>1024-dim]
        SPARSE[Qdrant/bm25<br/>sparse vectors]
        QD[(Qdrant)]
    end
    subgraph Agent Assist
        API[FastAPI<br/>/api/agent-assist/solve]
        HS[Hybrid search<br/>RRF + filters]
        RR[Cohere Rerank v3.5]
        LLM[Gemini<br/>JSON or SSE stream]
    end
    RAW --> EF
    WEB --> EF
    EF --> CF --> DENSE --> QD
    CF --> SPARSE --> QD
    API --> HS --> QD
    HS --> RR --> LLM --> API
    API -. traces .-> LF[Langfuse]
```

### Request flow

1. **Embed** the CSR query (dense + sparse).
2. **Hybrid search** in Qdrant: top 5 by RRF fusion, with optional intent / format / policy filters.
3. **Rerank** with Cohere Rerank v3.5 and keep the top 3.
4. **Generate** with Gemini, grounded in the reranked chunks.
5. **Return** the structured resolution (or stream it) with citations, latency breakdown, tokens and cost.

### Ingestion details

| Format | Extractor | Chunking strategy |
|---|---|---|
| HTML | `HTMLExtractor` | `HTMLHeaderTextSplitter` on h1–h3, then recursive split (500 / 80 overlap) |
| PDF (text or scanned, Arabic/English) | `GeminiOCRExtractor` | Gemini Vision → Markdown, `MarkdownHeaderTextSplitter`, then recursive split (600 / 100) |
| DOCX | `DocxExtractor` | Clause-aware recursive split (450 / 60) |
| XML | `XMLExtractor` | Recursive split (500 / 80) |
| Live web pages | `WebScraperExtractor` (httpx) | `HTMLHeaderTextSplitter`, then recursive split (650 / 120) |

**Intent categories:** `SIM_MANAGEMENT`, `NETWORK_TECHNICAL_SUPPORT`, `ROAMING_AND_INTERNATIONAL`,
`ENTERPRISE_B2B_SUPPORT`, `BILLING_AND_PAYMENTS`, `BROADBAND_INSTALLATION`, `FRAUD_AND_SECURITY`,
`ACCOUNT_MIGRATION_OFFERS`, `ROUTER_HARDWARE_SUPPORT`, `WIFI_TECHNICAL_SUPPORT`, `PLANS_AND_OFFERS`, `GENERAL_SUPPORT`.

### Response example (fields)

`POST /api/agent-assist/solve` returns:

| Field | Meaning |
|---|---|
| `customer_issue_summary` | One-line summary of the problem |
| `detected_intent` | One of the 12 intent categories |
| `policy_applied` / `primary_source_modality` | Which policy answered it, and from which format |
| `resolution_status` | Resolved, needs escalation, and so on |
| `actionable_agent_steps` | Step-by-step actions for the CSR |
| `suggested_customer_reply` | Ready-to-send reply |
| `policy_citations` | The top reranked sources |
| `sla_or_credit_details` | SLA or credit information when relevant |
| `latency_breakdown`, `total_tokens`, `estimated_cost_usd` | Per-request telemetry |

---

## Code structure

The app uses a layered **controller → service → repository** design, with **factories** for extractors and
chunkers, **singletons** for API clients and the database connection, and FastAPI dependency injection.

```
src/
├── api/main.py              FastAPI app; ingests sources on startup if Qdrant is empty
├── controllers/             agent assist, ingestion, scraper, documents, health
├── services/                agent_assist, ingestion, cohere, gemini, sparse embeddings
├── repositories/            Qdrant repository (collection, upsert, hybrid search)
├── ingestion/
│   ├── extractors/          html, xml, docx, gemini_ocr, web_scraper
│   ├── chunkers/            format-aware policy chunkers
│   └── factories.py         ExtractorFactory, ChunkerFactory
├── core/                    logger (loguru), Langfuse observability, singletons
├── models/                  Pydantic API and document models
└── config/settings.py       pydantic-settings configuration
static/                      CSR dashboard (HTML, CSS, JS)
tests/                       11 pytest modules
```

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/agent-assist/solve` | Structured JSON resolution |
| POST | `/api/agent-assist/solve/stream` | Token-by-token reply over SSE |
| POST | `/api/ingest/all` | Re-ingest all local documents and live pages |
| POST | `/api/ingest/scrape-url` | Scrape and index one URL |
| POST | `/api/scraper/run` | Run the scraper manually |
| GET | `/api/v1/policies` | List indexed policy documents |
| GET | `/api/v1/files/raw/{filename}` · `/api/v1/files/preview/{filename}` | Download or preview a source file |
| GET | `/api/health` | Health check |

---

## Tech stack

**Python** · **FastAPI** · **Qdrant** (hybrid dense + sparse, RRF) · **Cohere** (embed-multilingual-v3.0, rerank-v3.5) ·
**Gemini** (generation + Vision OCR) · **LangChain** text splitters · **Langfuse** · **loguru** · **Pydantic** ·
**Docker / Docker Compose** · **Pytest** · **GitHub Actions**

---

## Run it

### 1. Configure

Create a `.env` file:

```env
COHERE_API_KEY=your_cohere_key
GEMINI_API_KEY=your_gemini_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
# optional
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 2. Start with Docker Compose

```bash
docker compose up --build
```

This starts Qdrant (v1.13.0) and the app. On first start, the app ingests all local documents and live pages into
Qdrant, then serves the dashboard at http://localhost:8000.

### 3. Or run locally

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Tests

```bash
pytest -v
```

GitHub Actions runs the test suite and builds the Docker image on every push and pull request.

---

## Roadmap

- **Extraction quality evaluation (in progress):** human-verified ground truth for all 10 documents, scored with
  word-level F1, ROUGE-L, entity and number retention, section order (Kendall's tau) and a Gemini LLM-as-a-judge,
  with Arabic normalization.
- Retrieval and answer evaluation (hit rate, answer relevancy) on a set of real CSR questions.
