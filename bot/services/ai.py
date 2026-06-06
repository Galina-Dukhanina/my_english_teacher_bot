import logging
import httpx
from openai import OpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL_DIALOG, PROXY_URL

logger = logging.getLogger(__name__)

# Создаем httpx-клиент с нашим прокси (если он задан).
# Это нужно, потому что OpenRouter доступен только через VPN,
# и нельзя позволить библиотеке схватить системный socks4.
if PROXY_URL:
    http_client = httpx.Client(proxy=PROXY_URL, trust_env=False)
else:
    http_client = httpx.Client(trust_env=False)

# Клиент OpenRouter (формат совместим с OpenAI)
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    http_client=http_client,
)

# Сообщение-заглушка на случай, если AI недоступен
FALLBACK_MESSAGE = (
    "Ой, что-то пошло не так с моей стороны. Попробуй написать еще раз через минуту."
)


def get_ai_response(system_prompt: str, history: list) -> tuple[str, dict]:
    """Отправить запрос в OpenRouter и получить ответ.

    system_prompt — собранный промпт под пользователя (стиль + уровень).
    history — список сообщений диалога [{"role": "user"/"assistant", "content": "..."}].

    Возвращает кортеж (текст_ответа, информация_о_расходах).
    Если произошла ошибка — возвращает FALLBACK_MESSAGE и пустые расходы.
    """
    # Собираем сообщения: системный промпт + история диалога
    messages = [{"role": "system", "content": system_prompt}] + history

    try:
        response = client.chat.completions.create(
            model=MODEL_DIALOG,
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )

        text = response.choices[0].message.content.strip()

        # Собираем информацию о расходах (для будущего cost_control)
        usage = {
            "tokens_in": response.usage.prompt_tokens,
            "tokens_out": response.usage.completion_tokens,
            "model": MODEL_DIALOG,
        }

        logger.info(
            f"AI ответил: {usage['tokens_in']} вход / "
            f"{usage['tokens_out']} выход токенов"
        )
        return text, usage

    except Exception as e:
        # Любая ошибка (нет сети, упал OpenRouter, кончились деньги) —
        # не роняем бота, отдаем мягкую заглушку
        logger.error(f"Ошибка запроса к AI: {e}")
        return FALLBACK_MESSAGE, {}
