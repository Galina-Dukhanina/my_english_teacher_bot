"""Журнал показанных фраз дня."""

from __future__ import annotations

from datetime import datetime

from database.db import get_connection


class DailyPhraseRepository:
    def get_log(self, user_id: int, phrase_date: str) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            """
            SELECT * FROM daily_phrases_log
            WHERE user_id = ? AND phrase_date = ?
            """,
            (user_id, phrase_date),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def was_sent_today(self, user_id: int, phrase_date: str) -> bool:
        return self.get_log(user_id, phrase_date) is not None

    def log_phrase(
        self,
        user_id: int,
        phrase_date: str,
        phrase_id: str,
        module_id: int | None = None,
    ):
        now = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        conn.execute(
            """
            INSERT OR REPLACE INTO daily_phrases_log (
                user_id, phrase_date, phrase_id, module_id, shown_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, phrase_date, phrase_id, module_id, now),
        )
        conn.commit()
        conn.close()
