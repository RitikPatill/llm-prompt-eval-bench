from pathlib import Path

import yaml

from eval_bench.schema import EvalSuite


def load_suite(path: str | Path) -> EvalSuite:
    """Load and validate an eval suite YAML file."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return EvalSuite.model_validate(raw)
