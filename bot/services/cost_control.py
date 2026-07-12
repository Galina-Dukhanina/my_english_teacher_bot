import logging
from datetime import date

from config import DAILY_COST_LIMIT_USD
from database.db import get_today_ai_spend, record_ai_usage

logger = logging.getLogger(__name__)

DEFAULT_INPUT_COST_PER_M = 0.50
DEFAULT_OUTPUT_COST_PER_M = 1.50

LIMIT_EXCEEDED_MESSAGE = (
    "Сейчас я временно не могу обращаться к AI — достигнут дневной лимит расходов. "
    "Попробуй завтра или напиши позже."
)

_limit_alert_sent_for_date = None


def estimate_cost(tokens_in: int, tokens_out: int, model: str) -> float:
    """Примерная стоимость запроса в USD."""
    del model
    cost_in = (tokens_in or 0) / 1_000_000 * DEFAULT_INPUT_COST_PER_M
    cost_out = (tokens_out or 0) / 1_000_000 * DEFAULT_OUTPUT_COST_PER_M
    return round(cost_in + cost_out, 6)


def is_daily_limit_reached() -> bool:
    """True, если сегодняшние расходы на AI достигли потолка."""
    return get_today_ai_spend() >= DAILY_COST_LIMIT_USD


def log_ai_usage(user_id: int | None, usage: dict) -> float:
    """Записать расход в ai_usage. Возвращает cost_estimate."""
    if not usage:
        return 0.0
    tokens_in = usage.get("tokens_in") or 0
    tokens_out = usage.get("tokens_out") or 0
    model = usage.get("model") or ""
    cost = estimate_cost(tokens_in, tokens_out, model)
    record_ai_usage(user_id, tokens_in, tokens_out, model, cost)
    return cost


def should_alert_admin_on_limit() -> bool:
    """Один алерт admin в день при превышении лимита."""
    global _limit_alert_sent_for_date
    today = date.today().isoformat()
    if not is_daily_limit_reached():
        return False
    if _limit_alert_sent_for_date == today:
        return False
    _limit_alert_sent_for_date = today
    return True
