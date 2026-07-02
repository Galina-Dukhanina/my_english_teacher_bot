import logging
import httpx
import json
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


def generate_word_set(topic: str, level: str, count: int = 10) -> list:
    """Сгенерировать набор слов по теме под уровень.
    Возвращает список словарей с word, translation, transcription, example, options.
    options — 3 неправильных перевода для режима 'варианты ответа'."""

    level_hint = {
        "beginner": "простые, базовые слова",
        "intermediate": "слова среднего уровня",
        "advanced": "продвинутые слова, включая идиомы",
        "unknown": "слова разного уровня",
    }.get(level, "слова разного уровня")

    system = "Ты генератор учебных карточек для изучения английского. Отвечай ТОЛЬКО валидным JSON, без пояснений и markdown."

    user = f"""Сгенерируй {count} английских слов по теме «{topic}» ({level_hint}).
Для каждого слова дай: само слово, перевод на русский, транскрипцию (IPA и русскими буквами в скобках), короткий пример предложения, и 3 НЕПРАВИЛЬНЫХ перевода (похожие, но другие слова) для теста.

Формат ответа — массив JSON:
[
  {{"word": "travel", "translation": "путешествовать", "transcription": "[ˈtrævl] (трэвл)", "example": "I love to travel.", "options": ["работать", "отдыхать", "лететь"]}},
  ...
]
Только JSON, ничего больше."""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_DIALOG,
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
        )
        text = response.choices[0].message.content.strip()

        # Убираем возможные markdown-обертки ```json ... ```
        text = text.replace("```json", "").replace("```", "").strip()

        words = json.loads(text)
        logger.info(f"Сгенерировано слов: {len(words)} по теме '{topic}'")
        return words

    except json.JSONDecodeError as e:
        logger.error(f"AI вернул невалидный JSON для слов: {e}")
        return []
    except Exception as e:
        logger.error(f"Ошибка генерации слов: {e}")
        return []


def explain_grammar_topic(topic: str, level: str, style: str, language: str) -> str:
    """Сгенерировать объяснение грамматической темы под уровень/стиль/язык."""

    lang_hint = {
        "ru": "Объясняй на русском языке.",
        "en": "Explain in simple English.",
        "both": "Объясняй на русском, ключевые моменты дублируй на английском.",
        "auto": "Объясняй на русском для начинающих, больше английского для продвинутых.",
    }.get(language, "Объясняй на русском языке.")

    level_hint = {
        "beginner": "Ученик начинающий — объясняй очень просто, минимум терминов, больше примеров.",
        "intermediate": "Ученик среднего уровня — можно термины с пояснениями.",
        "advanced": "Ученик продвинутый — можно глубже, с нюансами.",
        "unknown": "Уровень неизвестен — объясняй просто.",
    }.get(level, "Объясняй просто.")

    system = (
        "Ты преподаватель английского. Объясняешь грамматику понятно и структурно. "
        "Пиши ТОЛЬКО обычным текстом, без markdown, без звездочек и решеток. "
        f"{lang_hint} {level_hint}"
    )

    user = f"""Объясни тему английской грамматики: «{topic}».

Структура объяснения:
1. Что это и зачем нужно (кратко)
2. Как образуется (правило)
3. Примеры (3-4 штуки с переводом)
4. Типичные ошибки или важные моменты

Будь понятным и не слишком длинным. Это чат, не учебник."""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_DIALOG,
            messages=messages,
            max_tokens=1500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Ошибка объяснения грамматики: {e}")
        return ""
