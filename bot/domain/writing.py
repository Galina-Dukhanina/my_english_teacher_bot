"""Результат проверки writing (шаг apply)."""

from __future__ import annotations

from dataclasses import dataclass, field


PASS_SCORE_THRESHOLD = 0.6


@dataclass(frozen=True)
class WritingCheckResult:
    passed: bool
    score: float
    feedback_ru: str
    corrected_text: str = ""
    errors: list[str] = field(default_factory=list)
    raw: dict | None = None

    @classmethod
    def from_payload(cls, data: dict) -> WritingCheckResult:
        score = float(data.get("score", 0))
        passed = bool(data.get("passed", False)) and score >= PASS_SCORE_THRESHOLD
        corrected = (data.get("corrected_text") or "").strip()
        feedback = (data.get("feedback_ru") or "").strip()
        errors = data.get("errors") or []
        if not isinstance(errors, list):
            errors = [str(errors)]
        errors = [str(e).strip() for e in errors if str(e).strip()]
        return cls(
            passed=passed,
            score=score,
            feedback_ru=feedback,
            corrected_text=corrected,
            errors=errors,
            raw=data,
        )
