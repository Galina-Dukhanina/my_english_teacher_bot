import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN

# Включаем логи, чтобы видеть, что происходит
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋 Я твой помощник в английском. Скоро тут будет много полезного!"
    )
    logger.info(f"Пользователь {update.effective_user.id} запустил бота")


def main():
    # Создаём приложение бота
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчик /start
    app.add_handler(CommandHandler("start", start))

    # Запускаем бота (polling — бот сам опрашивает Telegram)
    logger.info("Бот запускается...")
    app.run_polling()


if __name__ == "__main__":
    main()
