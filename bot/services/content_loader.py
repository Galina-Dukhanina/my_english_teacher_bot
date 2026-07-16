"""Загрузка curriculum-контента из JSON в БД."""

from __future__ import annotations

import json
from pathlib import Path

from bot.repositories.curriculum_repo import CurriculumRepository

CONTENT_ROOT = Path(__file__).resolve().parent.parent.parent / "content" / "curriculum"
REQUIRED_MODULE_KEYS = ("goal", "cefr_level", "title")
REQUIRED_LESSON_KEYS = ("day_number", "title", "steps")
VALID_STEP_TYPES = {
    "review",
    "phrase",
    "explain",
    "exercise",
    "apply",
    "feedback",
    "listen",
    "voice",
}


def discover_module_files(root: Path | None = None) -> list[Path]:
    root = root or CONTENT_ROOT
    if not root.exists():
        return []
    return sorted(root.glob("**/module_*.json"))


def validate_module_data(data: dict) -> list[str]:
    errors: list[str] = []
    module = data.get("module")
    if not module:
        return ["missing module block"]
    for key in REQUIRED_MODULE_KEYS:
        if not module.get(key):
            errors.append(f"module.{key} required")
    lessons = data.get("lessons")
    if not lessons:
        errors.append("lessons list empty")
        return errors
    for i, lesson in enumerate(lessons):
        for key in REQUIRED_LESSON_KEYS:
            if key not in lesson:
                errors.append(f"lesson[{i}] missing {key}")
        for j, step in enumerate(lesson.get("steps", [])):
            if step.get("step_type") not in VALID_STEP_TYPES:
                errors.append(f"lesson[{i}] step[{j}] invalid step_type")
            if "sort_order" not in step:
                errors.append(f"lesson[{i}] step[{j}] missing sort_order")
    return errors


def load_module_file(path: Path, repo: CurriculumRepository | None = None) -> tuple[int, int]:
    repo = repo or CurriculumRepository()
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_module_data(data)
    if errors:
        raise ValueError(f"{path}: " + "; ".join(errors))

    module_id = repo.insert_module(data["module"])
    lesson_count = 0
    for lesson in data["lessons"]:
        steps = lesson["steps"]
        lesson_id = repo.insert_lesson(
            {
                "module_id": module_id,
                "day_number": lesson["day_number"],
                "title": lesson["title"],
                "estimated_minutes": lesson.get("estimated_minutes", 15),
            }
        )
        lesson_count += 1
        for step in steps:
            repo.insert_step(
                {
                    "lesson_id": lesson_id,
                    "sort_order": step["sort_order"],
                    "step_type": step["step_type"],
                    "payload": step.get("payload", {}),
                }
            )
    return module_id, lesson_count


def load_all_modules(root: Path | None = None) -> list[tuple[str, int, int]]:
    results = []
    for path in discover_module_files(root):
        module_id, n_lessons = load_module_file(path)
        results.append((str(path.relative_to(CONTENT_ROOT.parent)), module_id, n_lessons))
    return results
