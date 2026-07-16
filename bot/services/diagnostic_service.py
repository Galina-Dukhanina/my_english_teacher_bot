"""Диагностика навыков Premium (Grammar, Vocabulary, …)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from bot.domain.levels import is_mvp_cefr
from bot.repositories.learning_profile_repo import LearningProfileRepository
from bot.services.premium_gate import check_program

logger = logging.getLogger(__name__)

KIND_DIAGNOSTIC = "diagnostic"
SKILLS = ("grammar", "vocabulary", "reading", "listening", "writing", "speaking")
CONTENT_PATH = (
    Path(__file__).resolve().parent.parent.parent / "content" / "diagnostic" / "skills_a1_b1.json"
)


@dataclass(frozen=True)
class DiagnosticQuestion:
    skill: str
    weight: int
    text: str
    options: tuple[str, ...]
    correct: int
    passage: str | None = None


def _load_questions() -> tuple[DiagnosticQuestion, ...]:
    raw = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    items = []
    for q in raw["questions"]:
        items.append(
            DiagnosticQuestion(
                skill=q["skill"],
                weight=int(q.get("weight", 1)),
                text=q["text"],
                options=tuple(q["options"]),
                correct=int(q["correct"]),
                passage=q.get("passage"),
            )
        )
    return tuple(items)


QUESTIONS: tuple[DiagnosticQuestion, ...] = _load_questions()


def can_take_diagnostic(user_id: int) -> tuple[bool, str]:
    access = check_program(user_id)
    if not access.allowed:
        return False, access.reason

    repo = LearningProfileRepository()
    skill_profile = repo.get_skill_profile(user_id)
    if skill_profile and skill_profile.get("diagnostic_at"):
        return False, "already_done"

    return True, "ok"


def score_skill_level(points: int, max_points: int) -> str:
    if max_points <= 0:
        return "A1"
    ratio = points / max_points
    if ratio < 0.34:
        return "A1"
    if ratio < 0.67:
        return "A2"
    return "B1"


def build_skill_profile(answers: list[bool]) -> dict[str, str]:
    """answers — bool по каждому вопросу в порядке QUESTIONS."""
    totals: dict[str, int] = {s: 0 for s in SKILLS}
    maxima: dict[str, int] = {s: 0 for s in SKILLS}

    for q, ok in zip(QUESTIONS, answers):
        maxima[q.skill] += q.weight
        if ok:
            totals[q.skill] += q.weight

    return {
        skill: score_skill_level(totals[skill], maxima[skill]) for skill in SKILLS
    }


def save_diagnostic_result(user_id: int, answers: list[bool]) -> dict[str, str]:
    skills = build_skill_profile(answers)
    repo = LearningProfileRepository()
    repo.upsert_skill_profile(
        user_id,
        grammar=skills["grammar"],
        vocabulary=skills["vocabulary"],
        reading=skills["reading"],
        listening=skills["listening"],
        writing=skills["writing"],
        speaking=skills["speaking"],
        diagnostic_at=datetime.now().isoformat(timespec="seconds"),
        source="premium_diagnostic",
    )
    for level in skills.values():
        if not is_mvp_cefr(level):
            logger.warning("Unexpected diagnostic level %s for user %s", level, user_id)
    return skills


def format_skill_profile(skills: dict[str, str]) -> str:
    from bot import texts

    labels = texts.DIAG_SKILL_LABELS
    lines = [f"• {labels.get(k, k)}: {skills[k]}" for k in SKILLS if k in skills]
    return "\n".join(lines)
