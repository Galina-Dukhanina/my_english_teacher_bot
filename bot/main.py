import os
import logging

# ВАЖНО: убираем системные прокси-переменные (Happ выставляет socks4,
# который ломает подключение). Делаем это ДО импорта telegram/httpx.
for var in [
    "ALL_PROXY",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "all_proxy",
    "http_proxy",
    "https_proxy",
]:
    os.environ.pop(var, None)

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from config import BOT_TOKEN, PROXY_URL
from database.db import init_db
from bot.handlers import onboarding, commands, dialog, activities, cards, grammar, feedback
from bot.middleware.error_handler import global_error_handler
from bot.scheduler import start_scheduler, stop_scheduler
from bot.services.reminders import handle_reminder_off

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    init_db()
    from database.db import migrate_db

    migrate_db()
    logger.info("База данных готова")

    # Создаём приложение, при необходимости через прокси
    builder = Application.builder().token(BOT_TOKEN)
    if PROXY_URL:
        builder = builder.proxy(PROXY_URL).get_updates_proxy(PROXY_URL)
        logger.info(f"Используется прокси: {PROXY_URL}")
    app = builder.build()
    app.add_error_handler(global_error_handler)

    # Онбординг
    app.add_handler(CommandHandler("start", onboarding.start))
    app.add_handler(
        CallbackQueryHandler(
            onboarding.handle_onboarding_button,
            pattern=r"^(terms|level|goal|style|timezone|time):",
        )
    )

    # Команды
    app.add_handler(CommandHandler("help", commands.help_command))
    app.add_handler(CommandHandler("style", commands.style_command))
    app.add_handler(CommandHandler("reminders", commands.reminders_command))
    app.add_handler(CommandHandler("feedback", feedback.feedback_command))
    app.add_handler(CommandHandler("progress", commands.progress_command))
    app.add_handler(CommandHandler("stats", commands.stats_command))

    # Кнопки команд (вне онбординга)
    app.add_handler(
        CallbackQueryHandler(commands.handle_style_button, pattern=r"^setstyle:")
    )
    app.add_handler(
        CallbackQueryHandler(
            commands.handle_reminders_button, pattern=r"^(rem|remtime):"
        )
    )
    app.add_handler(
        CallbackQueryHandler(handle_reminder_off, pattern=r"^reminder:off$")
    )
    # Меню активностей (выбор режима и темы)

    app.add_handler(
        CallbackQueryHandler(activities.handle_activity_button, pattern=r"^activity:")
    )

    app.add_handler(
        CallbackQueryHandler(activities.handle_topic_button, pattern=r"^topic:")
    )

    # Карточки слов
    app.add_handler(CallbackQueryHandler(cards.handle_words_topic, pattern=r"^wtopic:"))
    app.add_handler(
        CallbackQueryHandler(cards.handle_words_format, pattern=r"^wformat:")
    )
    app.add_handler(
        CallbackQueryHandler(cards.handle_card_answer, pattern=r"^(wans|wself):")
    )
    app.add_handler(CallbackQueryHandler(cards.handle_card_stop, pattern=r"^wstop:"))

    # Грамматика
    app.add_handler(
        CallbackQueryHandler(grammar.handle_grammar_topic, pattern=r"^gtopic:")
    )
    app.add_handler(CallbackQueryHandler(grammar.handle_grammar_nav, pattern=r"^gnav:"))
    app.add_handler(
        CallbackQueryHandler(grammar.handle_exercise_answer, pattern=r"^gex:")
    )
    app.add_handler(
        CallbackQueryHandler(grammar.handle_grammar_reexplain, pattern=r"^greexplain:")
    )
    app.add_handler(
        CallbackQueryHandler(grammar.handle_exercise_stop, pattern=r"^gexstop:")
    )

    # Кнопка выбора языка объяснений (inline-кнопки)
    app.add_handler(
        CallbackQueryHandler(dialog.handle_language_button, pattern=r"^setlang:")
    )

    # Основной диалог
    # Должен идти ПОСЛЕДНИМ, чтобы не перехватывать команды.
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            dialog.handle_message,
        )
    )

    logger.info("Бот запускается...")
    start_scheduler(app)
    try:
        app.run_polling()
    finally:
        stop_scheduler()


if __name__ == "__main__":
    main()
