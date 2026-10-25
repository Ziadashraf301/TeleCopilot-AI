"""
experiments/extraction_eval/hitl.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Human-In-The-Loop interactive review toolkit for Jupyter notebooks.

Features:
  - Side-by-side text diff display (HTML/IPython rich display)
  - Per-section diff highlighting: green = retained, red = missing, yellow = partial
  - PDF/DOCX page image display alongside extracted text
  - Interactive review recorder with APPROVE / FLAG / OVERRIDE_SCORE actions
  - Audit log persistence to experiments/reports/hitl_audit_log.json
"""

from __future__ import annotations

import difflib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Review Record Dataclass
# ---------------------------------------------------------------------------


@dataclass
class HITLReviewRecord:
    """Single human review decision for one document."""

    file_name: str
    file_type: str
    timestamp: str
    action: str  # APPROVE | FLAG | OVERRIDE_SCORE
    human_score: float | None = None
    comment: str = ""
    flagged_issues: list[str] = field(default_factory=list)
    auto_score: float = 0.0
    verdict: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Main HITLReviewer Class
# ---------------------------------------------------------------------------


class HITLReviewer:
    """
    Human-In-The-Loop reviewer for Jupyter notebooks.
    Records approvals, flags, and score overrides.
    Exports audit log to disk.
    """

    def __init__(self, report_dir: str = "experiments/reports"):
        self.report_dir = report_dir
        self.audit_log: list[HITLReviewRecord] = []
        os.makedirs(report_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def display_diff(
        self,
        extracted_text: str,
        ground_truth_text: str,
        title: str = "Extraction Diff",
        max_chars: int = 3000,
    ) -> None:
        """
        Render an HTML side-by-side diff in Jupyter via IPython.display.
        Green = present in both, Red = in GT but missing from extracted, Yellow = partial.
        """
        try:
            from IPython.display import HTML, display
        except ImportError:
            print("[HITL] IPython not available — printing plain text diff instead.\n")
            self._plain_diff(extracted_text, ground_truth_text, title)
            return

        gt_preview = ground_truth_text[:max_chars]
        ex_preview = extracted_text[:max_chars]

        # Compute word-level diff using difflib
        gt_words = gt_preview.split()
        ex_words = ex_preview.split()
        matcher = difflib.SequenceMatcher(None, ex_words, gt_words, autojunk=False)

        ex_html_parts = []
        gt_html_parts = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            ex_segment = " ".join(ex_words[i1:i2])
            gt_segment = " ".join(gt_words[j1:j2])
            if tag == "equal":
                ex_html_parts.append(f'<span style="color:#22c55e">{_esc(ex_segment)}</span>')
                gt_html_parts.append(f'<span style="color:#22c55e">{_esc(gt_segment)}</span>')
            elif tag == "replace":
                ex_html_parts.append(
                    f'<span style="background:#fef9c3;color:#92400e;'
                    f'border-radius:3px;padding:1px 3px">{_esc(ex_segment)}</span>'
                )
                gt_html_parts.append(
                    f'<span style="background:#fee2e2;color:#991b1b;'
                    f'border-radius:3px;padding:1px 3px">{_esc(gt_segment)}</span>'
                )
            elif tag == "delete":
                ex_html_parts.append(
                    f'<span style="background:#fef9c3;color:#92400e;'
                    f'border-radius:3px;padding:1px 3px">{_esc(ex_segment)}</span>'
                )
            elif tag == "insert":
                gt_html_parts.append(
                    f'<span style="background:#fee2e2;color:#991b1b;'
                    f'border-radius:3px;padding:1px 3px">{_esc(gt_segment)}</span>'
                )

        ex_html = " ".join(ex_html_parts)
        gt_html = " ".join(gt_html_parts)

        html = f"""
<div style="font-family:'JetBrains Mono','Fira Code',monospace;font-size:13px;
            border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;margin:12px 0">
  <div style="background:#1e293b;color:#f1f5f9;padding:10px 16px;
              font-weight:bold;font-size:14px">
      🔍 {_esc(title)}
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0">
    <div style="border-right:1px solid #e2e8f0">
      <div style="background:#f0fdf4;padding:6px 12px;font-weight:bold;
                  color:#166534;border-bottom:1px solid #e2e8f0">
          ✅ Extracted Text
      </div>
      <div style="padding:12px;line-height:1.8;white-space:pre-wrap;
                  max-height:400px;overflow-y:auto;word-break:break-word">
          {ex_html}
      </div>
    </div>
    <div>
      <div style="background:#fef2f2;padding:6px 12px;font-weight:bold;
                  color:#991b1b;border-bottom:1px solid #e2e8f0">
          📋 Ground Truth
      </div>
      <div style="padding:12px;line-height:1.8;white-space:pre-wrap;
                  max-height:400px;overflow-y:auto;word-break:break-word">
          {gt_html}
      </div>
    </div>
  </div>
  <div style="background:#f8fafc;padding:8px 16px;font-size:11px;color:#64748b;
              border-top:1px solid #e2e8f0">
      🟢 Retained &nbsp;&nbsp; 🟡 Modified &nbsp;&nbsp; 🔴 Missing from extraction
      &nbsp;&nbsp;|&nbsp;&nbsp; Showing first {max_chars:,} characters
  </div>
</div>"""
        display(HTML(html))

    def display_image_alongside_text(
        self,
        images: list[Any],  # PIL Images
        extracted_text: str,
        title: str = "Visual vs Extracted",
        max_images: int = 3,
    ) -> None:
        """Display PDF/DOCX page images alongside extracted text in Jupyter."""
        try:
            import base64
            import io

            from IPython.display import HTML, display
        except ImportError:
            print("[HITL] IPython not available.")
            return

        image_panels = []
        for i, img in enumerate(images[:max_images]):
            try:
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()
                image_panels.append(
                    f'<div style="margin-bottom:12px">'
                    f'<div style="font-size:11px;color:#64748b;margin-bottom:4px">'
                    f"Page / Image {i + 1}</div>"
                    f'<img src="data:image/png;base64,{b64}" '
                    f'style="max-width:100%;border:1px solid #e2e8f0;border-radius:4px"/>'
                    f"</div>"
                )
            except Exception:
                image_panels.append(f"<div>[Image {i + 1} — render error]</div>")

        ex_preview = _esc(extracted_text[:2000])

        html = f"""
<div style="font-family:sans-serif;font-size:13px;border:1px solid #e2e8f0;
            border-radius:8px;overflow:hidden;margin:12px 0">
  <div style="background:#1e293b;color:#f1f5f9;padding:10px 16px;
              font-weight:bold;font-size:14px">
      🖼️ {_esc(title)}
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:0">
    <div style="border-right:1px solid #e2e8f0;padding:12px;
                max-height:500px;overflow-y:auto">
      <div style="font-weight:bold;color:#7c3aed;margin-bottom:8px">
          🖼️ Source Page Images
      </div>
      {"".join(image_panels)}
    </div>
    <div style="padding:12px;max-height:500px;overflow-y:auto">
      <div style="font-weight:bold;color:#0284c7;margin-bottom:8px">
          📄 Extracted Text
      </div>
      <pre style="white-space:pre-wrap;word-break:break-word;
                  font-family:monospace;font-size:12px;line-height:1.6">
{ex_preview}</pre>
    </div>
  </div>
</div>"""
        display(HTML(html))

    def display_metrics_summary(self, metrics_dict: dict[str, Any], judge_result: Any = None) -> None:
        """Render a styled metrics summary card in Jupyter."""
        try:
            from IPython.display import HTML, display
        except ImportError:
            print(json.dumps(metrics_dict, indent=2))
            return

        def badge(value: float, thresholds=(0.8, 0.6)) -> str:
            color = "#22c55e" if value >= thresholds[0] else ("#f59e0b" if value >= thresholds[1] else "#ef4444")
            return (
                f'<span style="background:{color};color:white;'
                f'border-radius:4px;padding:2px 8px;font-size:12px;font-weight:bold">'
                f"{value:.1%}</span>"
            )

        rows = ""
        metric_labels = {
            "word_recall": "Word Recall",
            "word_precision": "Word Precision",
            "word_f1": "Word F1",
            "rouge_l_score": "ROUGE-L",
            "entity_recall_overall": "Entity Retention",
            "section_order_tau": "Section Order (τ)",
            "table_cell_retention": "Table Retention",
            "media_retention": "Media Retention",
        }
        for key, label in metric_labels.items():
            val = metrics_dict.get(key)
            if val is not None:
                rows += (
                    f"<tr><td style='padding:6px 12px;color:#475569'>{label}</td>"
                    f"<td style='padding:6px 12px'>{badge(val)}</td></tr>"
                )

        judge_section = ""
        if judge_result:
            verdict_color = {"PASS": "#22c55e", "CONDITIONAL_PASS": "#f59e0b", "FAIL": "#ef4444"}.get(
                judge_result.verdict, "#94a3b8"
            )
            judge_section = f"""
<div style="margin-top:12px;padding:12px;background:#f8fafc;border-radius:6px;
            border-left:4px solid {verdict_color}">
  <div style="font-weight:bold;color:{verdict_color};margin-bottom:6px">
      Gemini Judge: {judge_result.verdict_emoji} {judge_result.verdict}
      &nbsp;(Score: {judge_result.overall_score:.1f}/100)
  </div>
  <div style="font-size:12px;color:#475569">
    Completeness: {judge_result.completeness_score:.0f} &nbsp;|&nbsp;
    Structure: {judge_result.structure_fidelity_score:.0f} &nbsp;|&nbsp;
    Noise: {judge_result.noise_hallucination_score:.0f} &nbsp;|&nbsp;
    Arabic: {judge_result.arabic_fidelity_score:.0f}
  </div>
  {"".join(f'<div style="color:#ef4444;font-size:11px;margin-top:4px">⚠ {_esc(m)}</div>' for m in judge_result.missing_critical_elements[:5])}
</div>"""

        html = f"""
<div style="font-family:sans-serif;border:1px solid #e2e8f0;border-radius:8px;
            overflow:hidden;margin:12px 0;max-width:600px">
  <div style="background:#0f172a;color:#f1f5f9;padding:10px 16px;
              font-weight:bold">📊 Extraction Metrics</div>
  <table style="width:100%;border-collapse:collapse">
    {rows}
  </table>
  {judge_section}
</div>"""
        display(HTML(html))

    # ------------------------------------------------------------------
    # HITL Review Recording
    # ------------------------------------------------------------------

    def record_review(
        self,
        file_name: str,
        file_type: str,
        action: str,
        auto_score: float = 0.0,
        verdict: str = "",
        human_score: float | None = None,
        comment: str = "",
        flagged_issues: list[str] | None = None,
    ) -> HITLReviewRecord:
        """
        Record a human review decision.

        Args:
            action: One of 'APPROVE', 'FLAG', 'OVERRIDE_SCORE'
            human_score: If action is OVERRIDE_SCORE, provide your score (0–100)
            comment: Free-text annotation
            flagged_issues: List of specific issues identified
        """
        record = HITLReviewRecord(
            file_name=file_name,
            file_type=file_type,
            timestamp=datetime.now().isoformat(),
            action=action.upper(),
            human_score=human_score,
            comment=comment,
            flagged_issues=flagged_issues or [],
            auto_score=auto_score,
            verdict=verdict,
        )
        self.audit_log.append(record)

        try:
            from IPython.display import HTML, display

            color_map = {"APPROVE": "#22c55e", "FLAG": "#f59e0b", "OVERRIDE_SCORE": "#7c3aed"}
            color = color_map.get(action.upper(), "#94a3b8")
            comment_html = f"<br><em style='color:#64748b'>{_esc(comment)}</em>" if comment else ""
            display(
                HTML(
                    f'<div style="background:{color}1a;border-left:4px solid {color};'
                    f'border-radius:4px;padding:10px 16px;margin:8px 0;font-family:sans-serif">'
                    f'<strong style="color:{color}">{action.upper()}</strong> recorded for '
                    f"<code>{_esc(file_name)}</code>"
                    f"{f' — Score override: {human_score}' if human_score is not None else ''}"
                    f"{comment_html}"
                    f"</div>"
                )
            )
        except ImportError:
            print(f"[HITL] {action.upper()} recorded for {file_name}")

        return record

    def save_audit_log(self, filename: str = "hitl_audit_log.json") -> str:
        """Persist all review records to JSON."""
        out_path = os.path.join(self.report_dir, filename)
        data = {
            "generated_at": datetime.now().isoformat(),
            "total_reviews": len(self.audit_log),
            "reviews": [r.to_dict() for r in self.audit_log],
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[HITL] Audit log saved → {out_path}")
        return out_path

    # ------------------------------------------------------------------
    # Plain text fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _plain_diff(extracted: str, ground_truth: str, title: str) -> None:
        print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")
        diff = difflib.unified_diff(
            ground_truth.splitlines(),
            extracted.splitlines(),
            fromfile="ground_truth",
            tofile="extracted",
            lineterm="",
        )
        print("\n".join(list(diff)[:80]))


# ---------------------------------------------------------------------------
# Benchmark Report Writer
# ---------------------------------------------------------------------------


def save_benchmark_report(
    all_metrics: list[dict[str, Any]],
    aggregations: dict[str, Any],
    judge_results: list[dict[str, Any]],
    report_dir: str = "experiments/reports",
) -> tuple[str, str]:
    """
    Save comprehensive benchmark results as JSON + Markdown summary.
    Returns (json_path, md_path).
    """
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ---- JSON Report ----
    json_data = {
        "generated_at": datetime.now().isoformat(),
        "per_file_metrics": all_metrics,
        "aggregations": {k: asdict(v) if hasattr(v, "__dataclass_fields__") else v for k, v in aggregations.items()},
        "judge_results": judge_results,
    }
    json_path = os.path.join(report_dir, f"extraction_benchmark_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # ---- Markdown Summary ----
    md_lines = [
        "# Extraction Quality Benchmark Report",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n**Total Files Evaluated:** {len(all_metrics)}\n",
        "---\n",
        "## Aggregated Metrics\n",
        "| Scope | Macro Word F1 | Macro ROUGE-L | Micro Word F1 | Macro Entity | Macro Table |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for label, agg in aggregations.items():
        if hasattr(agg, "__dataclass_fields__"):
            md_lines.append(
                f"| **{label}** "
                f"| {agg.macro_word_f1:.1%} "
                f"| {agg.macro_rouge_l:.1%} "
                f"| {agg.micro_word_f1:.1%} "
                f"| {agg.macro_entity_recall:.1%} "
                f"| {agg.macro_table_retention:.1%} |"
            )

    md_lines += [
        "\n---\n",
        "## Per-File Results\n",
        "| File | Type | Word F1 | ROUGE-L | Entity | Order τ | Gemini Score | Verdict |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    judge_map = {j.get("file_name", ""): j for j in judge_results}
    for m in all_metrics:
        fn = m.get("file_name", "")
        j = judge_map.get(fn, {})
        verdict = j.get("verdict", "—")
        verdict_emoji = {"PASS": "✅", "CONDITIONAL_PASS": "⚠️", "FAIL": "❌"}.get(verdict, "—")
        md_lines.append(
            f"| `{fn}` "
            f"| {m.get('file_type', '')}"
            f"| {m.get('word_f1', 0):.1%} "
            f"| {m.get('rouge_l_score', 0):.1%} "
            f"| {m.get('entity_recall_overall', 0):.1%} "
            f"| {m.get('section_order_tau', 1):.2f} "
            f"| {j.get('overall_score', 0):.1f}/100 "
            f"| {verdict_emoji} {verdict} |"
        )

    md_lines.append("\n---\n*Generated by TeleCopilot-AI Extraction Quality Evaluation Framework*")

    md_path = os.path.join(report_dir, f"extraction_audit_summary_{timestamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"[Report] JSON  → {json_path}")
    print(f"[Report] MD    → {md_path}")
    return json_path, md_path


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# Fix missing Tuple import at module level
