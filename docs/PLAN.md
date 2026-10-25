# TeleCopilot AI v2 — Plan

Goal: turn the RAG demo into an **agent-assist product** a small contact centre could run: CSRs work inside an
agent desktop (queue, conversations, customer 360, tickets), and the copilot listens to each conversation, pulls
customer context through tools, remembers the customer, and drafts replies, actions and wrap-up notes.
Everything runs on **open-source models** that we deploy ourselves.

The feasibility study (Arabic/English) is [docs/TeleCopilot_v2_Feasibility.pdf](TeleCopilot_v2_Feasibility.pdf).
Where this file and the PDF disagree, **this file wins** (decisions below were taken after the PDF).

---

## Decisions (2026-10-25)
| Topic | Decision |
|---|---|
| Strategy | **Local first.** Everything must work on the dev laptop (RTX 2050, 4 GB) before any cloud GPU. Measure quality, business KPIs and max capacity there = the **baseline**. Then free cloud GPUs → bigger models → evaluate and load test again |
| UI | **Reflex** (Python full-stack). Keeps the whole project in Python |
| WhatsApp | **Simulator first**, built to the same webhook/message format as Meta's WhatsApp Cloud API, so switching to the real API is an adapter swap. Real API only with its free test number |
| Voice | **Both**: live calls (browser WebRTC softphone, no paid phone numbers) and recordings / WhatsApp voice notes |
| Budget | **$0 first, max $10 total**, spent only after free tiers are used up |
| Delivery | **One milestone at a time** in the order of [SPRINTS.md](SPRINTS.md): restructure → UI + CRM data → KB & data pipelines → models → … Each service fully done (built, evaluated, KPIs, load tested) before the next |
| Data before models | The KB pipeline and data quality are built and measured before any model is chosen |
| Design first | Every milestone starts with a design pack (diagrams, ERD, explained decisions) approved by Ziad |
| UI style | Bilingual Arabic + English, RTL for Arabic, based on the Figma "Chat UI" reference — [design/ui-reference/STYLE_GUIDE.md](design/ui-reference/STYLE_GUIDE.md) |
| Code quality | SOLID, DRY, KISS/YAGNI, no anti-patterns, ruff — [design/CODE_GUIDELINES.md](design/CODE_GUIDELINES.md); a report per ticket |

## Scope
TeleCopilot is a **learning + portfolio** project: an agent-assist copilot for **one telecom contact centre**
(single company).

## Stages
| Stage | Hardware | Models | Output |
|---|---|---|---|
| **A. Local baseline** | Laptop: RTX 2050 4 GB + CPU | Five models (LLM, embedding, reranker, ASR, vision/OCR) chosen in M3 from the Hugging Face Hub on our Egyptian dialect / Franco evals — candidates in [design/MODEL_SELECTION.md](design/MODEL_SELECTION.md). LLM on llama.cpp (GGUF Q4), embed/rerank on CPU | Quality + KPI + capacity report per service: "baseline v1" |
| **B. Free cloud GPU** | Kaggle (T4×2 / P100, ~30 GPU-h/week), Google Colab free (T4, short sessions), Modal / Lightning free credits | Qwen2.5-7B/14B AWQ on vLLM, whisper large-v3 | Same eval + load test, side-by-side with Stage A |
| **C. Paid (≤ $10)** | RunPod / Vast spot, a few hours | Qwen 32B AWQ, open LLM judge | Final benchmark table only |

Free-tier notes (verify current limits before relying on them): Kaggle/Colab sessions are temporary and not meant
to host a public service, so in Stage B the model server runs for a session and we expose it through a tunnel only
for the eval and load-test runs. Free API hosts of open models (Groq, OpenRouter free models, HF Inference) can
serve as the "bigger open model" comparison without deploying anything.

Local VRAM budget (4 GB): LLM 3B Q4 ≈ 2.0–2.5 GB incl. KV cache · whisper small int8 ≈ 0.5 GB · embeddings/rerank
on CPU by default. Only one GPU-heavy service is loaded at a time if memory runs out.

## How every service is measured
Each service ships with three reports in `evals/reports/<service>/`: **quality**, **performance**, **business KPI**.

| Service | Quality metrics | Performance metrics | Business KPI it feeds |
|---|---|---|---|
| Channels (simulator, web chat, tickets) | Message delivery, ordering, no loss | msgs/s, p95 delivery latency, WebSocket connections | Queue wait time, SLA breaches |
| KB ingestion | Extraction F1 / ROUGE-L, number retention (existing metrics) | docs/min, OCR s/page | KB freshness (days since update) |
| Retrieval (embed + hybrid + rerank) | hit@3, MRR, context recall/precision, AR vs EN | p50/p95 latency, QPS | Policy lookup time |
| LLM generation | Faithfulness, answer relevancy, JSON validity, dialect match | Tokens/s, time-to-first-token, concurrent streams | Draft acceptance rate |
| Agent + tools | Tool selection + argument accuracy, task success | Steps/turn, p95 turn latency | AHT reduction, FCR proxy |
| Memory | Recall of correct customer facts, false-memory rate | Lookup latency | Repeat-contact detection rate |
| Speech (STT) | WER / CER on Egyptian Arabic, diarisation accuracy | Real-time factor, live-call latency | After-call work time |
| Summaries / wrap-up | Coverage of key facts, correct disposition code | Latency | ACW seconds saved |

