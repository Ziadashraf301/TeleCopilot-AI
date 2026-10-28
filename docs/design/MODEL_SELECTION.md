# Model Selection — 5 roles

TeleCopilot needs **five open models**. All come from the **Hugging Face Hub** (huggingface.co), the main public
registry for open model weights, datasets and leaderboards. Selection happens in **M3 (S08-00)**, after the data
work in M2, so candidates are scored on **our own Egyptian test sets**, not only on public leaderboards.

| Role | Used for | Runs where (Stage A) |
|---|---|---|
| 1. **LLM** | Understanding the customer, drafting grounded replies, tool calling | llama.cpp on the 4 GB GPU (GGUF Q4) |
| 2. **Embedding** | Turning text into vectors for search | CPU |
| 3. **Reranker** | Re-ordering the top search results | CPU |
| 4. **ASR** (speech-to-text) | Calls, recordings, WhatsApp voice notes | GPU or CPU (int8) |
| 5. **Vision / OCR** | Reading scanned and Arabic PDFs, images, tables in the KB pipeline | Offline batch job (GPU when the LLM is stopped, or cloud) |

## What "relevant" means for us
Egyptian customers write and speak in **many ways**: Cairene, Alexandrian, Upper-Egypt (Sa'idi) and Delta dialects ·
MSA in formal text · **code-switching** Arabic ↔ English ("el router mesh shaghal") · **Franco/Arabizi** in Latin
letters with numbers (3, 7, 2) · telecom English terms (LOS, ADSL, eSIM). Every candidate is tested on all of these.

Selection criteria, in order:
1. Quality on **our** eval sets (M2 gold sets + dialect/Franco slices + recorded Egyptian speech).
2. Fits the hardware (4 GB VRAM for Stage A; larger variants for Stage B).
3. Licence allows our use (check every model card: Apache-2.0 / MIT / Llama / Gemma / CC-BY-NC etc.).
4. Speed (latency, tokens/s, real-time factor) and download size (internet quota).
5. Community health: recent updates, documentation, GGUF/ONNX availability.

## Candidates (to verify in S08-00 — sizes, licences and scores change often)

### 1. LLM
| Candidate | Why it is interesting | Fit for 4 GB |
|---|---|---|
| **Nile-Chat-4B** (MBZUAI-Paris) | Built for **Egyptian dialect in both Arabic script and Latin script (Arabizi/Franco)**; family also has 12B and MoE 2x4B/3x4B; paper reports the 12B beating Qwen2.5-14B-Instruct on Latin-script benchmarks | 4B at Q4 ≈ 2.5–3 GB → tight but possible; check GGUF exists |
| **NileChat-3B** (UBC-NLP) | 3B adapted for Egyptian and Moroccan communities | Fits |
| **Qwen2.5-3B / Qwen3 small** (Alibaba) | Strong general + multilingual, good tool calling, mature GGUF/vLLM support | Fits |
| Larger for Stage B: Nile-Chat-12B, Qwen 7B/14B, ALLaM-7B, Jais family | Compare quality gain vs cost | Cloud only |
Key test: Egyptian + Franco understanding, **tool-calling reliability** and **JSON validity** (small dialect models may be weaker at tools).

### 2. Embedding
| Candidate | Why | Notes |
|---|---|---|
| **BGE-M3** | Multilingual, strong Arabic, dense + sparse, long inputs | Current plan |
| **Qwen3-Embedding (small sizes)** | High multilingual MTEB scores (larger sizes lead MMTEB) | Check the smallest size on CPU |
| Arabic-specific (Omartificial-Intelligence-Space GATE / Matryoshka models) | Arabic-tuned | Reported scores are STS (similarity), not retrieval — must test |
| multilingual-e5 | Solid baseline | — |
Test: retrieval hit@k on our AR/EN set, plus queries written in Egyptian dialect and Franco against MSA/English documents.

### 3. Reranker
| Candidate | Why |
|---|---|
| **bge-reranker-v2-m3** | Multilingual, pairs with BGE-M3 |
| Qwen3-Reranker (small) | Newer, multilingual |
| Arabic-specific rerankers (search the Hub) | Few exist; public evidence is thin |
Test: hit@3 gain over no rerank, and CPU latency.

### 4. ASR (speech-to-text)
| Candidate | Why | Notes |
|---|---|---|
| **Cohere Transcribe Arabic** (Cohere Labs, July 2026) | Reported lowest average WER (25.87) among open models on the **Open Universal Arabic ASR Leaderboard** (MSA, Egyptian, Gulf, Levantine, Maghrebi) | Verify size, licence, runtime |
| **Whisper fine-tuned on Egyptian** (e.g. MAdel121 whisper-small/medium-egy, whisper-large-v3 Egyptian LoRA) | Egyptian-specific; small fits locally | Self-reported WER on different test sets — not comparable; must test |
| **faster-whisper small / turbo / large-v3** | Robust baseline, code-switching with English, fast int8 | Current plan |
| wav2vec2 Egyptian models | Reported call-centre WER ~19% (self-reported) | Check |
Test: our 40–60 recorded Egyptian calls/voice notes from different regions, with code-switching → WER/CER, plus real-time factor.

### 5. Vision / OCR
| Candidate | Why | Notes |
|---|---|---|
| **QARI-OCR** (Qwen2-VL-2B, Arabic-tuned) | Small; reported WER 0.16 / CER 0.061 on Arabic print | 2B may fit 4 GB in 4-bit; batch only |
| Qwen2.5-VL-7B Arabic OCR fine-tunes (e.g. arabic-ocr-qwen2.5-vl, DIMI-Arabic-OCR-V2) | Stronger, 7B | Cloud / CPU-slow |
| Classic OCR (Tesseract ara, PaddleOCR, Surya) | Tiny, fast baseline | Weaker on complex layouts |
| Gemini Vision (current) | Strong baseline to compare against | API |
Test: M2 extraction ground truth (CER/WER, number and table retention) on our scanned Arabic PDFs.

## Where the evidence comes from
- **Hugging Face Hub**: model cards (size, licence, training data, reported scores), GGUF/ONNX variants.
- **Leaderboards**: Open Arabic LLM Leaderboard (OALL), Open Universal Arabic ASR Leaderboard (multi-dialect), MTEB
  (embeddings), papers (Nile-Chat, QARI-OCR).
- **Our own evals**: the deciding factor. Public scores are self-reported or measured on other data.

## Hugging Face MCP
Hugging Face runs an official MCP server (`https://huggingface.co/mcp`) for searching models, datasets, Spaces,
papers and docs from Claude Code. Ziad adds it once (needs an interactive login):
`claude mcp add hf-mcp-server -t http "https://huggingface.co/mcp?login"`. In S08-00 the agent uses it to build a
shortlist (filters: task, language `ar`, size, licence, downloads, recent updates) and records every candidate with
its card link here. **Downloads still need Ziad's OK** (data-saver).

## Sources
[Nile-Chat-4B](https://huggingface.co/MBZUAI-Paris/Nile-Chat-4B) · [Nile-Chat-12B](https://huggingface.co/MBZUAI-Paris/Nile-Chat-12B) ·
[Nile-Chat paper](https://arxiv.org/pdf/2507.04569) · [NileChat-3B (UBC-NLP)](https://huggingface.co/UBC-NLP/NileChat-3B) ·
[Open Universal Arabic ASR Leaderboard paper](https://arxiv.org/abs/2412.13788v1) · [Cohere Transcribe Arabic](https://huggingface.co/blog/CohereLabs/cohere-transcribe-arabic-07-2026-release) ·
[whisper-small-egyptian-arabic](https://huggingface.co/MAdel121/whisper-small-egyptian-arabic) · [whisper-medium-egy](https://huggingface.co/MAdel121/whisper-medium-egy) ·
[whisper-large-v3-egyptian-arabic](https://huggingface.co/AbdelrahmanHassan/whisper-large-v3-egyptian-arabic) · [wav2vec2-egyptian-arabic](https://huggingface.co/Yousef1258852/wav2vec2-egyptian-arabic) ·
[Arabic GATE/Matryoshka embeddings](https://huggingface.co/collections/Omartificial-Intelligence-Space/arabic-matryoshka-and-gate-embedding-models) ·
[QARI-OCR paper](https://huggingface.co/papers/2506.02295) · [arabic-ocr-qwen2.5-vl](https://huggingface.co/mo1998/arabic-ocr-qwen2.5-vl) · [DIMI-Arabic-OCR-V2](https://huggingface.co/AhmedZaky1/DIMI-Arabic-OCR-V2) ·
[Arabic manuscript OCR study](https://arxiv.org/html/2608.22366v1) · [OALL](https://www.tii.ae/node/3080) · [HF MCP docs](https://huggingface.co/docs/hub/en/hf-mcp-server)
