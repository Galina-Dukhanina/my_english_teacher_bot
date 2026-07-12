import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID
from database.db import get_user, set_pending_action, save_feedback, log_event
from bot import texts, keyboards

logger = logging.getLogger(__name__)


async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /feedback — попросить написать отзыв."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user["onboarding_done"]:
        await update.message.reply_text("Сначала пройди онбординг: /start")
        return

    set_pending_action(user_id, "wait_feedback")
    log_event(user_id, "feedback_start")
    await update.message.reply_text(texts.FEEDBACK_ASK)


async def submit_feedback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, text: str
):
    """Принять текст отзыва и уведомить admin."""
    set_pending_action(user_id, None)
    save_feedback(user_id, text.strip())
    log_event(user_id, "feedback_sent")

    await update.message.reply_text(
        texts.FEEDBACK_THANKS,
        reply_markup=keyboards.main_keyboard(),
    )

    if ADMIN_USER_ID:
        user = update.effective_user
        name = user.first_name or "Пользователь"
        username = f"@{user.username}" if user.username else f"id:{user_id}"
        try:
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=(
                    f"📩 Новый отзыв\n\n"
                    f"От: {name} ({username})\n\n"
                    f"{text.strip()}"
                ),
            )
        except Exception as e:
            logger.error(f"Не удалось отправить отзыв admin: {e}")
