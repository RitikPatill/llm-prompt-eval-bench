from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from eval_bench.schema import EvalSuite
from eval_bench.runner import RunResult

# ---------------------------------------------------------------------------
# Inline Jinja2 template — no separate file needed
# ---------------------------------------------------------------------------

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Eval Report — {{ suite_name }}</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; background: #f9f9f9; color: #222; }
    h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
    .meta { color: #666; font-size: 0.85rem; margin-bottom: 1.5rem; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; background: #fff; }
    th, td { border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }
    th { background: #eef; font-weight: 600; }
    tr:nth-child(even) { background: #f5f5f5; }
    details { margin-bottom: 0.75rem; background: #fff; border: 1px solid #ddd; border-radius: 4px; }
    summary { cursor: pointer; padding: 0.6rem 0.75rem; font-weight: 600; background: #eef; }
    .case-table { width: 100%; border-collapse: collapse; }
    .case-table th, .case-table td { border: 1px solid #e0e0e0; padding: 0.4rem 0.6rem; vertical-align: top; }
    .case-table th { background: #f5f5ff; }
    .score-high { color: #1a7a1a; font-weight: bold; }
    .score-mid  { color: #a06000; font-weight: bold; }
    .score-low  { color: #c00000; font-weight: bold; }
    .score-none { color: #888; }
    .diverge    { background: #fff9c4; }
    .error-cell { color: #c00; font-style: italic; }
    .rationale  { font-size: 0.82rem; color: #555; margin-top: 0.25rem; }
    .input-block { background: #f0f0f0; padding: 0.4rem 0.6rem; border-radius: 3px;
                   font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h1>Eval Report — {{ suite_name }}</h1>
  <p class="meta">Generated {{ timestamp }} &nbsp;·&nbsp; {{ cases|length }} case(s) &nbsp;·&nbsp; {{ models|length }} model(s)</p>

  <h2>Summary</h2>
  <table>
    <thead>
      <tr>
        <th>Model</th>
        <th>Cases</th>
        <th>Avg Score</th>
        <th>Avg Latency (ms)</th>
      </tr>
    </thead>
    <tbody>
      {% for row in summary %}
      <tr>
        <td>{{ row.model }}</td>
        <td>{{ row.n }}</td>
        <td>
          {% if row.avg_score is none %}
          <span class="score-none">—</span>
          {% elif row.avg_score >= 4 %}
          <span class="score-high">{{ "%.2f"|format(row.avg_score) }}</span>
          {% elif row.avg_score >= 2 %}
          <span class="score-mid">{{ "%.2f"|format(row.avg_score) }}</span>
          {% else %}
          <span class="score-low">{{ "%.2f"|format(row.avg_score) }}</span>
          {% endif %}
        </td>
        <td>
          {% if row.avg_latency_ms is none %}—
          {% else %}{{ "%.0f"|format(row.avg_latency_ms) }}{% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <h2>Cases</h2>
  {% for case in cases %}
  <details {% if case.has_divergence %}open{% endif %}>
    <summary>{{ case.case_id }} — {{ case.input[:80] }}{% if case.input|length > 80 %}…{% endif %}
      {% if case.has_divergence %}&nbsp;<span style="color:#a06000">[divergence]</span>{% endif %}
    </summary>
    <div style="padding: 0.75rem;">
      <div class="input-block">{{ case.input }}</div>
      {% if case.expected %}
      <p style="font-size:0.85rem;margin-top:0.5rem;"><strong>Expected:</strong> {{ case.expected }}</p>
      {% endif %}
      <table class="case-table" style="margin-top:0.75rem;">
        <thead>
          <tr>
            <th>Model</th>
            <th>Output</th>
            <th>Score</th>
            <th>Rationale</th>
            <th>Latency (ms)</th>
          </tr>
        </thead>
        <tbody>
          {% for r in case.results %}
          <tr>
            <td>{{ r.model }}</td>
            <td {% if case.has_divergence %}class="diverge"{% endif %}>
              {% if r.error %}
              <span class="error-cell">ERROR: {{ r.error }}</span>
              {% else %}
              {{ r.output }}
              {% endif %}
            </td>
            <td>
              {% if r.score is none %}
              <span class="score-none">—</span>
              {% elif r.score >= 4 %}
              <span class="score-high">{{ "%.1f"|format(r.score) }}</span>
              {% elif r.score >= 2 %}
              <span class="score-mid">{{ "%.1f"|format(r.score) }}</span>
              {% else %}
              <span class="score-low">{{ "%.1f"|format(r.score) }}</span>
              {% endif %}
            </td>
            <td><span class="rationale">{{ r.rationale or "—" }}</span></td>
            <td>{{ "%.0f"|format(r.latency_ms) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </details>
  {% endfor %}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_report_data(suite: EvalSuite, results: list[RunResult]) -> dict:
    """Return a serialisable dict used for both JSON and HTML rendering."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Collect all model strings that appear in results
    models: list[str] = list(dict.fromkeys(r.model for r in results))

    # Group results by case_id
    case_results: dict[str, list[RunResult]] = {}
    for r in results:
        case_results.setdefault(r.case_id, []).append(r)

    # Build per-case rows (preserve case declaration order)
    cases = []
    seen_case_ids: set[str] = set()
    for case in suite.cases:
        case_id = case.id or case.input[:40]
        if case_id in seen_case_ids:
            continue
        seen_case_ids.add(case_id)
        c_results = case_results.get(case_id, [])
        outputs = {r.output for r in c_results if r.output}
        has_divergence = len(outputs) > 1
        cases.append(
            {
                "case_id": case_id,
                "input": case.input,
                "expected": case.expected,
                "results": [
                    {
                        "model": r.model,
                        "output": r.output,
                        "score": r.score,
                        "rationale": r.rationale,
                        "latency_ms": r.latency_ms,
                        "error": r.error,
                    }
                    for r in c_results
                ],
                "has_divergence": has_divergence,
            }
        )

    # Build summary per model
    summary = []
    for model in models:
        model_results = [r for r in results if r.model == model]
        scores = [r.score for r in model_results if r.score is not None]
        latencies = [r.latency_ms for r in model_results]
        summary.append(
            {
                "model": model,
                "n": len(model_results),
                "avg_score": (sum(scores) / len(scores)) if scores else None,
                "avg_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
            }
        )

    return {
        "suite_name": suite.name,
        "timestamp": timestamp,
        "models": models,
        "summary": summary,
        "cases": cases,
    }


def save_report(
    suite: EvalSuite,
    results: list[RunResult],
    output_dir: Path = Path(".eval_reports"),
) -> tuple[Path, Path]:
    """
    Persist JSON artifact and rendered HTML.
    Returns (json_path, html_path).
    Creates output_dir if it doesn't exist.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    data = build_report_data(suite, results)

    # JSON artifact
    json_path = output_dir / f"run_{ts}.json"
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # HTML report
    html_path = output_dir / f"run_{ts}.html"
    template = Template(REPORT_TEMPLATE)
    html = template.render(**data)
    html_path.write_text(html, encoding="utf-8")

    return json_path, html_path
