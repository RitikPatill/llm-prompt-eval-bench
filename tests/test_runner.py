"""Unit tests for the async runner (no real API calls)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eval_bench.runner import RunResult, run_suite
from eval_bench.schema import EvalCase, EvalSuite


def _make_suite(models: list[str], n_cases: int = 1) -> EvalSuite:
    cases = [
        EvalCase(id=f"c{i}", input=f"hello {i}", expected="world", models=models, scorer="exact_match")
        for i in range(n_cases)
    ]
    return EvalSuite(name="test-suite", cases=cases)


def _openai_response(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _anthropic_response(text: str) -> MagicMock:
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


@pytest.mark.asyncio
async def test_run_suite_openai_success():
    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_openai_response("hello world"))

    suite = _make_suite(["openai/gpt-4o-mini"])
    results = await run_suite(suite, openai_client=mock_client)

    assert len(results) == 1
    assert results[0].output == "hello world"
    assert results[0].error is None
    assert results[0].model == "openai/gpt-4o-mini"


@pytest.mark.asyncio
async def test_run_suite_anthropic_success():
    mock_client = MagicMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=_anthropic_response("claude says hi"))

    suite = _make_suite(["anthropic/claude-haiku-4-5-20251001"])
    results = await run_suite(suite, anthropic_client=mock_client)

    assert len(results) == 1
    assert results[0].output == "claude says hi"
    assert results[0].error is None


@pytest.mark.asyncio
async def test_run_suite_records_latency():
    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_openai_response("ok"))

    suite = _make_suite(["openai/gpt-4o-mini"])
    results = await run_suite(suite, openai_client=mock_client)

    assert results[0].latency_ms >= 0


@pytest.mark.asyncio
async def test_run_suite_captures_api_error():
    import openai

    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=openai.APIConnectionError(request=MagicMock())
    )

    suite = _make_suite(["openai/gpt-4o-mini"])
    results = await run_suite(suite, openai_client=mock_client)

    assert results[0].output is None
    assert results[0].error is not None
    assert len(results[0].error) > 0


@pytest.mark.asyncio
async def test_run_suite_unknown_prefix_raises():
    suite = _make_suite(["local/llama"])
    results = await run_suite(suite)

    # ValueError is caught and stored in .error field
    assert results[0].output is None
    assert "Unknown model prefix" in results[0].error


@pytest.mark.asyncio
async def test_run_suite_progress_advanced():
    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_openai_response("x"))

    suite = _make_suite(["openai/gpt-4o-mini", "openai/gpt-4o-mini"], n_cases=1)
    # 1 case × 2 models = 2 pairs
    progress = MagicMock()
    task_id = 42
    await run_suite(suite, openai_client=mock_client, progress=progress, task_id=task_id)

    assert progress.advance.call_count == 2


@pytest.mark.asyncio
async def test_run_suite_preserves_order():
    texts = ["alpha", "beta", "gamma"]
    call_count = 0

    async def _fake_create(**kwargs):
        nonlocal call_count
        resp = _openai_response(texts[call_count])
        call_count += 1
        return resp

    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = _fake_create

    cases = [
        EvalCase(id=f"c{i}", input=f"q{i}", expected="x", models=["openai/gpt-4o-mini"], scorer="exact_match")
        for i in range(3)
    ]
    suite = EvalSuite(name="order-test", cases=cases)
    results = await run_suite(suite, openai_client=mock_client)

    outputs = [r.output for r in results]
    assert outputs == texts
