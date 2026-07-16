"""Профиль обучения и skill profile."""

import json
from datetime import datetime

from database.db import get_connection


class LearningProfileRepository:
    def get(self, user_id: int) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM learning_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def upsert_from_user(
        self,
        user_id: int,
        *,
        cefr_level: str,
        display_level: str | None,
        goal: str | None,
        ui_language: str = "ru",
    ) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO learning_profiles (
                user_id, cefr_level, display_level, goal, ui_language, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                cefr_level = excluded.cefr_level,
                display_level = excluded.display_level,
                goal = COALESCE(excluded.goal, learning_profiles.goal),
                ui_language = excluded.ui_language,
                updated_at = excluded.updated_at
            """,
            (user_id, cefr_level, display_level, goal, ui_language, now),
        )
        conn.commit()
        conn.close()

    def update_fields(self, user_id: int, **fields) -> None:
        if not fields:
            return
        fields["updated_at"] = datetime.now().isoformat(timespec="seconds")
        cols = ", ".join(f"{k} = ?" for k in fields)
        conn = get_connection()
        conn.execute(
            f"UPDATE learning_profiles SET {cols} WHERE user_id = ?",
            (*fields.values(), user_id),
        )
        conn.commit()
        conn.close()

    def get_skill_profile(self, user_id: int) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM skill_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def upsert_skill_profile(self, user_id: int, **skills) -> None:
        conn = get_connection()
        existing = conn.execute(
            "SELECT user_id FROM skill_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if existing:
            cols = ", ".join(f"{k} = ?" for k in skills)
            conn.execute(
                f"UPDATE skill_profiles SET {cols} WHERE user_id = ?",
                (*skills.values(), user_id),
            )
        else:
            keys = ["user_id", *skills.keys()]
            placeholders = ", ".join("?" for _ in keys)
            conn.execute(
                f"INSERT INTO skill_profiles ({', '.join(keys)}) VALUES ({placeholders})",
                (user_id, *skills.values()),
            )
        conn.commit()
        conn.close()

    @staticmethod
    def parse_interests(profile: dict | None) -> list[str]:
        if not profile:
            return []
        raw = profile.get("interests_json")
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []
