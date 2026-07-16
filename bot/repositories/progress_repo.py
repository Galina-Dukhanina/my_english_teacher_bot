"""Прогресс пользователя по модулям и урокам."""

from datetime import datetime

from database.db import get_connection


class ProgressRepository:
    def get_module_progress(self, user_id: int, module_id: int) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            """
            SELECT * FROM user_module_progress
            WHERE user_id = ? AND module_id = ?
            """,
            (user_id, module_id),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def ensure_module_progress(self, user_id: int, module_id: int) -> dict:
        row = self.get_module_progress(user_id, module_id)
        if row:
            return row
        now = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO user_module_progress (user_id, module_id, status, started_at)
            VALUES (?, ?, 'in_progress', ?)
            """,
            (user_id, module_id, now),
        )
        conn.commit()
        conn.close()
        return self.get_module_progress(user_id, module_id) or {}

    def set_module_status(
        self,
        user_id: int,
        module_id: int,
        status: str,
        *,
        week_check_score: float | None = None,
    ):
        now = datetime.now().isoformat(timespec="seconds")
        fields = ["status = ?"]
        params: list = [status]
        if status == "completed":
            fields.append("completed_at = ?")
            params.append(now)
        if week_check_score is not None:
            fields.append("week_check_score = ?")
            params.append(week_check_score)
        params.extend([user_id, module_id])
        conn = get_connection()
        conn.execute(
            f"""
            UPDATE user_module_progress
            SET {", ".join(fields)}
            WHERE user_id = ? AND module_id = ?
            """,
            params,
        )
        conn.commit()
        conn.close()

    def get_lesson_progress(self, user_id: int, lesson_id: int) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            """
            SELECT * FROM user_lesson_progress
            WHERE user_id = ? AND lesson_id = ?
            """,
            (user_id, lesson_id),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def list_lesson_progress_for_module(
        self, user_id: int, module_id: int
    ) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT lp.* FROM user_lesson_progress lp
            JOIN curriculum_lessons cl ON cl.id = lp.lesson_id
            WHERE lp.user_id = ? AND cl.module_id = ?
            ORDER BY cl.day_number, cl.id
            """,
            (user_id, module_id),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def mark_lesson_started(self, user_id: int, lesson_id: int, step_id: int | None = None):
        now = datetime.now().isoformat(timespec="seconds")
        existing = self.get_lesson_progress(user_id, lesson_id)
        conn = get_connection()
        if existing:
            conn.execute(
                """
                UPDATE user_lesson_progress
                SET status = 'in_progress',
                    current_step_id = COALESCE(?, current_step_id),
                    started_at = COALESCE(started_at, ?)
                WHERE user_id = ? AND lesson_id = ?
                """,
                (step_id, now, user_id, lesson_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO user_lesson_progress (
                    user_id, lesson_id, status, current_step_id, started_at
                ) VALUES (?, ?, 'in_progress', ?, ?)
                """,
                (user_id, lesson_id, step_id, now),
            )
        conn.commit()
        conn.close()

    def mark_lesson_completed(
        self,
        user_id: int,
        lesson_id: int,
        *,
        score_summary_json: str | None = None,
    ):
        now = datetime.now().isoformat(timespec="seconds")
        existing = self.get_lesson_progress(user_id, lesson_id)
        conn = get_connection()
        if existing:
            conn.execute(
                """
                UPDATE user_lesson_progress
                SET status = 'completed',
                    completed_at = ?,
                    score_summary_json = COALESCE(?, score_summary_json)
                WHERE user_id = ? AND lesson_id = ?
                """,
                (now, score_summary_json, user_id, lesson_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO user_lesson_progress (
                    user_id, lesson_id, status, completed_at, score_summary_json
                ) VALUES (?, ?, 'completed', ?, ?)
                """,
                (user_id, lesson_id, now, score_summary_json),
            )
        conn.commit()
        conn.close()

    def count_due_review_items(self, user_id: int) -> int:
        from bot.repositories.learning_item_repo import LearningItemRepository

        return LearningItemRepository().count_due(user_id)
