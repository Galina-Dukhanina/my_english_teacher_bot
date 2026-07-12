import logging
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_USER_ID

logger = logging.getLogger(__name__)

USER_ERROR_MESSAGE = (
    "Что-то пошло не так с моей стороны. "
    "Попробуй ещё раз или нажми /start, если проблема повторяется."
)


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Перехват необработанных исключений — пользователю fallback, admin алерт."""
    logger.error(
        "Необработанное исключение при обработке update",
        exc_info=context.error,
    )

    if isinstance(update, Update):
        try:
            if update.effective_message:
                await update.effective_message.reply_text(USER_ERROR_MESSAGE)
            elif update.callback_query:
                await update.callback_query.answer(
                    "Ошибка, попробуй ещё раз",
                    show_alert=True,
                )
        except Exception as notify_err:
            logger.error(f"Не удалось отправить сообщение об ошибке: {notify_err}")

    if ADMIN_USER_ID:
        tb = "".join(
            traceback.format_exception(
                type(context.error),
                context.error,
                context.error.__traceback__,
            )
        )
        text = f"⚠️ Ошибка бота:\n\n{tb[-3500:]}"
        try:
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text=text)
        except Exception as admin_err:
            logger.error(f"Не удалось отправить алерт admin: {admin_err}")
