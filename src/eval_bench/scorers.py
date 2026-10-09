"""Scorer functions for eval_bench.

Each scorer accepts an EvalCase and a raw output string and returns
a (score: float, rationale: str) tuple.
"""
from __future__ import annotations

import re
from typing import Any

from eval_bench.schema import EvalCase

_JUDGE_PROMPT = """\
You are grading an AI assistant's response to a task.

Task: {input}
Response: {output}
{reference_line}
Rate the response from 1 to 5:
1 = completely wrong or irrelevant
2 = mostly wrong
3 = partially correct
4 = mostly correct
5 = perfect

Reply with a single integer only."""


def _exact_match(case: EvalCase, output: str) -> tuple[float, str]:
    if output.strip() == case.expected.strip():
        return 1.0, "exact match"
    return 0.0, "no match"


def _regex_match(case: EvalCase, output: str) -> tuple[float, str]:
    try:
        m = re.search(case.expected, output)
    except re.error as exc:
        return 0.0, f"invalid regex pattern: {exc}"
    if m:
        return 1.0, f"pattern matched at position {m.start()}"
    return 0.0, "pattern not found"


async def _llm_judge(
    case: EvalCase,
    output: str,
    *,
    openai_client: Any = None,
    anthropic_client: Any = None,
) -> tuple[float, str]:
    reference_line = (
        f"Reference answer: {case.expected}" if case.expected else ""
    )
    prompt = _JUDGE_PROMPT.format(
        input=case.input,
        output=output,
        reference_line=reference_line,
    )

    response_text: str

    if openai_client is not None:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=16,
        )
        response_text = response.choices[0].message.content
    elif anthropic_client is not None:
        response = await anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=16,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text
    else:
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=16,
        )
        response_text = response.choices[0].message.content

    m = re.search(r"[1-5]", response_text)
    if not m:
        raise ValueError(
            f"llm_judge: no digit 1-5 found in response: {response_text!r}"
        )
    return float(m.group()), response_text


async def score(
    case: EvalCase,
    output: str,
    *,
    openai_client: Any = None,
    anthropic_client: Any = None,
) -> tuple[float, str]:
    """Dispatch to the correct scorer. Returns (score, rationale)."""
    if case.scorer == "exact_match":
        return _exact_match(case, output)
    elif case.scorer == "regex":
        return _regex_match(case, output)
    elif case.scorer == "llm_judge":
        return await _llm_judge(
            case, output,
            openai_client=openai_client,
            anthropic_client=anthropic_client,
        )
    else:
        raise ValueError(f"Unknown scorer type: {case.scorer!r}")