Business KPIs (measured on the simulator with scripted scenarios, baseline = CSR using KB search only):
**AHT**, **ACW time**, **FCR proxy** (resolved without follow-up), **suggestion acceptance rate**, **escalation rate**,
**SLA breach rate**, **cost per contact** (GPU-hours or $ per 1k contacts).

Load testing: **Locust** with scripted CSR + customer behaviour. For each stage report the **max concurrent CSRs**
at which p95 copilot latency stays < 4 s and error rate < 1%. That number is the stated capacity of the stage.

## Build order (agreed 2026-10-25; details in SPRINTS.md)
| # | Milestone | Done when |
|---|---|---|
| M0 | Restructure & foundation | v1 unchanged on the new package layout, Postgres/Redis ready |
| M1 | Agent desktop + CRM data (Reflex, Ziad's design) | CSR works a ticket end to end on synthetic CRM data |
| M2 | Knowledge base & data pipelines (data before models) | Data-quality + extraction reports; ≥ 150 verified questions |
| M3 | Model providers + retrieval baseline (local) | Retrieval reports; local config chosen |
| M4 | Generation baseline (local) | Faithfulness, JSON validity, capacity |
| M5 | Channels | 3 channels in one inbox |
| M6 | Agent + tools + memory | Tool accuracy; AHT simulation |
| M7 | Speech (voice notes, recordings, live calls) | WER; live latency |
| M8 | MCP + hardening | Checklist ≥ 90% |
| M9 | Stage A report | Published |
| M10 | Stage B / C | Side-by-side benchmark |
Every milestone starts with a design pack (diagrams, ERD, explained decisions) approved by Ziad.

## Channels
| Channel | Approach | Cost |
|---|---|---|
| Tickets / email / web form | Own tables; form on a sample landing page | Free |
| WhatsApp | Simulator using the Cloud API webhook + message JSON format; later the real API with Meta's free test number (a handful of verified recipient numbers; customer-initiated service conversations free in the 24 h window — verify current limits) | Free |
| Web chat | Own widget (WebSocket), bot first then human handover | Free |
| Voice notes / recordings | Upload or WhatsApp audio → STT | Free |
| Live calls | Browser softphone over WebRTC with self-hosted LiveKit (customer simulator in a second browser tab). No real phone numbers | Free |

## Knowledge base (real data, Arabic + English)
Public sources: te.eg (WE), Vodafone Egypt, Orange Egypt, e& Egypt (offers, FAQs, T&Cs, roaming), NTRA consumer
protection and QoS rules (Arabic PDFs, some scanned), router/ONT manuals (Huawei, ZTE, TP-Link). Respect robots.txt,
snapshot each source with a date, cite it. Formats: HTML, text PDF, scanned PDF, DOCX, XLSX, XML, FAQ JSON.
Synthetic (clearly labelled): CRM customers (Faker `ar_EG`), bills, ticket history, conversations in Egyptian Arabic /
Franco-Arabic / English, our own recorded calls. Each synthetic set has a hand-checked eval slice.

## Target layout (ADR-1 in SPRINTS.md)
```
src/telecopilot/      one installable package
  api/                FastAPI routers, schemas, websockets
  config/ core/       settings, logging, tracing, errors, security
  kb/                 extractors, chunkers, indexing, retrieval (today's ingestion + repositories)
  llm/                providers: llamacpp, vllm, gemini; embed/rerank: local, tei, cohere
  crm/                customers, plans, bills, tickets (Postgres)
  channels/           whatsapp (simulator + cloud adapter), webchat, email, voice
  speech/             stt, vad, diarisation, live-call bridge
  agent/              graph, tools, memory, prompts, guardrails
  mcp_servers/        crm, kb, tickets
  worker/             background jobs: ingestion, STT, summaries
apps/web/             Reflex agent desktop
evals/                datasets, harness, metrics, load tests (Locust), reports
deploy/               compose profiles (local-gpu, api-fallback, cloud-gpu), llama.cpp / vLLM / TEI configs
data/                 raw KB, synthetic, ground_truth
```

## Production checklist (small scale)
Auth + roles · PII masking in logs and prompts · audit log of every AI suggestion and CSR action · human approval for
every write action · rate limits, locked-down CORS · Postgres migrations + backups · job queue · health/readiness
probes · timeouts, retries, model fallback · tracing + metrics + alerts · eval regression gate in CI · load-tested
capacity per stage · runbook.

## Still open
- Final model choices for the five roles (M3, S08-00), and the download list Ziad approves (S08-03).
- Whether int8/ONNX variants can replace full-size embedding/reranker weights to save bandwidth and RAM.
