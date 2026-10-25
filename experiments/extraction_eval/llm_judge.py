"""
experiments/extraction_eval/llm_judge.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Gemini LLM-as-a-Judge for extraction quality evaluation.

Features:
  - Sliding window chunking for large documents (Fix 4)
  - Telecom-specific 4-dimension rubric
  - Multimodal judging (text + page images for PDF/DOCX)
  - Structured JSON output parsing with fallback heuristic judge
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Judge Result Dataclass
# ---------------------------------------------------------------------------


@dataclass
class JudgeResult:
    """Structured output from Gemini LLM-as-a-Judge."""

    file_name: str
    file_type: str

    # 4-dimension rubric scores (0–100)
    completeness_score: float = 0.0  # Were all clauses, rules, prices, tables preserved?
    structure_fidelity_score: float = 0.0  # Quality of heading hierarchy, tables, ordering
    noise_hallucination_score: float = 0.0  # Cleanliness (100 = no noise/hallucination)
    arabic_fidelity_score: float = 0.0  # Arabic/multilingual correctness

    overall_score: float = 0.0
    verdict: str = "UNKNOWN"  # PASS | CONDITIONAL_PASS | FAIL

    missing_critical_elements: list[str] = field(default_factory=list)
    noise_artifacts: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Provenance
    chunks_evaluated: int = 1
    used_vision: bool = False
    used_fallback_heuristic: bool = False
    evaluation_note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def verdict_emoji(self) -> str:
        return {"PASS": "✅", "CONDITIONAL_PASS": "⚠️", "FAIL": "❌"}.get(self.verdict, "❓")


# ---------------------------------------------------------------------------
# Telecom Evaluation Rubric Prompt
# ---------------------------------------------------------------------------

TELECOM_RUBRIC_PROMPT = """\
You are an expert Telecom Document Extraction Quality Auditor.
Your task is to evaluate the quality of an extracted document against its ground truth.

## Document Details
- File: {file_name}
- Format: {file_type}
- Chunk: {chunk_label}

## Ground Truth (Reference — Gold Standard)
```
{ground_truth_chunk}
```

## Extracted Text (System Output — Under Evaluation)
```
{extracted_chunk}
```

## Evaluation Rubric (Score 0–100 per dimension)

1. **Completeness Score (0–100)**
   - 90–100: All critical policy clauses, prices (EGP/ج.م), SLA percentages, deadlines, phone numbers, table data are present.
   - 70–89: Minor omissions of secondary information; no critical business rules missing.
   - 50–69: Notable gaps — missing 1–2 important clauses, rates, or table rows.
   - 0–49: Major information loss — sections skipped, tables missing, critical values dropped.

2. **Structure Fidelity Score (0–100)**
   - 90–100: Heading hierarchy, section order, table grids, and bullet structure faithfully preserved.
   - 70–89: Minor structural displacement (e.g. table at end instead of inline); order mostly correct.
   - 50–69: Sections shuffled or merged; table headers missing; notable order inversions.
   - 0–49: Structure largely destroyed; content is an unstructured blob.

3. **Noise & Hallucination Score (0–100)**
   - 90–100: Clean output with no CSS artifacts, HTML tags, XML brackets, or invented content.
   - 70–89: Minor boilerplate noise (e.g. CSS class names, one stray tag).
   - 50–69: Noticeable noise; some content may be generated/hallucinated.
   - 0–49: Heavy noise, repeated boilerplate, or significant hallucinated content.

4. **Arabic / Multilingual Fidelity Score (0–100)**
   - 90–100: Arabic text correctly preserved, RTL terms accurate, no scrambled Unicode.
   - 70–89: Mostly correct; minor garbling of Arabic phrases or diacritics.
   - 50–69: Partial Arabic loss; some Egyptian dialect terms or phone codes garbled.
   - 0–49: Arabic content largely corrupted, reversed, or replaced with question marks.

