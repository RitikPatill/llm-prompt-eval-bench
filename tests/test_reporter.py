"""Tests for eval_bench.reporter (M5)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from eval_bench.cli import app
from eval_bench.reporter import build_report_data, save_report
from eval_bench.runner import RunResult
from eval_bench.schema import EvalCase, EvalSuite


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_suite() -> EvalSuite:
    return EvalSuite(
        name="test suite",
        cases=[
            EvalCase(id="c1", input="Say hi", expected="hi", models=["openai/gpt-x"], scorer="exact_match"),
            EvalCase(id="c2", input="2+2", expected="4", models=["openai/gpt-x", "anthropic/claude-y"], scorer="exact_match"),
        ],
    )


def _make_results() -> list[RunResult]:
    return [
        RunResult(case_id="c1", model="openai/gpt-x", output="hi", error=None, latency_ms=100.0, score=1.0, rationale="exact"),
        RunResult(case_id="c2", model="openai/gpt-x", output="4", error=None, latency_ms=120.0, score=1.0, rationale="exact"),
        RunResult(case_id="c2", model="anthropic/claude-y", output="four", error=None, latency_ms=200.0, score=0.0, rationale="no match"),
    ]


# ---------------------------------------------------------------------------
# build_report_data tests
# ---------------------------------------------------------------------------


def test_build_report_data_shape():
    data = build_report_data(_make_suite(), _make_results())
    assert set(data.keys()) >= {"suite_name", "timestamp", "models", "summary", "cases"}


def test_build_report_data_avg_score():
    data = build_report_data(_make_suite(), _make_results())
    summary = {row["model"]: row for row in data["summary"]}
    # openai/gpt-x: scores [1.0, 1.0] → avg 1.0
    assert summary["openai/gpt-x"]["avg_score"] == pytest.approx(1.0)
    # anthropic/claude-y: scores [0.0] → avg 0.0
    assert summary["anthropic/claude-y"]["avg_score"] == pytest.approx(0.0)


def test_build_report_data_avg_score_excludes_none():
    suite = EvalSuite(
        name="s",
        cases=[EvalCase(id="c1", input="q", models=["openai/m"], scorer="llm_judge")],
    )
    results = [
        RunResult(case_id="c1", model="openai/m", output=None, error="timeout", latency_ms=0.0, score=None),
    ]
    data = build_report_data(suite, results)
    assert data["summary"][0]["avg_score"] is None


def test_build_report_data_divergence_flag():
    data = build_report_data(_make_suite(), _make_results())
    cases = {c["case_id"]: c for c in data["cases"]}
    # c2 has two models returning different outputs → divergence
    assert cases["c2"]["has_divergence"] is True
    # c1 has only one model → no divergence
    assert cases["c1"]["has_divergence"] is False


# ---------------------------------------------------------------------------
# save_report tests
# ---------------------------------------------------------------------------


def test_save_report_creates_files(tmp_path):
    json_path, html_path = save_report(_make_suite(), _make_results(), output_dir=tmp_path)
    assert json_path.exists()
    assert html_path.exists()


def test_json_artifact_valid(tmp_path):
    json_path, _ = save_report(_make_suite(), _make_results(), output_dir=tmp_path)
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "cases" in data
    assert len(data["cases"]) == 2


def test_html_contains_model_names(tmp_path):
    _, html_path = save_report(_make_suite(), _make_results(), output_dir=tmp_path)
    html = html_path.read_text(encoding="utf-8")
    assert "openai/gpt-x" in html
    assert "anthropic/claude-y" in html


def test_html_contains_scores(tmp_path):
    _, html_path = save_report(_make_suite(), _make_results(), output_dir=tmp_path)
    html = html_path.read_text(encoding="utf-8")
    # Scores like "1.0" and "0.0" should appear
    assert "1.0" in html
    assert "0.0" in html


# ---------------------------------------------------------------------------
# CLI report command tests
# ---------------------------------------------------------------------------


runner = CliRunner()


def test_report_last_no_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["report", "last"])
    assert result.exit_code == 1
    assert "No reports found" in result.output


def test_report_last_opens_newest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports_dir = tmp_path / ".eval_reports"
    reports_dir.mkdir()
    # Create two fake HTML files with sortable timestamps
    old_html = reports_dir / "run_20250101T000000.html"
    new_html = reports_dir / "run_20250102T000000.html"
    old_html.write_text("<html>old</html>")
    new_html.write_text("<html>new</html>")

    opened_urls: list[str] = []

    def fake_open(url: str) -> None:
        opened_urls.append(url)

    monkeypatch.setattr("webbrowser.open", fake_open)

    result = runner.invoke(app, ["report", "last"])
    assert result.exit_code == 0
    assert len(opened_urls) == 1
    # Should open the newest file
    assert "run_20250102T000000.html" in opened_urls[0]
