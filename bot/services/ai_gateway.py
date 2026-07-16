"""Единая точка JSON-запросов к DeepSeek (Premium writing и др.)."""

from __future__ import annotations

import json
import logging

from config import MODEL_ANALYSIS
from bot.domain.writing import WritingCheckResult
from bot.services.ai import _request_completion
from bot.services.cost_control import LIMIT_EXCEEDED_MESSAGE

logger = logging.getLogger(__name__)

WRITING_CHECK_SCHEMA = {
    "passed": "bool — задание выполнено по смыслу",
    "score": "float 0..1 — качество ответа",
    "corrected_text": "string — исправленный вариант на английском",
    "feedback_ru": "string — короткий комментарий на русском (2–3 предложения)",
    "errors": "array of strings — главные ошибки, может быть пустым",
}


def parse_json_response(text: str) -> dict | None:
    if not text:
        return None
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            logger.error("AI gateway: invalid JSON")
            return None
        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            logger.error("AI gateway: JSON parse failed: %s", exc)
            return None
    return data if isinstance(data, dict) else None


def request_json(
    *,
    system: str,
    user: str,
    user_id: int | None = None,
    model: str | None = None,
    max_tokens: int = 500,
) -> tuple[dict | None, dict]:
    """Запрос с ожиданием одного JSON-объекта в ответе."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    text, usage = _request_completion(
        messages,
        model or MODEL_ANALYSIS,
        max_tokens=max_tokens,
        user_id=user_id,
        temperature=0.2,
    )
    if usage.get("limit_reached"):
        return None, {"limit_reached": True}
    payload = parse_json_response(text or "")
    return payload, usage


def check_writing(
    user_id: int,
    *,
    prompt_ru: str,
    user_text: str,
    cefr_level: str = "A1",
    phrase_en: str = "",
    explain_ru: str = "",
) -> tuple[WritingCheckResult | None, str | None]:
    """Проверить ответ ученика на шаге apply.

    Возвращает (result, error_message). error_message — для показа пользователю.
    """
    system = (
        "Ты преподаватель английского. Оцениваешь короткий письменный ответ ученика. "
        "Отвечай ТОЛЬКО валидным JSON-объектом, без markdown и пояснений."
    )
    context_parts = [
        f"Уровень CEFR: {cefr_level}",
        f"Задание (RU): {prompt_ru}",
    ]
    if phrase_en:
        context_parts.append(f"Опорная фраза урока: {phrase_en}")
    if explain_ru:
        context_parts.append(f"Правило из урока: {explain_ru}")

    schema_lines = "\n".join(f'- "{k}": {v}' for k, v in WRITING_CHECK_SCHEMA.items())
    user = f"""{chr(10).join(context_parts)}

Ответ ученика:
{user_text}

Оцени ответ: выполнено ли задание по смыслу, насколько грамотно написано для уровня {cefr_level}.
Будь поддерживающим: мелкие огрехи у A1/A2 не должны автоматически давать passed=false.
passed=true если смысл верный и текст в целом понятен.

Формат ответа — JSON:
{{
  "passed": true,
  "score": 0.85,
  "corrected_text": "...",
  "feedback_ru": "...",
  "errors": ["..."]
}}

Поля:
{schema_lines}
"""

    payload, usage = request_json(
        system=system,
        user=user,
        user_id=user_id,
        max_tokens=450,
    )
    if usage.get("limit_reached"):
        return None, LIMIT_EXCEEDED_MESSAGE
    if not payload:
        return None, None

    try:
        return WritingCheckResult.from_payload(payload), None
    except (TypeError, ValueError) as exc:
        logger.error("Writing check payload invalid: %s", exc)
        return None, None
