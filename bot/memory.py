# Слой доступа к истории диалогов (хранение в SQLite).
# Handlers работают только через функции ниже.

from database.db import (
    get_conversation_history,
    add_conversation_message,
    trim_conversation_history,
    clear_conversation_history,
)

MAX_HISTORY = 20


def get_history(user_id: int) -> list:
    """Вернуть историю диалога пользователя (список сообщений)."""
    return get_conversation_history(user_id, MAX_HISTORY)


def add_message(user_id: int, role: str, content: str):
    """Добавить сообщение в историю. role — 'user' или 'assistant'."""
    add_conversation_message(user_id, role, content)
    trim_conversation_history(user_id, MAX_HISTORY)


def clear_history(user_id: int):
    """Очистить историю диалога."""
    clear_conversation_history(user_id)
