"""SRS: регистрация фраз из уроков и повторение перед уроком."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from config import PREMIUM_REVIEW_BATCH_SIZE
from bot.domain.review import (
    LearningItemStatus,
    ReviewResult,
    ReviewState,
    apply_review,
    initial_interval_days,
)
from bot.repositories.learning_item_repo import LearningItemRepository

logger = logging.getLogger(__name__)

ITEM_TYPE_PHRASE = "phrase"


class ReviewEngine:
    def __init__(self):
        self._items = LearningItemRepository()

    @staticmethod
    def phrase_ref_id(module_id: int, phrase_id: str) -> str:
        return f"{module_id}:{phrase_id}"

    def has_due_items(self, user_id: int) -> bool:
        return self._items.count_due(user_id) > 0

    def register_phrase(
        self,
        user_id: int,
        module_id: int,
        payload: dict,
        *,
        due_now: bool = False,
    ) -> int | None:
        phrase_id = payload.get("phrase_id")
        if not phrase_id:
            return None
        ref_id = self.phrase_ref_id(module_id, phrase_id)
        content = {
            "phrase_en": payload.get("phrase_en", ""),
            "phrase_ru": payload.get("phrase_ru", ""),
            "phrase_id": phrase_id,
            "module_id": module_id,
        }
        return self._items.upsert_phrase(
            user_id, ref_id, content, due_now=due_now
        )

    def register_exercise_miss(
        self, user_id: int, module_id: int, session: dict
    ) -> int | None:
        phrase_payload = self._last_phrase_payload(session)
        if not phrase_payload:
            return None
        return self.register_phrase(
            user_id, module_id, phrase_payload, due_now=True
        )

    def get_due_batch(self, user_id: int) -> list[dict]:
        rows = self._items.list_due(user_id, limit=PREMIUM_REVIEW_BATCH_SIZE)
        return [self._to_review_card(row) for row in rows]

    def submit_review(
        self, user_id: int, item_id: int, result: ReviewResult
    ) -> dict | None:
        row = self._get_owned_item(user_id, item_id)
        if not row:
            return None

        state = ReviewState(
            status=row.get("status") or LearningItemStatus.NEW,
            interval_days=int(row.get("interval_days") or initial_interval_days()),
            correct_streak=int(row.get("correct_streak") or 0),
            error_count=int(row.get("error_count") or 0),
        )
        next_state = apply_review(state, result)
        next_review_at = self._schedule_at(next_state.interval_days)

        self._items.update_review_state(
            item_id,
            status=next_state.status,
            interval_days=next_state.interval_days,
            correct_streak=next_state.correct_streak,
            error_count=next_state.error_count,
            next_review_at=next_review_at,
        )
        logger.debug(
            "review user=%s item=%s result=%s next=%s",
            user_id,
            item_id,
            result,
            next_state.status,
        )
        return {
            "item_id": item_id,
            "result": result,
            "status": next_state.status,
            "interval_days": next_state.interval_days,
            "phrase_en": row.get("content", {}).get("phrase_en", ""),
            "phrase_ru": row.get("content", {}).get("phrase_ru", ""),
        }

    def _get_owned_item(self, user_id: int, item_id: int) -> dict | None:
        conn_items = self._items
        from database.db import get_connection

        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM user_learning_items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        ).fetchone()
        conn.close()
        if not row:
            return None
        return conn_items._row_to_dict(row)

    @staticmethod
    def _to_review_card(row: dict) -> dict:
        content = row.get("content") or {}
        return {
            "id": row["id"],
            "phrase_en": content.get("phrase_en", ""),
            "phrase_ru": content.get("phrase_ru", ""),
            "status": row.get("status"),
        }

    @staticmethod
    def _schedule_at(interval_days: int) -> str:
        days = max(interval_days, 1)
        return (datetime.now() + timedelta(days=days)).isoformat(timespec="seconds")

    @staticmethod
    def _last_phrase_payload(session: dict) -> dict | None:
        step_index = session.get("step_index", 0)
        steps = session.get("steps") or []
        for step in reversed(steps[:step_index]):
            if step.get("step_type") == "phrase":
                return step.get("payload") or {}
        return None


review_engine = ReviewEngine()