## Output Format
Respond ONLY with a valid JSON object following this exact schema:
```json
{{
  "completeness_score": <int 0-100>,
  "structure_fidelity_score": <int 0-100>,
  "noise_hallucination_score": <int 0-100>,
  "arabic_fidelity_score": <int 0-100>,
  "overall_score": <int 0-100>,
  "verdict": "<PASS|CONDITIONAL_PASS|FAIL>",
  "missing_critical_elements": ["<element1>", "<element2>"],
  "noise_artifacts": ["<artifact1>"],
  "recommendations": ["<specific actionable recommendation for the extractor code>"]
}}
```
Rules:
- overall_score = weighted average: (completeness × 0.40) + (structure × 0.25) + (noise × 0.20) + (arabic × 0.15)
- PASS if overall_score >= 80
- CONDITIONAL_PASS if 60 <= overall_score < 80
- FAIL if overall_score < 60
- missing_critical_elements: specific telecom terms, clause numbers, percentages, IDs missing from extraction.
- recommendations: reference specific extractor file/function if applicable (e.g. "xml_extractor.py — capture elem.attrib on self-closing tags").
"""


# ---------------------------------------------------------------------------
# Tokeniser (for chunking, reusing metrics logic)
# ---------------------------------------------------------------------------


def _simple_tokenize(text: str) -> list[str]:
    """Simple word tokeniser for chunk size estimation."""
    return re.findall(r"\S+", text)


def _chunk_text(text: str, chunk_size: int = 3500, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping token-count-based chunks.
    Returns list of text chunk strings.
    """
    tokens = _simple_tokenize(text)
    if len(tokens) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(" ".join(chunk_tokens))
        if end == len(tokens):
            break
        start = end - overlap
    return chunks


# ---------------------------------------------------------------------------
# JSON Response Parser
# ---------------------------------------------------------------------------


