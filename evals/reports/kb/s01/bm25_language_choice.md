# BM25 language setting (S01-11)

Question: which FastEmbed `Qdrant/bm25` setting works best for our mixed Arabic + English corpus?
BM25 only (no dense, no rerank), Qdrant sparse vector with `modifier=IDF`, in-memory Qdrant, the 651 chunks of the
v1 index (dumped before the re-index).

## How FastEmbed BM25 treats text
- Tokenizer: lower-case, every non-`\w` character becomes a space. Arabic letters are `\w`; Arabic diacritics are
  not, so a diacritic **inside** a word splits it (`مُحَمَّد` → `م ح م د`). Corpus check: 122 chunks contain diacritics,
  **0 mid-word** (all word-final, which are simply dropped) → no impact on our data today.
- Stemmer: one Snowball stemmer per model. `english` leaves Arabic untouched; `arabic` leaves English untouched.
  Examples: `english`: activation/activated → `activ`, but `الباقات` / `باقة` stay different. `arabic`: `الباقات`,
  `باقة` → `باق`, but `activation` / `activated` stay different.
- Arabic stemmer quirk: `إلغاء` → `الغاء` but hamza-less `الغاء` → `غاء` (Egyptian typing often omits hamza).
- Stopwords: one list per language (english 936 B, arabic 759 words).

## Configurations
| Name | Stemmer | Stopwords |
|---|---|---|
| english | English Snowball for all tokens | English |
| arabic | Arabic Snowball for all tokens | Arabic |
| bilingual | Arabic Snowball for Arabic-script tokens, English for the rest | English ∪ Arabic |
| bilingual+normalize | as bilingual, plus alef forms → ا and diacritics/tatweel removed before embedding | English ∪ Arabic |

## Test 1 — questions with a known source document (hit = right file in top-k)
34 queries: the 13 RAG eval questions, hamza-stripped copies of the 3 Arabic ones, and 19 keyword queries (EN,
AR, Egyptian spelling, mixed).

| Config | EN hit@1 (19) | AR hit@1 (8) | AR-Egyptian hit@1 (4) | Mixed hit@1 (3) | All hit@1 / hit@3 (34) | MRR@3 |
|---|---|---|---|---|---|---|
| english | 17 | 3 | 2 | 1 | 23 / 25 | 0.701 |
| arabic | 16 | 4 | 2 | 1 | 23 / 24 | 0.686 |
| **bilingual** | **17** | **4** | 2 | 1 | **24 / 25** | **0.716** |
| bilingual+normalize | 17 | 4 | 2 | 1 | 24 / 25 | 0.716 |

Most Arabic misses are **not** a BM25 problem: `arabic_family_bundles_migration.pdf` and
`arabic_router_diagnostics_scan.pdf` contain **English** text (0% Arabic letters in both the index and the
human-verified ground truth), despite their names and Arabic catalogue titles, so an Arabic keyword query cannot
match them lexically (that is the dense model's job). The only genuinely Arabic source is
`arabic_enterprise_sla_contracts.xml` (124 chunks).

## Test 2 — Arabic surface forms (stemming robustness)
60 random Arabic chunks; query = their 3 rarest Arabic words, in three forms; hit = that exact chunk in top 3.

| Config | exact words | definite article toggled (`ال`) | hamza stripped |
|---|---|---|---|
| english | 8/60 | **1/60** | 6/60 |
| arabic | 8/60 | 8/60 | 8/60 |
| **bilingual** | 8/60 | 8/60 | 8/60 |
| bilingual+normalize | 8/60 | 8/60 | 8/60 |

(Absolute numbers are low because the SLA chunks are near-identical contract rows; the comparison between configs
is what matters: with `english`, a query that adds or drops `ال` almost never finds the chunk.)

## Decision
**bilingual** — it equals the better single-language setting on every slice (English inflections like `arabic`
can't do, Arabic morphology like `english` can't do) and is best overall. `normalize` adds nothing measurable on
this corpus, so it is left out (YAGNI); Arabic normalisation belongs to the M2 cleaning stage (S06-02), where it
will apply to all of extraction, BM25 and evaluation at once.
