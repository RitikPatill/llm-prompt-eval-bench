"""Unit tests for scorer functions."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from eval_bench.runner import RunResult, run_suite
from eval_bench.schema import EvalCase, EvalSuite
from eval_bench.scorers import score


def _make_case(scorer="exact_match", expected="hello", input_text="say hello") -> EvalCase:
    return EvalCase(
        id="test",
        input=input_text,
        expected=expected,
        models=["openai/gpt-4o-mini"],
        scorer=scorer,
    )


# --- exact_match ---

@pytest.mark.asyncio
async def test_exact_match_hit():
    case = _make_case(scorer="exact_match", expected="hello")
    sc, rationale = await score(case, "hello")
    assert sc == 1.0


@pytest.mark.asyncio
async def test_exact_match_miss():
    case = _make_case(scorer="exact_match", expected="hello")
    sc, rationale = await score(case, "Hello")
    assert sc == 0.0


@pytest.mark.asyncio
async def test_exact_match_strips_whitespace():
    case = _make_case(scorer="exact_match", expected="hello")
    sc, rationale = await score(case, " hello\n")
    assert sc == 1.0


# --- regex ---

@pytest.mark.asyncio
async def test_regex_match_hit():
    case = _make_case(scorer="regex", expected=r"^\d{4}$")
    sc, rationale = await score(case, "1234")
    assert sc == 1.0


@pytest.mark.asyncio
async def test_regex_match_miss():
    case = _make_case(scorer="regex", expected=r"^\d{4}$")
    sc, rationale = await score(case, "12345")
    assert sc == 0.0


@pytest.mark.asyncio
async def test_regex_invalid_pattern():
    case = _make_case(scorer="regex", expected="[")
    sc, rationale = await score(case, "anything")
    assert sc == 0.0
    assert "invalid regex" in rationale.lower() or "error" in rationale.lower()


# --- llm_judge ---

def _openai_response(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.mark.asyncio
async def test_llm_judge_parses_score():
    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_openai_response("4"))

    case = EvalCase(id="j1", input="What is 2+2?", expected=None, models=["openai/gpt-4o-mini"], scorer="llm_judge")
    sc, rationale = await score(case, "The answer is 4", openai_client=mock_client)
    assert sc == 4.0
    assert rationale == "4"


@pytest.mark.asyncio
async def test_llm_judge_parses_score_embedded():
    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_openai_response("Rating: 3/5"))

    case = EvalCase(id="j2", input="What is 2+2?", expected=None, models=["openai/gpt-4o-mini"], scorer="llm_judge")
    sc, rationale = await score(case, "Four", openai_client=mock_client)
    assert sc == 3.0


@pytest.mark.asyncio
async def test_llm_judge_no_digit_raises():
    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_openai_response("good"))

    case = EvalCase(id="j3", input="What is 2+2?", expected=None, models=["openai/gpt-4o-mini"], scorer="llm_judge")
    with pytest.raises(ValueError):
        await score(case, "four", openai_client=mock_client)


# --- RunResult fields ---

def test_run_result_has_score_field():
    result = RunResult(case_id="c1", model="openai/gpt-4o-mini", output="hi", error=None, latency_ms=0.0)
    assert result.score is None
    assert result.rationale is None


# --- runner integration ---

@pytest.mark.asyncio
async def test_runner_attaches_score():
    """run_suite should attach score to RunResult for exact_match."""
    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_openai_response("world")
    )

    case = EvalCase(id="c1", input="hello", expected="world", models=["openai/gpt-4o-mini"], scorer="exact_match")
    suite = EvalSuite(name="s", cases=[case])
    results = await run_suite(suite, openai_client=mock_client)

    assert results[0].score is not None
    assert results[0].score == 1.0
