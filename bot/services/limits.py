"""Дневные лимиты бесплатного тарифа (задел под Этап 5)."""

from bot.services.subscription import is_premium


def check_limit(user_id: int, action: str) -> bool:
    """True — действие разрешено. Пока premium и free без ограничений."""
    del action
    if is_premium(user_id):
        return True
    return True
