# LLM Prompt Eval Bench

> A lightweight CLI tool to define, run, and diff LLM prompt evaluations across models, with scored HTML reports.

![demo](demo/demo.gif)

## What it is

`llm-prompt-eval-bench` is a local evaluation harness for LLM prompts. You write test cases in a
YAML file — each with an input, an expected output or rubric, and a list of models to run against —
and the tool fans out all `(case, model)` pairs concurrently, scores each result, and saves a static
HTML report plus a JSON artifact to `.eval_reports/`.

It supports three scorer types: exact string match, regex match, and `llm_judge` (a small model
grades outputs 1–5). Both OpenAI and Anthropic models are supported via their official SDKs. No
cloud account beyond API keys, no persistent server, no framework lock-in.

## Quickstart

Requires Python >= 3.10.

```bash
git clone https://github.com/RitikPatill/llm-prompt-eval-bench.git
cd llm-prompt-eval-bench
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .

# Set API keys for the providers you plan to use
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Run the bundled demo suite (3 cases, 2 models)
eval run examples/demo_suite.yaml

# Open the report in your browser
eval report last
```

## Usage

Define a suite in YAML:

```yaml
name: my suite

cases:
  - id: greeting
    input: "Reply with exactly the word: hello"
    expected: "hello"
    models:
      - openai/gpt-4o-mini
      - anthropic/claude-haiku-4-5-20251001
    scorer: exact_match

  - id: year-check
    input: "What year did World War 2 end? Reply with only the 4-digit year."
    expected: "^\\d{4}$"
    models:
      - openai/gpt-4o-mini
    scorer: regex

  - id: open-ended
    input: "Write a haiku about debugging code."
    models:
      - openai/gpt-4o-mini
      - anthropic/claude-haiku-4-5-20251001
    scorer: llm_judge
```

Run it with `eval run suite.yaml`. Two files are written to `.eval_reports/`:
- `run_<timestamp>.html` — summary table, expandable per-case rows, divergence highlighting
- `run_<timestamp>.json` — same data, machine-readable

`eval report last` opens the most recent HTML in your system browser.

### Scorer reference

| Scorer | `expected` | Score | Description |
|---|---|---|---|
| `exact_match` | required | 0.0 or 1.0 | Case-sensitive equality after whitespace strip |
| `regex` | required | 0.0 or 1.0 | `re.search(expected, output)` |
| `llm_judge` | optional | 1.0 – 5.0 | Small model grades the output 1–5 |

### Model strings

Prefix with `openai/` or `anthropic/`. Any model name the respective SDK accepts works:

```
openai/gpt-4o-mini
openai/gpt-4o
anthropic/claude-haiku-4-5-20251001
anthropic/claude-sonnet-4-6
```

## Architecture

```
┌──────────────────────────────────────┐
│  CLI  (eval run / eval report)       │
│  cli.py                              │
└──────────────────┬───────────────────┘
                   │ suite path
                   ▼
┌──────────────────────────────────────┐
│  Schema + Loader                     │
│  schema.py — EvalCase, EvalSuite     │
│  loader.py — load_suite(path)        │
└──────────────────┬───────────────────┘
                   │ List[EvalCase]
                   ▼
┌──────────────────────────────────────┐
│  Runner  (async, concurrent)         │
│  runner.py — run_suite(), RunResult  │
└────────────┬─────────────────────────┘
             │ List[RunResult]
       ┌─────┴──────┐
       ▼            ▼
┌────────────┐  ┌──────────────────────┐
│  Scorers   │  │  Reporter            │
│  exact_match  │  HTML + JSON output  │
│  regex     │  │  diff highlighting   │
│  llm_judge │  └──────────────────────┘
└────────────┘
```

## Project structure

```
llm-prompt-eval-bench/
├── src/eval_bench/       # library source: cli, schema, loader, runner, scorers, reporter
├── tests/                # 34 unit tests (all mocked, no API keys required)
├── examples/             # demo_suite.yaml — 3-case runnable example
├── demo/                 # demo.gif + demo.tape (VHS script to regenerate GIF)
├── pyproject.toml        # package config, entry point: eval
├── requirements.txt      # pinned runtime deps
└── requirements-dev.txt  # pinned dev deps (pytest, ruff)
```

## Roadmap

- [ ] CSV and JSONL dataset loaders so inline YAML examples are not required for large suites
- [ ] `eval diff run_a.json run_b.json` command to compare two runs side by side
- [ ] `--concurrency` flag and configurable per-suite timeout
- [ ] Local model support via Ollama for offline / GPU-free evaluation
- [ ] GitHub Actions workflow to run evals on every PR and post score deltas as a comment

## License

MIT — see [LICENSE](LICENSE).

---

Built autonomously by [autodev](https://github.com/RitikPatill/autodev),
a multi-agent orchestrator I designed. Each commit in this repo was
authored by me; the implementation work was performed by Sonnet under
the orchestrator's control. Read the orchestrator's README to see how.
