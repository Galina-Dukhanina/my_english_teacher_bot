"""Статус подписки и активация premium."""

import logging
from datetime import datetime

from database.db import (
    get_user,
    activate_premium as db_activate_premium,
    update_payment_status,
    get_payment_by_provider_id,
)

from bot.services.activation_notify import queue_premium_activated

logger = logging.getLogger(__name__)


def is_premium(user_id: int) -> bool:
    """True, если у пользователя активный premium."""
    user = get_user(user_id)
    if not user or not user.get("is_premium"):
        return False
    until = user.get("premium_until")
    if not until:
        return True
    try:
        return datetime.fromisoformat(until) > datetime.now()
    except ValueError:
        return bool(user.get("is_premium"))


def grant_premium(user_id: int, days: int, *, notify: bool = True):
    """Выдать premium на N дней (admin или webhook)."""
    db_activate_premium(user_id, days)
    if notify:
        queue_premium_activated(user_id, days=days, source="grant")
    logger.info(f"Premium активирован: user={user_id}, days={days}")


def complete_payment(provider_payment_id: str, user_id: int, plan: str, days: int):
    """Отметить платёж оплаченным и активировать premium."""
    record = get_payment_by_provider_id(provider_payment_id)
    if record and record.get("status") == "paid":
        return

    update_payment_status(
        provider_payment_id,
        "paid",
        paid_at=datetime.now().isoformat(timespec="seconds"),
    )
    grant_premium(user_id, days, notify=True)


def save_word_from_meaning(user_id: int, word: str, explanation: str):
    """Premium: сохранить слово из «Непонятно слово» в словарь."""
    from database.db import add_words_batch, sync_progress_words

    translation = explanation.strip().split("\n")[0][:200]
    add_words_batch(
        user_id,
        [
            {
                "word": word.strip(),
                "translation": translation or "—",
                "transcription": "",
                "example": "",
            }
        ],
        "из диалога",
    )
    sync_progress_words(user_id)
