# llm-prompt-eval-bench

> One YAML file. One command. One report.

## What it does

`llm-prompt-eval-bench` is a lightweight, local evaluation harness for LLM prompts.
You define test cases in a YAML file — each with an input, an expected output or rubric,
and a list of models to run against — and the tool runs all combinations, scores them,
and emits a static HTML report plus a JSON artifact.

No cloud account required. No opaque framework. Just a YAML file and a single command.

## Status

**M3 — multi-model runner (current)**

| Deliverable | State |
|---|---|
| `pyproject.toml` with entry point `eval` | done |
| `requirements.txt` / `requirements-dev.txt` | done |
| MIT `LICENSE` | done |
| `src/eval_bench/cli.py` — `eval run` with Rich progress bar | done |
| `src/eval_bench/schema.py` — Pydantic v2 models (`EvalCase`, `EvalSuite`) | done |
| `src/eval_bench/loader.py` — `load_suite(path)` function | done |
| `src/eval_bench/runner.py` — async runner, `RunResult`, `run_suite()` | done |
| `tests/fixtures/simple_suite.yaml` — fixture covering all three scorer types | done |
| `tests/test_schema_loader.py` — 7 unit tests, all passing | done |
| `tests/test_runner.py` — 7 runner unit tests (mocked, no real API calls) | done |

`eval run suite.yaml` now fans out all `(case, model)` pairs concurrently,
calls the real OpenAI or Anthropic API, and streams a Rich progress bar.
A summary table (case_id / model / latency_ms / status) is printed at the end.

## Quick-start

Requires Python >= 3.10.

```bash
# Install
pip install -e .

# Verify the CLI is registered
eval --help

# Write your eval suite
cat > suite.yaml << 'EOF'
name: my eval suite

cases:
  - id: greeting
    input: "Say hello"
    expected: "hello"
    models:
      - openai/gpt-4o-mini
    scorer: exact_match
EOF

# Run the evaluation
eval run suite.yaml

# Re-open the last report  (not yet implemented — future milestone)
eval report last
```

Set your API keys before running:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

## Suite YAML format

```yaml
name: <string>            # required — human label for the suite
description: <string>     # optional

cases:
  - id: <string>          # optional — human label for the case
    input: <string>       # required — prompt sent to the model
    expected: <string>    # required for exact_match and regex; optional for llm_judge
    models:               # required — list of model strings (provider/name)
      - openai/gpt-4o-mini
      - anthropic/claude-haiku-4-5-20251001
    scorer: <scorer>      # required — one of: exact_match, regex, llm_judge
```

### Scorer types

| Scorer | `expected` field | Description |
|---|---|---|
| `exact_match` | required | Case-sensitive string equality |
| `regex` | required | Python `re.search` against the model output |
| `llm_judge` | optional | A small model grades the output 1–5 |

### Model strings

Models are specified as `provider/name`, e.g.:
- `openai/gpt-4o-mini`
- `anthropic/claude-haiku-4-5-20251001`

## Scorers

[TODO M4 — documentation for `exact_match`, `regex`, and `llm_judge` scorers]

## Report output

[TODO M4 — description of the static HTML report and JSON artifact]

## Architecture

Components marked `[done]` are implemented and tested. The rest are planned.

```
┌─────────────────────────────────────────────────────┐
│  CLI  (eval run / eval report)          [done]      │
│  src/eval_bench/cli.py                              │
└────────────────────┬────────────────────────────────┘
                     │ path to suite.yaml
                     ▼
┌─────────────────────────────────────────────────────┐
│  Schema + Loader                        [done]      │
│  src/eval_bench/schema.py  — EvalCase, EvalSuite    │
│  src/eval_bench/loader.py  — load_suite(path)       │
└────────────────────┬────────────────────────────────┘
                     │ List[EvalCase]
                     ▼
┌─────────────────────────────────────────────────────┐
│  Runner                                 [done]      │
│  src/eval_bench/runner.py  — run_suite(), RunResult │
│  • iterates (test_case × model) combinations        │
│  • calls OpenAI / Anthropic SDKs async             │
│  • rich progress bar, concurrency semaphore         │
└────────────┬──────────────────┬─────────────────────┘
             │                  │
             ▼                  ▼
┌────────────────────┐  ┌───────────────────────────┐
│  Scorers [planned] │  │  Reporter       [planned] │
│  • exact_match     │  │  • static HTML report     │
│  • regex           │  │  • JSON artifact          │
│  • llm_judge       │  │  • diff highlighting      │
└────────────────────┘  └───────────────────────────┘
```

## Roadmap

| Milestone | Scope |
|---|---|
| M1 — scaffold | repo init, CLI stubs, dependency pinning (done) |
| M2 — yaml schema + loader | Pydantic models, `load_suite()`, unit tests (done) |
| M3 — multi-model runner | async runner, Rich progress bar, RunResult (done) |
| M4 — scorers | `exact_match`, `regex`, `llm_judge` |
| M5 — reporter | static HTML report, JSON artifact, diff highlighting |
| M6 — polish | `eval diff`, caching, CI smoke test |

## Contributing

1. Fork the repo and create a feature branch.
2. Install dev dependencies: `pip install -e ".[dev]"`
3. Run tests: `pytest`
4. Lint: `ruff check src tests`
5. Open a pull request.

## License

MIT — see [LICENSE](LICENSE).
