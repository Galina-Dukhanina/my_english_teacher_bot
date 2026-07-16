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
PROXY_URL = os.getenv("PROXY_URL")

# === Лимиты бесплатного тарифа ===
FREE_LIMIT_MESSAGES = int(os.getenv("FREE_LIMIT_MESSAGES", "15"))
FREE_LIMIT_WORDS_SESSIONS = int(os.getenv("FREE_LIMIT_WORDS_SESSIONS", "1"))
FREE_LIMIT_GRAMMAR_EXERCISES = int(os.getenv("FREE_LIMIT_GRAMMAR_EXERCISES", "1"))

# === Лимиты Premium (listening/voice — этапы 13–14) ===
PREMIUM_LIMIT_LISTENING = int(os.getenv("PREMIUM_LIMIT_LISTENING", "5"))
PREMIUM_LIMIT_VOICE = int(os.getenv("PREMIUM_LIMIT_VOICE", "2"))
PREMIUM_REVIEW_BATCH_SIZE = int(os.getenv("PREMIUM_REVIEW_BATCH_SIZE", "3"))

# === Платежи ===
PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "manual")  # manual | yookassa
PREMIUM_PRICE_MONTH = float(os.getenv("PREMIUM_PRICE_MONTH", "299"))
PREMIUM_PRICE_YEAR = float(os.getenv("PREMIUM_PRICE_YEAR", "2490"))
PREMIUM_DAYS_MONTH = int(os.getenv("PREMIUM_DAYS_MONTH", "30"))
PREMIUM_DAYS_YEAR = int(os.getenv("PREMIUM_DAYS_YEAR", "365"))
# false — показываем заглушку «Premium скоро», оплата недоступна
PREMIUM_SALES_ENABLED = os.getenv("PREMIUM_SALES_ENABLED", "false").lower() in (
    "1",
    "true",
    "yes",
)
PAYMENT_RETURN_URL = os.getenv("PAYMENT_RETURN_URL", "https://t.me")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))

# Проверка: без токена бот не запустится
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден! Проверь файл .env")
