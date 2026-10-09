from __future__ import annotations

import asyncio
import time
from typing import Any

from pydantic import BaseModel

from eval_bench.schema import EvalSuite


class RunResult(BaseModel):
    case_id: str
    model: str
    output: str | None
    error: str | None
    latency_ms: float


async def _call_openai(model_name: str, prompt: str, client: Any) -> tuple[str, float]:
    t0 = time.monotonic()
    response = await client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
    )
    latency_ms = (time.monotonic() - t0) * 1000
    return response.choices[0].message.content, latency_ms


async def _call_anthropic(model_name: str, prompt: str, client: Any) -> tuple[str, float]:
    t0 = time.monotonic()
    response = await client.messages.create(
        model=model_name,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = (time.monotonic() - t0) * 1000
    if not response.content:
        raise ValueError("Anthropic response returned empty content list")
    return response.content[0].text, latency_ms


async def run_suite(
    suite: EvalSuite,
    *,
    openai_client: Any = None,
    anthropic_client: Any = None,
    concurrency: int = 5,
    progress: Any = None,
    task_id: Any = None,
) -> list[RunResult]:
    pairs = [
        (case, model_str)
        for case in suite.cases
        for model_str in case.models
    ]

    semaphore = asyncio.Semaphore(concurrency)

    async def _run_one(case, model_str: str) -> RunResult:
        case_id = case.id or case.input[:40]

        async with semaphore:
            try:
                if model_str.startswith("openai/"):
                    client = openai_client
                    if client is None:
                        from openai import AsyncOpenAI
                        client = AsyncOpenAI()
                    model_name = model_str[len("openai/"):]
                    output, latency_ms = await _call_openai(model_name, case.input, client)
                elif model_str.startswith("anthropic/"):
                    client = anthropic_client
                    if client is None:
                        from anthropic import AsyncAnthropic
                        client = AsyncAnthropic()
                    model_name = model_str[len("anthropic/"):]
                    output, latency_ms = await _call_anthropic(model_name, case.input, client)
                else:
                    raise ValueError(
                        f"Unknown model prefix in '{model_str}'. "
                        "Expected 'openai/<name>' or 'anthropic/<name>'."
                    )
                result = RunResult(
                    case_id=case_id,
                    model=model_str,
                    output=output,
                    error=None,
                    latency_ms=latency_ms,
                )
            except Exception as exc:
                result = RunResult(
                    case_id=case_id,
                    model=model_str,
                    output=None,
                    error=str(exc),
                    latency_ms=0.0,
                )
            finally:
                if progress is not None:
                    progress.advance(task_id)

        return result

    tasks = [_run_one(case, model_str) for case, model_str in pairs]
    results = await asyncio.gather(*tasks)
    return list(results)
