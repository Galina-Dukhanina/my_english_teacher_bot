import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")
MODEL_DIALOG = os.getenv("MODEL_DIALOG")
MODEL_ANALYSIS = os.getenv("MODEL_ANALYSIS")
DAILY_COST_LIMIT_USD = float(os.getenv("DAILY_COST_LIMIT_USD", "1.0"))
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

# Проверка: без токена бот не запустится
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден! Проверь файл .env")
