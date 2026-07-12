"""Планировщик фоновых задач (напоминания)."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.services.reminders import send_reminders

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _reminders_job(app):
    count = await send_reminders(app)
    if count:
        logger.info(f"Отправлено напоминаний: {count}")


def start_scheduler(app):
    """Запустить APScheduler и привязать к event loop бота."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _reminders_job,
        "interval",
        minutes=1,
        args=[app],
        id="send_reminders",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Планировщик напоминаний запущен (интервал 1 мин)")
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
