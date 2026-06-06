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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, PROXY_URL
from database.db import init_db
from bot.handlers import onboarding

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    init_db()
    logger.info("База данных готова")

    # Создаём приложение, при необходимости через прокси
    builder = Application.builder().token(BOT_TOKEN)
    if PROXY_URL:
        builder = builder.proxy(PROXY_URL).get_updates_proxy(PROXY_URL)
        logger.info(f"Используется прокси: {PROXY_URL}")
    app = builder.build()

    # Онбординг
    app.add_handler(CommandHandler("start", onboarding.start))
    app.add_handler(
        CallbackQueryHandler(
            onboarding.handle_onboarding_button,
            pattern=r"^(terms|level|goal|style|timezone|time):",
        )
    )

    logger.info("Бот запускается...")
    app.run_polling()


if __name__ == "__main__":
    main()
