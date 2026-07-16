#!/usr/bin/env python3
"""Preflight QA перед тестом Premium и деплоем на prod.

Запуск:
  python scripts/qa_preflight.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Изолированная БД для проверки миграций
os.environ.setdefault("DB_PATH", str(ROOT / "tests" / "tmp_qa_preflight.db"))


def _ok(msg: str):
    print(f"  OK  {msg}")


def _warn(msg: str):
    print(f"  WARN {msg}")


def _fail(msg: str):
    print(f"  FAIL {msg}")
    return False


def check_env() -> bool:
    print("\n== Env ==")
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    ok = True
    required = ["BOT_TOKEN", "OPENROUTER_API_KEY", "ADMIN_USER_ID"]
    for key in required:
        if os.getenv(key):
            _ok(key)
        else:
            ok = _fail(f"{key} не задан") and ok

    if os.getenv("MODEL_ANALYSIS"):
        _ok("MODEL_ANALYSIS")
    else:
        _warn("MODEL_ANALYSIS не задан — будет использован fallback из config")

    from bot.services.premium_gate import sales_enabled, validate_sales_configuration

    if sales_enabled():
        _warn("PREMIUM_SALES_ENABLED=true — продажи включены")
        for w in validate_sales_configuration():
            ok = _fail(w) and ok
    else:
        _ok("PREMIUM_SALES_ENABLED=false (dev/staging)")

    proxy = os.getenv("PROXY_URL")
    if proxy and proxy.startswith("socks") and "socksio" not in sys.modules:
        _warn(f"PROXY_URL={proxy} — на prod убедись, что socksio установлен или прокси отключён")

    return ok


def check_imports() -> bool:
    print("\n== Imports ==")
    modules = [
        "bot.main",
        "bot.services.premium_gate",
        "bot.services.lesson_engine",
        "bot.services.lesson_runner",
        "bot.services.review_engine",
        "bot.services.ai_gateway",
        "bot.services.daily_phrase_service",
        "bot.services.progress_report_service",
        "bot.services.activation_notify",
    ]
    ok = True
    for name in modules:
        try:
            __import__(name)
            _ok(name)
        except Exception as exc:
            ok = _fail(f"{name}: {exc}") and ok

    from config import PAYMENT_PROVIDER

    if PAYMENT_PROVIDER == "yookassa":
        try:
            __import__("bot.web.server")
            _ok("bot.web.server (yookassa)")
        except Exception as exc:
            ok = _fail(f"bot.web.server: {exc} — нужен для webhook") and ok
    else:
        _ok("bot.web.server — пропуск (PAYMENT_PROVIDER != yookassa)")

    return ok


def check_db() -> bool:
    print("\n== Database ==")
    db_path = Path(os.environ["DB_PATH"])
    if db_path.exists():
        db_path.unlink()

    from database.db import init_db, migrate_db, get_connection

    init_db()
    migrate_db()

    conn = get_connection()
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()

    required = {
        "learning_profiles",
        "skill_profiles",
        "curriculum_modules",
        "curriculum_lessons",
        "lesson_steps",
        "user_learning_items",
        "daily_phrases_log",
        "bot_notifications",
        "exercise_attempts",
    }
    ok = True
    for table in sorted(required):
        if table in tables:
            _ok(f"table {table}")
        else:
            ok = _fail(f"нет таблицы {table}") and ok
    return ok


def check_curriculum() -> bool:
    print("\n== Curriculum ==")
    from bot.services.content_loader import discover_module_files, validate_module_data

    files = discover_module_files()
    if len(files) < 15:
        return _fail(f"ожидалось >=15 модулей, найдено {len(files)}")

    _ok(f"{len(files)} JSON-модулей")
    ok = True
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_module_data(data)
        if errors:
            ok = _fail(f"{path.name}: {errors}") and ok
    return ok


def check_domain() -> bool:
    print("\n== Domain logic ==")
    from bot.domain.review import ReviewResult, ReviewState, apply_review
    from bot.domain.writing import WritingCheckResult

    state = ReviewState(status="learning", interval_days=2, correct_streak=1, error_count=0)
    nxt = apply_review(state, ReviewResult.CORRECT)
    if nxt.correct_streak != 2:
        return _fail("SRS apply_review")

    wr = WritingCheckResult.from_payload(
        {"passed": True, "score": 0.8, "feedback_ru": "ok", "corrected_text": "Hi"}
    )
    if not wr.passed:
        return _fail("writing pass threshold")

    _ok("SRS intervals")
    _ok("writing check schema")
    return True


def main() -> int:
    print("Preflight QA — Premium English Teacher Bot")
    checks = [
        check_env,
        check_imports,
        check_db,
        check_curriculum,
        check_domain,
    ]
    ok = True
    for fn in checks:
        if not fn():
            ok = False

    print("\n== Result ==")
    if ok:
        print("  PASS — можно переходить к ручному тесту Premium")
        print("\n  Дальше (dev):")
        print("    python scripts/seed_curriculum.py --rebuild")
        print("    python -m bot.main")
        print("    /grant_premium YOUR_ID 30")
        return 0

    print("  FAIL — исправь ошибки перед деплоем")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
