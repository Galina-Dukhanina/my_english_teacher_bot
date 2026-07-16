"""Загрузка curriculum JSON в SQLite."""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DB_PATH", str(ROOT / "bot_database_dev.db"))

from database.db import init_db, migrate_db
from bot.services.content_loader import discover_module_files, load_all_modules


def main():
    parser = argparse.ArgumentParser(description="Seed curriculum from content/curriculum/")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Очистить curriculum-таблицы перед загрузкой (dev only)",
    )
    args = parser.parse_args()

    init_db()
    migrate_db()

    files = discover_module_files()
    if not files:
        print("Нет файлов content/curriculum/**/module_*.json")
        print("Запусти: python scripts/build_mvp_curriculum.py")
        sys.exit(1)

    if args.rebuild:
        from database.db import get_connection

        conn = get_connection()
        conn.execute("DELETE FROM lesson_steps")
        conn.execute("DELETE FROM curriculum_lessons")
        conn.execute("DELETE FROM curriculum_modules")
        conn.commit()
        conn.close()
        print("Curriculum tables cleared.")

    results = load_all_modules()
    total_lessons = sum(n for _, _, n in results)
    print(f"Loaded {len(results)} modules, {total_lessons} lessons")
    for path, mid, n in results:
        print(f"  {path} -> module_id={mid}, lessons={n}")
    print(f"DB: {os.environ.get('DB_PATH')}")


if __name__ == "__main__":
    main()
