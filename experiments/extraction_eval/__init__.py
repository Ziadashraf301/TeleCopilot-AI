"""
experiments/extraction_eval
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Shared evaluation toolkit for TeleCopilot-AI extraction quality experiments.

Modules:
    ground_truth_builder  - Lossless container-level parsers per file format
    metrics               - Word-level, ROUGE-L, entity, order & type metrics
    llm_judge             - Gemini LLM-as-a-Judge with sliding window chunking
    hitl                  - Human-in-the-loop diff display and review logging
"""
from .ground_truth_builder import GroundTruthDocument, GroundTruthBuilder
from .metrics import ExtractionMetrics, compute_all_metrics, aggregate_micro_macro
from .llm_judge import GeminiJudge, JudgeResult
from .hitl import HITLReviewer

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
