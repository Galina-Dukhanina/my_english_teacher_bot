"""Запуск режима «Поговорить»."""


def start_talk(user_id: int, topic_name: str):
    """Установить активность и тему."""
    from database.db import set_topic, set_activity

    set_activity(user_id, "talk")
    set_topic(user_id, topic_name)


async def begin_talk_session(message, context, user_id: int, topic_name: str):
    """Запустить разговор — бот задает первый вопрос."""
    start_talk(user_id, topic_name)
    from bot.handlers.dialog import send_talk_opener

    await send_talk_opener(message, context, user_id, topic_name)
