"""Уведомления пользователю после активации Premium (очередь + scheduler)."""

from __future__ import annotations

import json
import logging

from telegram import InlineKeyboardMarkup

from bot.i18n import t
from database.db import (
    enqueue_bot_notification,
    list_pending_bot_notifications,
    mark_bot_notification_sent,
)

logger = logging.getLogger(__name__)

KIND_PREMIUM_ACTIVATED = "premium_activated"


def queue_premium_activated(user_id: int, *, days: int, source: str = "payment"):
    enqueue_bot_notification(
        user_id,
        KIND_PREMIUM_ACTIVATED,
        {"days": days, "source": source},
    )


def _activation_keyboard(user_id: int) -> InlineKeyboardMarkup:
    from bot.handlers.premium_onboarding import premium_setup_keyboard

    return premium_setup_keyboard(user_id)


async def send_pending_notifications(app) -> int:
    sent = 0
    for row in list_pending_bot_notifications(limit=30):
        user_id = row["user_id"]
        kind = row["kind"]
        try:
            if kind == KIND_PREMIUM_ACTIVATED:
                payload = json.loads(row.get("payload_json") or "{}")
                days = int(payload.get("days") or 30)
                await app.bot.send_message(
                    chat_id=user_id,
                    text=t("PREMIUM_ACTIVATED_USER", user_id=user_id, days=days),
                    reply_markup=_activation_keyboard(user_id),
                )
            mark_bot_notification_sent(row["id"])
            sent += 1
        except Exception as exc:
            logger.error(
                "Notification failed id=%s user=%s kind=%s: %s",
                row["id"],
                user_id,
                kind,
                exc,
            )
    return sent
