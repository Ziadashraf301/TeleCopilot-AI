"""
evals/extraction
~~~~~~~~~~~~~~~~
Shared evaluation toolkit for TeleCopilot-AI extraction quality experiments.

Modules:
    ground_truth_builder  - Lossless container-level parsers per file format
    metrics               - Word-level, ROUGE-L, entity, order & type metrics
    llm_judge             - Gemini LLM-as-a-Judge with sliding window chunking
    hitl                  - Human-in-the-loop diff display and review logging
"""

from .ground_truth_builder import GroundTruthBuilder, GroundTruthDocument
from .hitl import HITLReviewer
from .llm_judge import GeminiJudge, JudgeResult
from .metrics import ExtractionMetrics, aggregate_micro_macro, compute_all_metrics

__all__ = [
    "GroundTruthDocument",
    "GroundTruthBuilder",
    "ExtractionMetrics",
    "compute_all_metrics",
    "aggregate_micro_macro",
    "GeminiJudge",
    "JudgeResult",
    "HITLReviewer",
]
