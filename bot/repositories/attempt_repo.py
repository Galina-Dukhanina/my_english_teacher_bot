"""Журнал попыток упражнений и writing."""

from __future__ import annotations

import json

from database.db import get_connection


class AttemptRepository:
    def log_attempt(
        self,
        user_id: int,
        *,
        lesson_id: int | None = None,
        lesson_step_id: int | None = None,
        answer_text: str = "",
        result: dict | None = None,
        score: float | None = None,
    ) -> int:
        conn = get_connection()
        cur = conn.execute(
            """
            INSERT INTO exercise_attempts (
                user_id, lesson_id, lesson_step_id,
                answer_text, result_json, score
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                lesson_id,
                lesson_step_id,
                answer_text[:2000],
                json.dumps(result or {}, ensure_ascii=False),
                score,
            ),
        )
        attempt_id = int(cur.lastrowid)
        conn.commit()
        conn.close()
        return attempt_id
