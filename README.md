# llm-prompt-eval-bench

> One YAML file. One command. One report.

## What it does

`llm-prompt-eval-bench` is a lightweight, local evaluation harness for LLM prompts.
You define test cases in a YAML file — each with an input, an expected output or rubric,
and a list of models to run against — and the tool runs all combinations, scores them,
and emits a static HTML report plus a JSON artifact.

No cloud account required. No opaque framework. Just a YAML file and a single command.

## Status

**M1 — scaffold (current)**

| Deliverable | State |
|---|---|
| `pyproject.toml` with entry point `eval` | done |
| `requirements.txt` / `requirements-dev.txt` | done |
| MIT `LICENSE` | done |
| `src/eval_bench/cli.py` — `eval run` and `eval report` registered | stub |
| `tests/` scaffold | done |

The `eval run` and `eval report` commands are wired and importable; they print
`not yet implemented` until M2 ships the runner.

## Quick-start

Requires Python >= 3.10.

```bash
# Install
pip install -e .

# Verify the CLI is registered (commands are stubs until M2)
eval --help

# Write your eval suite
cat > suite.yaml << 'EOF'
# [TODO M2 — example suite will go here]
EOF

# Run the evaluation  (not yet implemented — M2)
eval run suite.yaml

# Re-open the last report  (not yet implemented — M5)
eval report last
```

Set your API keys before running:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

## Suite YAML format

[TODO M2 — schema table: `input`, `expected`, `models`, `scorer` fields]

## Scorers

[TODO M4 — documentation for `exact_match`, `regex`, and `llm_judge` scorers]

## Report output

[TODO M5 — description of the static HTML report and JSON artifact]

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  CLI  (eval run / eval report)                      │
│  src/eval_bench/cli.py                              │
└────────────────────┬────────────────────────────────┘
                     │ loads suite.yaml
                     ▼
┌─────────────────────────────────────────────────────┐
│  Runner                                             │
│  • iterates (test_case × model) combinations        │
│  • calls OpenAI / Anthropic SDKs                   │
│  • rich progress bar                               │
└────────────┬──────────────────┬─────────────────────┘
             │                  │
             ▼                  ▼
┌────────────────────┐  ┌───────────────────────────┐
│  Scorers           │  │  Reporter                 │
│  • exact_match     │  │  • static HTML report     │
│  • regex           │  │  • JSON artifact          │
│  • llm_judge       │  │  • diff highlighting      │
└────────────────────┘  └───────────────────────────┘
```

## Roadmap

| Milestone | Scope |
|---|---|
| M1 — scaffold | repo init, CLI stubs, dependency pinning (done) |
| M2 — runner | YAML loader, model dispatch, OpenAI + Anthropic adapters |
| M3 — scorers | `exact_match`, `regex`, `llm_judge` |
| M4 — reporter | static HTML report, JSON artifact, diff highlighting |
| M5 — polish | `eval diff`, caching, CI smoke test |

## Contributing

1. Fork the repo and create a feature branch.
2. Install dev dependencies: `pip install -e ".[dev]"`
3. Run tests: `pytest`
4. Lint: `ruff check src tests`
5. Open a pull request.

## License

MIT — see [LICENSE](LICENSE).
