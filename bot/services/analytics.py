"""Агрегации для admin-команды /stats."""

from database.db import (
    count_users,
    count_onboarded_users,
    get_dau_last_days,
    get_top_events,
    get_funnel_counts,
    get_today_ai_spend,
    count_new_feedback,
    count_premium_users,
)


def get_admin_stats(days: int = 7) -> dict:
    """Сводка метрик для admin."""
    return {
        "total_users": count_users(),
        "onboarded_users": count_onboarded_users(),
        "dau": get_dau_last_days(days),
        "top_events": get_top_events(days, limit=8),
        "funnel": get_funnel_counts(),
        "ai_spend_today": get_today_ai_spend(),
        "new_feedback": count_new_feedback(),
        "premium_users": count_premium_users(),
    }


def format_admin_stats(stats: dict, daily_limit_usd: float) -> str:
    """Форматировать stats в текст для Telegram."""
    lines = [
        "📊 Статистика бота",
        "",
        f"Пользователи: {stats['total_users']} "
        f"(онбординг: {stats['onboarded_users']}, premium: {stats['premium_users']})",
        "",
        f"DAU ({len(stats['dau'])} дн):",
    ]

    if stats["dau"]:
        for day, count in stats["dau"]:
            lines.append(f"  {day}: {count}")
    else:
        lines.append("  нет данных")

    lines.extend(["", "Топ событий:"])
    if stats["top_events"]:
        for event_type, count in stats["top_events"]:
            lines.append(f"  {event_type}: {count}")
    else:
        lines.append("  нет данных")

    funnel = stats["funnel"]
    lines.extend(
        [
            "",
            "Воронка (уник. пользователи):",
            f"  /start → {funnel.get('start', 0)}",
            f"  онбординг → {funnel.get('onboarding_done', 0)}",
            f"  диалог → {funnel.get('dialog', 0)}",
            "",
            f"AI сегодня: ${stats['ai_spend_today']:.4f} / ${daily_limit_usd:.2f}",
            f"Новых отзывов: {stats['new_feedback']}",
        ]
    )
    return "\n".join(lines)
