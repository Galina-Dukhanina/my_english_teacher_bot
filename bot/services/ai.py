import logging
import httpx
import json
from openai import OpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL_DIALOG, PROXY_URL
from bot.services.cost_control import (
    is_daily_limit_reached,
    log_ai_usage,
    LIMIT_EXCEEDED_MESSAGE,
    should_alert_admin_on_limit,
)

logger = logging.getLogger(__name__)

if PROXY_URL:
    http_client = httpx.Client(proxy=PROXY_URL, trust_env=False)
else:
    http_client = httpx.Client(trust_env=False)

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    http_client=http_client,
)

FALLBACK_MESSAGE = (
    "Ой, что-то пошло не так с моей стороны. Попробуй написать еще раз через минуту."
)


def _request_completion(
    messages: list,
    model: str,
    max_tokens: int,
    user_id: int | None = None,
    temperature: float = 0.7,
) -> tuple[str | None, dict]:
    """Общий запрос к OpenRouter с проверкой лимита и учётом расходов.

    Возвращает (text, usage) или (None, {}) при ошибке/лимите.
    """
    if is_daily_limit_reached():
        logger.warning("Дневной лимит расходов на AI исчерпан")
        return None, {"limit_reached": True}

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = response.choices[0].message.content.strip()
        usage = {
            "tokens_in": response.usage.prompt_tokens,
            "tokens_out": response.usage.completion_tokens,
            "model": model,
        }
        log_ai_usage(user_id, usage)
        logger.info(
            f"AI ответил: {usage['tokens_in']} вход / "
            f"{usage['tokens_out']} выход токенов"
        )
        return text, usage
    except Exception as e:
        logger.error(f"Ошибка запроса к AI: {e}")
        return None, {}


def get_ai_response(
    system_prompt: str, history: list, user_id: int | None = None
) -> tuple[str, dict]:
    """Отправить запрос в OpenRouter и получить ответ."""
    messages = [{"role": "system", "content": system_prompt}] + history
    text, usage = _request_completion(
        messages, MODEL_DIALOG, max_tokens=500, user_id=user_id
    )
    if usage.get("limit_reached"):
        return LIMIT_EXCEEDED_MESSAGE, usage
    if text is None:
        return FALLBACK_MESSAGE, usage
    return text, usage


def generate_word_set(
    topic: str, level: str, count: int = 10, user_id: int | None = None
) -> list:
    """Сгенерировать набор слов по теме под уровень."""
    level_hint = {
        "beginner": "простые, базовые слова",
        "intermediate": "слова среднего уровня",
        "advanced": "продвинутые слова, включая идиомы",
        "unknown": "слова разного уровня",
    }.get(level, "слова разного уровня")

    system = (
        "Ты генератор учебных карточек для изучения английского. "
        "Отвечай ТОЛЬКО валидным JSON, без пояснений и markdown."
    )
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

    text, usage = _request_completion(
        messages, MODEL_DIALOG, max_tokens=2000, user_id=user_id
    )
    if not text:
        return []

    try:
        text = text.replace("```json", "").replace("```", "").strip()
        words = json.loads(text)
        logger.info(f"Сгенерировано слов: {len(words)} по теме '{topic}'")
        return words
    except json.JSONDecodeError as e:
        logger.error(f"AI вернул невалидный JSON для слов: {e}")
        return []


def explain_grammar_topic(
    topic: str,
    level: str,
    style: str,
    language: str,
    user_id: int | None = None,
) -> str:
    """Сгенерировать объяснение грамматической темы."""
    from bot.prompts import GRAMMAR_EXPLANATION_FORMAT

    del style

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

{GRAMMAR_EXPLANATION_FORMAT}"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    text, _ = _request_completion(
        messages, MODEL_DIALOG, max_tokens=1500, user_id=user_id
    )
    return text or ""


def generate_grammar_exercises(
    topic: str, level: str, count: int = 5, user_id: int | None = None
) -> list:
    """Сгенерировать упражнения по грамматической теме (multiple choice)."""
    level_hint = {
        "beginner": "простые предложения, базовая лексика",
        "intermediate": "предложения средней сложности",
        "advanced": "сложные предложения, продвинутая лексика",
        "unknown": "простые предложения",
    }.get(level, "простые предложения")

    system = (
        "Ты генератор упражнений по английской грамматике. "
        "Отвечай ТОЛЬКО валидным JSON, без пояснений и markdown."
    )

    user = f"""Создай {count} упражнений по теме «{topic}» ({level_hint}).
Каждое упражнение — предложение с пропуском (___), 3-4 варианта ответа, правильный вариант, и краткое пояснение почему.

Формат — массив JSON:
[
  {{"sentence": "She ___ a teacher.", "options": ["is", "are", "am"], "correct": "is", "explanation": "С she используется is."}},
  ...
]
Только JSON, ничего больше."""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    text, _ = _request_completion(
        messages, MODEL_DIALOG, max_tokens=2000, user_id=user_id
    )
    if not text:
        return []

    try:
        text = text.replace("```json", "").replace("```", "").strip()
        exercises = json.loads(text)
        logger.info(f"Сгенерировано упражнений: {len(exercises)} по теме '{topic}'")
        return exercises
    except Exception as e:
        logger.error(f"Ошибка генерации упражнений: {e}")
        return []


def check_limit_alert_pending() -> bool:
    """Нужно ли отправить admin алерт о превышении дневного лимита."""
    return should_alert_admin_on_limit()
