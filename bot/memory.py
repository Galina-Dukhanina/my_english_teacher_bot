# Хранение истории диалогов В ПАМЯТИ.
# Весь остальной код работает только через функции ниже,
# поэтому потом можно переписать хранилище на БД, не трогая логику.

# Структура: {user_id: [ {"role": "user"/"assistant", "content": "..."}, ... ]}
_conversations = {}

# Сколько последних сообщений храним на пользователя.
# Ограничение нужно, чтобы не раздувать запрос к AI (и расходы).
MAX_HISTORY = 20


def get_history(user_id: int) -> list:
    """Вернуть историю диалога пользователя (список сообщений)."""
    return _conversations.get(user_id, [])


def add_message(user_id: int, role: str, content: str):
    """Добавить сообщение в историю. role — 'user' или 'assistant'."""
    if user_id not in _conversations:
        _conversations[user_id] = []
    _conversations[user_id].append({"role": role, "content": content})

    # Обрезаем старые сообщения, оставляя последние MAX_HISTORY
    if len(_conversations[user_id]) > MAX_HISTORY:
        _conversations[user_id] = _conversations[user_id][-MAX_HISTORY:]


def clear_history(user_id: int):
    """Очистить историю диалога (пригодится при смене активности)."""
    _conversations[user_id] = []
