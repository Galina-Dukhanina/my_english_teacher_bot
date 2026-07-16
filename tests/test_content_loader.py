from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_discover_modules_after_build():
    from bot.services.content_loader import discover_module_files, validate_module_data
    import json

    files = discover_module_files(ROOT / "content" / "curriculum")
    assert len(files) >= 15
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_module_data(data)
        assert errors == [], f"{path}: {errors}"


def test_a1_week_has_five_lessons():
    import json

    path = ROOT / "content" / "curriculum" / "work" / "A1" / "module_1.json"
    if not path.exists():
        pytest.skip("run scripts/build_mvp_curriculum.py first")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["lessons"]) == 5
