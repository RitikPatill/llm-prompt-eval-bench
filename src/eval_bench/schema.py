from typing import Literal
from pydantic import BaseModel, Field, model_validator

ScorerType = Literal["exact_match", "regex", "llm_judge"]


class EvalCase(BaseModel):
    id: str | None = None
    input: str
    expected: str | None = None
    models: list[str]
    scorer: ScorerType

    @model_validator(mode="after")
    def expected_required_for_deterministic_scorers(self) -> "EvalCase":
        if self.scorer in ("exact_match", "regex") and self.expected is None:
            raise ValueError(f"'expected' is required when scorer='{self.scorer}'")
        return self


class EvalSuite(BaseModel):
    name: str
    description: str | None = None
    cases: list[EvalCase] = Field(min_length=1)
