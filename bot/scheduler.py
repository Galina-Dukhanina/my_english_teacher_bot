"""Планировщик фоновых задач (напоминания)."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.services.reminders import send_reminders
from database.db import expire_premium_users

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _reminders_job(app):
    count = await send_reminders(app)
    if count:
        logger.info(f"Отправлено напоминаний: {count}")


async def _expire_premium_job(app):
    from bot import texts

    user_ids = expire_premium_users()
    for user_id in user_ids:
        try:
            await app.bot.send_message(chat_id=user_id, text=texts.PREMIUM_EXPIRED)
        except Exception as e:
            logger.error(f"Не удалось уведомить об истечении premium {user_id}: {e}")
    if user_ids:
        logger.info(f"Premium истёк у {len(user_ids)} пользователей")


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
    _scheduler.add_job(
        _expire_premium_job,
        "cron",
        hour=3,
        minute=0,
        args=[app],
        id="expire_premium",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Планировщик напоминаний запущен (интервал 1 мин)")
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler:
        try:
            _scheduler.shutdown(wait=False)
        except RuntimeError:
            # Event loop уже закрыт после run_polling — безопасно игнорируем
            pass
        _scheduler = None
