"""
evals/extraction/metrics.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Word-level, ROUGE-L, entity, structure, and aggregation metrics.

Incorporates:
  - Arabic morphological normalization (no heavy NLP dependency)
  - Word Recall / Precision / F1
  - ROUGE-L via Longest Common Subsequence (zero extra dependencies)
  - Critical entity and number/percentage retention
  - Section Order score via Kendall's tau
  - Table cell and media retention
  - Micro and Macro aggregation
  - Per-document-type (html, xml, docx, pdf) breakdowns
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field

# ---------------------------------------------------------------------------
# Arabic Normalisation & Tokenisation (Fix 1)
# ---------------------------------------------------------------------------


def normalize_arabic(text: str) -> str:
    """
    Lightweight Arabic morphological normalisation (no external NLP library).
    Steps:
      1. Strip diacritics (harakat / tashkeel)
      2. Normalise alif variants  →  ا
      3. Normalise teh marbuta  ة  →  ه
      4. Normalise waw with hamza  ؤ  →  و
      5. Normalise yeh with hamza  ئ  →  ي
    """
    # 1. Strip diacritics U+064B – U+065F, U+0670
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    # 2. Alif variants → bare alif
    text = re.sub(r"[أإآٱ]", "ا", text)
    # 3. Teh marbuta → ha
    text = text.replace("ة", "ه")
    # 4. Waw hamza → waw
    text = text.replace("ؤ", "و")
    # 5. Yeh hamza → yeh
    text = text.replace("ئ", "ي")
    return text


def tokenize(text: str) -> list[str]:
    """
    Tokenise text that may contain Arabic, English, numbers, and percentages.
    Normalises Arabic before splitting.
    Returns lowercased token list.
    """
    text = normalize_arabic(text)
    # Match Arabic words, Latin words, or numeric tokens (with optional % or EGP suffix)
    tokens = re.findall(r"[\u0621-\u064A]+|[a-zA-Z]+|\d+(?:\.\d+)?%?", text)
    return [t.lower() for t in tokens]


def token_set(text: str) -> set[str]:
    return set(tokenize(text))


# ---------------------------------------------------------------------------
# ROUGE-L via LCS  (Fix 5)
# ---------------------------------------------------------------------------


def _lcs_length(a: list[str], b: list[str]) -> int:
    """Dynamic programming LCS length — O(len(a) × len(b))."""
    m, n = len(a), len(b)
    # Space-optimised: only keep two rows
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(curr[j - 1], prev[j])
        prev, curr = curr, [0] * (n + 1)
    return prev[n]


def rouge_l(extracted: str, ground_truth: str) -> float:
    """
    ROUGE-L F1 score based on Longest Common Subsequence.
    Handles Arabic normalisation internally.
    Returns float in [0.0, 1.0].
    """
    a = tokenize(extracted)
    b = tokenize(ground_truth)
    if not a or not b:
        return 0.0
    lcs = _lcs_length(a, b)
    precision = lcs / len(a)
    recall = lcs / len(b)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# ---------------------------------------------------------------------------
# Critical Entity Extraction
# ---------------------------------------------------------------------------

# Regexes for telecom-critical entities
_ENTITY_PATTERNS: dict[str, str] = {
    "percentages": r"\b\d{1,3}(?:\.\d+)?%",  # 99.99%, 25%
    "egp_prices": r"\b\d+(?:\.\d+)?\s*(?:EGP|ج\.م)",  # 150 EGP, 5.00 EGP
    "phone_numbers": r"\b1[0-9]{7,10}\b|\b19\d{3}\b",  # 19777, 01xxxxxxxxx
    "sla_codes": r"\bSLA-[A-Z]+\b",  # SLA-DIAMOND, SLA-GOLD
    "circuit_ids": r"\bCORP-CIRC-\d{4}\b",  # CORP-CIRC-0001
    "doc_ids": r"\bPOL-[A-Z]+-\d{4}-V\d+\b",  # POL-SIM-2026-V4
    "speeds": r"\b\d+\s*(?:Mbps|Gbps|GB|MB)\b",  # 100 Mbps, 140GB
    "durations": r"\b\d+\s*(?:days?|hours?|minutes?|months?|years?)\b",
}


def extract_critical_entities(text: str) -> dict[str, list[str]]:
    """Extract all telecom-critical entity occurrences from text."""
    results: dict[str, list[str]] = {}
    for category, pattern in _ENTITY_PATTERNS.items():
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            results[category] = list(set(matches))
    return results


def entity_retention(extracted: str, ground_truth: str) -> dict[str, float]:
    """
    Per-category entity recall: how many unique GT entities appear in extracted text.
    Returns dict of category → recall (0.0–1.0).
    """
    gt_entities = extract_critical_entities(ground_truth)
    ex_entities = extract_critical_entities(extracted)
    scores: dict[str, float] = {}
    for cat, gt_vals in gt_entities.items():
        gt_set = set(v.lower() for v in gt_vals)
        ex_set = set(v.lower() for v in ex_entities.get(cat, []))
        scores[cat] = len(gt_set & ex_set) / len(gt_set) if gt_set else 1.0
    return scores


def overall_entity_recall(extracted: str, ground_truth: str) -> float:
    """Macro average entity recall across all categories present in GT."""
    per_cat = entity_retention(extracted, ground_truth)
    if not per_cat:
        return 1.0
    return sum(per_cat.values()) / len(per_cat)


# ---------------------------------------------------------------------------
# Section Order Score — Kendall's tau  (Fix 3)
# ---------------------------------------------------------------------------


def kendall_tau_order(extracted_titles: list[str], gt_titles: list[str]) -> float:
    """
    Measure section order preservation as Kendall's tau.
    Aligns extracted titles to GT titles via best-substring match, then computes tau.
    Returns float in [-1.0, 1.0]; 1.0 = perfect order, -1.0 = fully reversed.
    """
    if not extracted_titles or not gt_titles:
        return 1.0  # No sections to compare → neutral

    # Build rank mapping: for each GT title, find its best-matching extracted index
    def best_match_idx(title: str, candidates: list[str]) -> int:
        title_toks = set(tokenize(title))
        best_score, best_idx = -1.0, 0
        for i, cand in enumerate(candidates):
            cand_toks = set(tokenize(cand))
            union = title_toks | cand_toks
            score = len(title_toks & cand_toks) / len(union) if union else 0.0
            if score > best_score:
                best_score, best_idx = score, i
        return best_idx

    # Get extracted rank for each GT section
    ranks = [best_match_idx(t, extracted_titles) for t in gt_titles]

    # Compute Kendall's tau from the rank sequence
    n = len(ranks)
    if n < 2:
        return 1.0
    concordant = discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            diff = ranks[j] - ranks[i]
            if diff > 0:
                concordant += 1
            elif diff < 0:
                discordant += 1
    total_pairs = n * (n - 1) / 2
    return (concordant - discordant) / total_pairs if total_pairs > 0 else 1.0


# ---------------------------------------------------------------------------
# Table & Media Retention
# ---------------------------------------------------------------------------


def table_cell_retention(extracted_cells: int, gt_cells: int) -> float:
    if gt_cells == 0:
        return 1.0
    return min(extracted_cells / gt_cells, 1.0)


def media_retention(extracted_media: int, gt_media: int) -> float:
    if gt_media == 0:
        return 1.0
    return min(extracted_media / gt_media, 1.0)


# ---------------------------------------------------------------------------
# Per-File Extraction Metrics Dataclass
# ---------------------------------------------------------------------------


@dataclass
class ExtractionMetrics:
    """All quality metrics for one extracted document vs its ground truth."""

    file_name: str
    file_type: str  # html | xml | docx | pdf

    # Token-level
    word_recall: float = 0.0
    word_precision: float = 0.0
    word_f1: float = 0.0
    rouge_l_score: float = 0.0

    # Entity-level
    entity_recall_overall: float = 0.0
    entity_recall_per_category: dict[str, float] = field(default_factory=dict)

    # Structure-level
    section_order_tau: float = 1.0
    table_cell_retention: float = 1.0
    media_retention: float = 1.0

    # Counts for micro aggregation
    gt_token_count: int = 0
    extracted_token_count: int = 0
    gt_table_cells: int = 0
    extracted_table_cells: int = 0
    gt_media_count: int = 0
    extracted_media_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def compute_all_metrics(
    extracted_text: str,
    ground_truth_text: str,
    file_name: str,
    file_type: str,
    extracted_section_titles: list[str] | None = None,
    gt_section_titles: list[str] | None = None,
    extracted_table_cells: int = 0,
    gt_table_cells: int = 0,
    extracted_media_count: int = 0,
    gt_media_count: int = 0,
) -> ExtractionMetrics:
    """
    Compute the full suite of metrics for one file.
    Returns a populated ExtractionMetrics object.
    """
    gt_tokens = tokenize(ground_truth_text)
    ex_tokens = tokenize(extracted_text)

    gt_set = set(gt_tokens)
    ex_set = set(ex_tokens)

    intersection = gt_set & ex_set
    recall = len(intersection) / len(gt_set) if gt_set else 1.0
    precision = len(intersection) / len(ex_set) if ex_set else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    rl = rouge_l(extracted_text, ground_truth_text)
    er = overall_entity_recall(extracted_text, ground_truth_text)
    er_per_cat = entity_retention(extracted_text, ground_truth_text)

    tau = kendall_tau_order(
        extracted_section_titles or [],
        gt_section_titles or [],
    )
    tcr = table_cell_retention(extracted_table_cells, gt_table_cells)
    mr = media_retention(extracted_media_count, gt_media_count)

    return ExtractionMetrics(
        file_name=file_name,
        file_type=file_type,
        word_recall=round(recall, 4),
        word_precision=round(precision, 4),
        word_f1=round(f1, 4),
        rouge_l_score=round(rl, 4),
        entity_recall_overall=round(er, 4),
        entity_recall_per_category={k: round(v, 4) for k, v in er_per_cat.items()},
        section_order_tau=round(tau, 4),
        table_cell_retention=round(tcr, 4),
        media_retention=round(mr, 4),
        gt_token_count=len(gt_tokens),
        extracted_token_count=len(ex_tokens),
        gt_table_cells=gt_table_cells,
        extracted_table_cells=extracted_table_cells,
        gt_media_count=gt_media_count,
        extracted_media_count=extracted_media_count,
    )


# ---------------------------------------------------------------------------
# Micro / Macro Aggregation & Per-Type Breakdown
# ---------------------------------------------------------------------------


@dataclass
class AggregatedMetrics:
    """Aggregated metrics over a set of documents."""

    label: str  # e.g. "ALL", "html", "xml", "docx", "pdf"
    n_documents: int = 0

    # Macro (unweighted mean per document)
    macro_word_recall: float = 0.0
    macro_word_precision: float = 0.0
    macro_word_f1: float = 0.0
    macro_rouge_l: float = 0.0
    macro_entity_recall: float = 0.0
    macro_section_order_tau: float = 0.0
    macro_table_retention: float = 0.0
    macro_media_retention: float = 0.0

    # Micro (token-count weighted across corpus)
    micro_word_recall: float = 0.0
    micro_word_precision: float = 0.0
    micro_word_f1: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def aggregate_micro_macro(
    metrics_list: list[ExtractionMetrics],
    label: str = "ALL",
) -> AggregatedMetrics:
    """
    Compute Macro (unweighted) and Micro (token-weighted) aggregates
    over a list of ExtractionMetrics.
    """
    n = len(metrics_list)
    if n == 0:
        return AggregatedMetrics(label=label)

    # ----- Macro -----
    def _macro(attr: str) -> float:
        return sum(getattr(m, attr) for m in metrics_list) / n

    # ----- Micro word recall/precision/f1 -----
    total_gt = sum(m.gt_token_count for m in metrics_list)
    total_ex = sum(m.extracted_token_count for m in metrics_list)

    # Approximate: micro recall ≈ weighted average of recalls by GT size
    micro_recall = sum(m.word_recall * m.gt_token_count for m in metrics_list) / total_gt if total_gt else 0.0
    micro_precision = (
        sum(m.word_precision * m.extracted_token_count for m in metrics_list) / total_ex if total_ex else 0.0
    )
    micro_f1 = (
        2 * micro_recall * micro_precision / (micro_recall + micro_precision)
        if (micro_recall + micro_precision) > 0
        else 0.0
    )

    return AggregatedMetrics(
        label=label,
        n_documents=n,
        macro_word_recall=round(_macro("word_recall"), 4),
        macro_word_precision=round(_macro("word_precision"), 4),
        macro_word_f1=round(_macro("word_f1"), 4),
        macro_rouge_l=round(_macro("rouge_l_score"), 4),
        macro_entity_recall=round(_macro("entity_recall_overall"), 4),
        macro_section_order_tau=round(_macro("section_order_tau"), 4),
        macro_table_retention=round(_macro("table_cell_retention"), 4),
        macro_media_retention=round(_macro("media_retention"), 4),
        micro_word_recall=round(micro_recall, 4),
        micro_word_precision=round(micro_precision, 4),
        micro_word_f1=round(micro_f1, 4),
    )


def aggregate_per_type(
    metrics_list: list[ExtractionMetrics],
) -> dict[str, AggregatedMetrics]:
    """
    Break down metrics by document type: html, xml, docx, pdf.
    Also includes an 'ALL' entry.
    """
    groups: dict[str, list[ExtractionMetrics]] = defaultdict(list)
    for m in metrics_list:
        groups[m.file_type].append(m)
    groups["ALL"] = metrics_list

    return {label: aggregate_micro_macro(items, label=label) for label, items in groups.items()}
