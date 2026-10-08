import pytest
from pydantic import ValidationError

from eval_bench import EvalCase, EvalSuite, load_suite

FIXTURE = "tests/fixtures/simple_suite.yaml"


def test_load_valid_suite():
    suite = load_suite(FIXTURE)
    assert suite.name == "smoke test suite"
    assert len(suite.cases) == 3


def test_eval_case_types():
    suite = load_suite(FIXTURE)
    assert suite.cases[0].scorer == "exact_match"
    assert suite.cases[1].scorer == "regex"
    assert suite.cases[2].scorer == "llm_judge"
    assert suite.cases[2].expected is None


def test_exact_match_requires_expected():
    with pytest.raises(ValidationError):
        EvalCase(input="test", models=["openai/gpt-4o-mini"], scorer="exact_match")


def test_regex_requires_expected():
    with pytest.raises(ValidationError):
        EvalCase(input="test", models=["openai/gpt-4o-mini"], scorer="regex")


def test_empty_cases_rejected():
    with pytest.raises(ValidationError):
        EvalSuite(name="empty", cases=[])


def test_invalid_scorer_rejected():
    with pytest.raises(ValidationError):
        EvalCase(input="test", expected="x", models=["openai/gpt-4o-mini"], scorer="nonexistent")


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_suite("nonexistent.yaml")