def _parse_judge_response(response_text: str) -> dict[str, Any]:
    """Extract and parse JSON from Gemini response text."""
    # Try direct parse first
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    # Try extracting JSON block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding raw JSON object
    match = re.search(r"\{[^{}]+\}", response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


# ---------------------------------------------------------------------------
# Heuristic Fallback Judge (Fix 4 — offline / API key absent)
# ---------------------------------------------------------------------------


def _heuristic_judge(
    extracted_text: str,
    ground_truth_text: str,
    file_name: str,
    file_type: str,
) -> JudgeResult:
    """
    Deterministic fallback judge when Gemini API is unavailable.
    Uses word overlap, entity presence, and noise heuristics.
    """
    from .metrics import extract_critical_entities, tokenize

    gt_tokens = set(tokenize(ground_truth_text))
    ex_tokens = set(tokenize(extracted_text))
    overlap = gt_tokens & ex_tokens

    recall = len(overlap) / len(gt_tokens) if gt_tokens else 1.0
    completeness = round(min(recall * 110, 100))  # slight boost for normalisation

    # Structure: check section count and basic heading presence
    gt_headings = len(re.findall(r"^#{1,3} ", ground_truth_text, re.MULTILINE))
    ex_headings = len(re.findall(r"^#{1,3} ", extracted_text, re.MULTILINE))
    structure = round(min((ex_headings / max(gt_headings, 1)) * 100, 100))

    # Noise: penalise CSS-like artifacts and HTML tags
    noise_indicators = len(re.findall(r"<[^>]+>|\.container|\.badge|\{[^}]+\}", extracted_text))
    noise = max(0, 100 - noise_indicators * 5)

    # Arabic fidelity: check Arabic char presence ratio
    gt_arabic = len(re.findall(r"[\u0600-\u06FF]", ground_truth_text))
    ex_arabic = len(re.findall(r"[\u0600-\u06FF]", extracted_text))
    arabic = round(min((ex_arabic / max(gt_arabic, 1)) * 100, 100)) if gt_arabic > 0 else 100

    overall = round(completeness * 0.40 + structure * 0.25 + noise * 0.20 + arabic * 0.15)
    verdict = "PASS" if overall >= 80 else ("CONDITIONAL_PASS" if overall >= 60 else "FAIL")

    # Find missing entities
    gt_entities = extract_critical_entities(ground_truth_text)
    ex_entities = extract_critical_entities(extracted_text)
    missing = []
    for cat, vals in gt_entities.items():
        ex_vals = set(v.lower() for v in ex_entities.get(cat, []))
        for v in vals:
            if v.lower() not in ex_vals:
                missing.append(f"[{cat}] {v}")

    return JudgeResult(
        file_name=file_name,
        file_type=file_type,
        completeness_score=float(completeness),
        structure_fidelity_score=float(structure),
        noise_hallucination_score=float(noise),
        arabic_fidelity_score=float(arabic),
        overall_score=float(overall),
        verdict=verdict,
        missing_critical_elements=missing[:10],
        noise_artifacts=[],
        recommendations=["Run with Gemini API key for detailed recommendations."],
        used_fallback_heuristic=True,
        evaluation_note="Heuristic fallback — Gemini API unavailable.",
    )


# ---------------------------------------------------------------------------
# Gemini Judge (main)
# ---------------------------------------------------------------------------


class GeminiJudge:
    """
    Evaluates extraction quality using Gemini LLM-as-a-Judge.
    Implements sliding window for large documents (Fix 4).
    Supports multimodal evaluation (text + page images).
    """

    def __init__(self, gemini_client=None, chunk_size: int = 3500, overlap: int = 200):
        self.gemini_client = gemini_client
        self.chunk_size = chunk_size
        self.overlap = overlap

    def evaluate(
        self,
        extracted_text: str,
        ground_truth_text: str,
        file_name: str,
        file_type: str,
        page_images: list[Any] | None = None,  # PIL Images for visual audit
    ) -> JudgeResult:
        """
        Main evaluation entry point.
        Falls back to heuristic judge if no Gemini client available.
        """
        if self.gemini_client is None:
            return _heuristic_judge(extracted_text, ground_truth_text, file_name, file_type)

        gt_chunks = _chunk_text(ground_truth_text, self.chunk_size, self.overlap)
        ex_chunks = _chunk_text(extracted_text, self.chunk_size, self.overlap)
        n_chunks = max(len(gt_chunks), len(ex_chunks))

        chunk_results: list[dict[str, Any]] = []
        chunk_weights: list[int] = []

        for i in range(n_chunks):
            gt_chunk = gt_chunks[i] if i < len(gt_chunks) else ""
            ex_chunk = ex_chunks[i] if i < len(ex_chunks) else ""
            chunk_label = f"{i + 1}/{n_chunks}" if n_chunks > 1 else "full document"

            prompt = TELECOM_RUBRIC_PROMPT.format(
                file_name=file_name,
                file_type=file_type,
                chunk_label=chunk_label,
                ground_truth_chunk=gt_chunk[:4000],
                extracted_chunk=ex_chunk[:4000],
            )

            try:
                if page_images and i < len(page_images):
                    # Multimodal: include page image
                    response = self.gemini_client.generate_content([prompt, page_images[i]])
                else:
                    response = self.gemini_client.generate_content(prompt)

                result = _parse_judge_response(response.text)
                if result:
                    chunk_results.append(result)
                    chunk_weights.append(len(_simple_tokenize(gt_chunk)))
                time.sleep(0.5)  # Polite rate limit

            except Exception:
                # On chunk failure, use heuristic for this chunk
                heuristic = _heuristic_judge(ex_chunk, gt_chunk, file_name, file_type)
                chunk_results.append(heuristic.to_dict())
                chunk_weights.append(len(_simple_tokenize(gt_chunk)))

        if not chunk_results:
            return _heuristic_judge(extracted_text, ground_truth_text, file_name, file_type)

        # ----- Weighted aggregation of chunk scores -----
        total_weight = sum(chunk_weights) or 1

        def weighted_avg(key: str) -> float:
            return sum(r.get(key, 0) * w for r, w in zip(chunk_results, chunk_weights, strict=True)) / total_weight

        completeness = weighted_avg("completeness_score")
        structure = weighted_avg("structure_fidelity_score")
        noise = weighted_avg("noise_hallucination_score")
        arabic = weighted_avg("arabic_fidelity_score")
        overall = completeness * 0.40 + structure * 0.25 + noise * 0.20 + arabic * 0.15

        verdict = "PASS" if overall >= 80 else ("CONDITIONAL_PASS" if overall >= 60 else "FAIL")

        # Merge lists across chunks
        missing = []
        noise_artifacts = []
        recommendations = []
        for r in chunk_results:
            missing.extend(r.get("missing_critical_elements", []))
            noise_artifacts.extend(r.get("noise_artifacts", []))
            recommendations.extend(r.get("recommendations", []))

        return JudgeResult(
            file_name=file_name,
            file_type=file_type,
            completeness_score=round(completeness, 2),
            structure_fidelity_score=round(structure, 2),
            noise_hallucination_score=round(noise, 2),
            arabic_fidelity_score=round(arabic, 2),
            overall_score=round(overall, 2),
            verdict=verdict,
            missing_critical_elements=list(set(missing))[:15],
            noise_artifacts=list(set(noise_artifacts))[:10],
            recommendations=list(set(recommendations))[:10],
            chunks_evaluated=n_chunks,
            used_vision=bool(page_images),
            used_fallback_heuristic=False,
        )
