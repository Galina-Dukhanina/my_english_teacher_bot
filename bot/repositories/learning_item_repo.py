"""SRS-карточки пользователя (фразы и ошибки из уроков)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from database.db import get_connection


class LearningItemRepository:
    def find_by_ref(self, user_id: int, item_type: str, ref_id: str) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            """
            SELECT * FROM user_learning_items
            WHERE user_id = ? AND item_type = ? AND ref_id = ?
            """,
            (user_id, item_type, ref_id),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def insert_item(
        self,
        user_id: int,
        item_type: str,
        ref_id: str,
        content_json: dict,
        *,
        status: str = "new",
        interval_days: int = 1,
        next_review_at: str | None = None,
    ) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        if next_review_at is None:
            next_review_at = self._offset_review_at(interval_days)
        conn = get_connection()
        cur = conn.execute(
            """
            INSERT INTO user_learning_items (
                user_id, item_type, ref_id, content_json,
                status, interval_days, next_review_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                item_type,
                ref_id,
                json.dumps(content_json, ensure_ascii=False),
                status,
                interval_days,
                next_review_at,
            ),
        )
        item_id = cur.lastrowid
        conn.commit()
        conn.close()
        return int(item_id)

    def upsert_phrase(
        self,
        user_id: int,
        ref_id: str,
        content: dict,
        *,
        due_now: bool = False,
    ) -> int:
        existing = self.find_by_ref(user_id, "phrase", ref_id)
        if existing:
            if due_now and existing.get("status") != "mastered":
                self._mark_due_now(existing["id"])
            return int(existing["id"])

        next_at = datetime.now().isoformat(timespec="seconds") if due_now else None
        return self.insert_item(
            user_id,
            "phrase",
            ref_id,
            content,
            status="learning",
            interval_days=1,
            next_review_at=next_at,
        )

    def list_due(self, user_id: int, limit: int = 5) -> list[dict]:
        now = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT * FROM user_learning_items
            WHERE user_id = ?
              AND status != 'mastered'
              AND next_review_at IS NOT NULL
              AND next_review_at <= ?
            ORDER BY next_review_at ASC, error_count DESC, id ASC
            LIMIT ?
            """,
            (user_id, now, limit),
        ).fetchall()
        conn.close()
        return [self._row_to_dict(row) for row in rows]

    def count_due(self, user_id: int) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        row = conn.execute(
            """
            SELECT COUNT(*) AS n FROM user_learning_items
            WHERE user_id = ?
              AND status != 'mastered'
              AND next_review_at IS NOT NULL
              AND next_review_at <= ?
            """,
            (user_id, now),
        ).fetchone()
        conn.close()
        return int(row["n"] if row else 0)

    def count_by_status(self, user_id: int) -> dict[str, int]:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT status, COUNT(*) AS n
            FROM user_learning_items
            WHERE user_id = ?
            GROUP BY status
            """,
            (user_id,),
        ).fetchall()
        conn.close()
        return {row["status"]: int(row["n"]) for row in rows}

    def update_review_state(
        self,
        item_id: int,
        *,
        status: str,
        interval_days: int,
        correct_streak: int,
        error_count: int,
        next_review_at: str,
    ):
        now = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        conn.execute(
            """
            UPDATE user_learning_items
            SET status = ?,
                interval_days = ?,
                correct_streak = ?,
                error_count = ?,
                next_review_at = ?,
                last_reviewed_at = ?
            WHERE id = ?
            """,
            (
                status,
                interval_days,
                correct_streak,
                error_count,
                next_review_at,
                now,
                item_id,
            ),
        )
        conn.commit()
        conn.close()

    def _mark_due_now(self, item_id: int):
        now = datetime.now().isoformat(timespec="seconds")
        conn = get_connection()
        conn.execute(
            """
            UPDATE user_learning_items
            SET status = CASE WHEN status = 'mastered' THEN status ELSE 'weak' END,
                interval_days = 1,
                next_review_at = ?
            WHERE id = ?
            """,
            (now, item_id),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def _offset_review_at(interval_days: int) -> str:
        return (datetime.now() + timedelta(days=interval_days)).isoformat(
            timespec="seconds"
        )

    @staticmethod
    def _row_to_dict(row) -> dict:
        data = dict(row)
        raw = data.get("content_json")
        if raw:
            try:
                data["content"] = json.loads(raw)
            except json.JSONDecodeError:
                data["content"] = {}
        else:
            data["content"] = {}
        return data
