"""Загрузка dev-модуля curriculum в SQLite (локальная разработка)."""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DB_PATH", str(ROOT / "bot_database_dev.db"))

from database.db import init_db, migrate_db
from bot.repositories.curriculum_repo import CurriculumRepository


def load_module(path: Path) -> tuple[int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    repo = CurriculumRepository()

    module_data = data["module"]
    module_id = repo.insert_module(module_data)

    lesson_count = 0
    for lesson in data.get("lessons", []):
        steps = lesson.pop("steps", [])
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


def main():
    init_db()
    migrate_db()

    content_path = ROOT / "content" / "dev" / "work_a1_module.json"
    if not content_path.exists():
        print(f"Файл не найден: {content_path}")
        sys.exit(1)

    module_id, lesson_count = load_module(content_path)
    print(f"OK: module_id={module_id}, lessons={lesson_count}")
    print(f"DB: {os.environ.get('DB_PATH')}")


if __name__ == "__main__":
    main()
