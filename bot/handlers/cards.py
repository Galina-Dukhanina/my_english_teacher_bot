import logging
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import (
    get_user,
    set_activity,
    set_pending_action,
    log_event,
    add_words_batch,
    get_vocab_stats,
)
from bot import texts, keyboards
from bot.services.ai import generate_word_set

logger = logging.getLogger(__name__)

# Сессии карточек в памяти: {user_id: {"words":[...], "index":0, "format":"...", "knew":0, "topic":"..."}}
_card_sessions = {}


async def start_words(source, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Старт режима 'Учить слова' — показываем выбор темы.
    source может быть update (с .message) или query (с .message)."""
    set_activity(user_id, "words")
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"wtopic:{code}")]
        for code, label in texts.TALK_TOPICS.items()
    ]
    message = source.message if hasattr(source, "message") else source
    await message.reply_text(
        texts.WORDS_CHOOSE_TOPIC,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_words_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор темы для карточек."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    _, topic = query.data.split(":", 1)

    if topic == "free":
        set_pending_action(user_id, "wait_words_topic")
        await query.edit_message_text(texts.WORDS_ASK_TOPIC)
        return

    topic_name = texts.TALK_TOPICS[topic]
    _card_sessions[user_id] = {"topic": topic_name}
    await _ask_format(query, user_id)


async def _ask_format(query, user_id):
    """Показать выбор формата тренировки."""
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"wformat:{code}")]
        for code, label in texts.BTN_FORMAT.items()
    ]
    await query.edit_message_text(
        texts.WORDS_CHOOSE_FORMAT,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_words_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбран формат — генерируем слова и начинаем сессию."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    _, fmt = query.data.split(":", 1)

    session = _card_sessions.get(user_id, {})
    topic = session.get("topic", "общая лексика")
    session["format"] = fmt

    # Сообщение о генерации с темой и форматом
    fmt_name = texts.BTN_FORMAT.get(fmt, fmt)
    await query.edit_message_text(
        texts.WORDS_GENERATING.format(topic=topic, fmt=fmt_name)
    )

    user = get_user(user_id)
    words = generate_word_set(topic, user["level"] or "unknown", count=10)

    if not words:
        await query.message.reply_text(
            texts.WORDS_GEN_ERROR, reply_markup=keyboards.main_keyboard()
        )
        _card_sessions.pop(user_id, None)
        return

    # Слова НЕ сохраняем сразу — сохраним только те, что пользователь "не знал"
    log_event(user_id, "words_session")
    session["words"] = words
    session["index"] = 0
    session["knew"] = 0
    _card_sessions[user_id] = session

    try:
        await _show_card(query.message, context, user_id)
    except Exception as e:
        logger.error(f"Ошибка показа карточки: {e}")
        await query.message.reply_text(
            texts.WORDS_GEN_ERROR, reply_markup=keyboards.main_keyboard()
        )


async def _show_card(message, context, user_id):
    """Показать текущую карточку в выбранном формате."""
    session = _card_sessions.get(user_id)
    if not session:
        return

    index = session["index"]
    words = session["words"]

    if index >= len(words):
        await _finish_session(message, user_id)
        return

    card = words[index]
    word = card.get("word", "?")
    fmt = session["format"]

    if fmt == "options":
        # Формат "варианты ответа": слово + кнопки с переводами
        correct = card.get("translation", "?")
        options = card.get("options", [])[:3] + [correct]
        random.shuffle(options)
        keyboard = [
            [
                InlineKeyboardButton(
                    opt, callback_data=f"wans:{'1' if opt == correct else '0'}"
                )
            ]
            for opt in options
        ]
        keyboard.append(
            [InlineKeyboardButton(texts.CARD_STOP, callback_data="wstop:1")]
        )
        await message.reply_text(
            f"Выбери правильный перевод слова:\n\n{word.upper()}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        # Формат "самопроверка": слово, через 5 сек ответ + кнопки знал/не знал
        await message.reply_text(f"Вспомни перевод:\n\n{word.upper()}")
        await asyncio.sleep(5)
        transcription = card.get("transcription", "")
        translation = card.get("translation", "?")
        example = card.get("example", "")
        answer_text = f"{word} — {translation}\nЧитать как:\n{transcription}"
        if example:
            answer_text += f"\n\nПример: {example}"
        keyboard = [
            [
                InlineKeyboardButton(texts.CARD_KNEW, callback_data="wself:1"),
                InlineKeyboardButton(texts.CARD_DIDNT, callback_data="wself:0"),
            ],
            [InlineKeyboardButton(texts.CARD_STOP, callback_data="wstop:1")],
        ]
        await message.reply_text(
            answer_text, reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_card_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа: 'варианты' (wans) или 'самопроверка' (wself)."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action, value = query.data.split(":", 1)

    session = _card_sessions.get(user_id)
    if not session:
        await query.message.reply_text(
            "Сессия прервалась. Начни заново через «Учить слова».",
            reply_markup=keyboards.main_keyboard(),
        )
        return

    index = session["index"]
    words = session["words"]
    if index >= len(words):
        return
    card = words[index]
    knew = value == "1"

    # Если НЕ знал — сохраняем слово в словарь для повторения
    if not knew:
        add_words_batch(user_id, [card], session.get("topic", ""))
        session["to_review"] = session.get("to_review", 0) + 1
    else:
        session["knew"] += 1

    # Для формата "варианты" показываем результат
    if action == "wans":
        correct = card.get("translation", "?")
        transcription = card.get("transcription", "")
        if knew:
            feedback = f"✅ Верно!\n\n{card.get('word')} — {correct}\nЧитать как:\n{transcription}"
        else:
            feedback = f"❌ Правильный ответ:\n\n{card.get('word')} — {correct}\nЧитать как:\n{transcription}"
        try:
            await query.edit_message_text(feedback)
        except Exception:
            pass

    # Переход к следующей карточке
    session["index"] += 1
    _card_sessions[user_id] = session
    try:
        await _show_card(query.message, context, user_id)
    except Exception as e:
        logger.error(f"Ошибка показа следующей карточки: {e}")


async def _finish_session(message, user_id):
    """Завершить сессию, показать итог."""
    session = _card_sessions.get(user_id, {})
    total = len(session.get("words", []))
    knew = session.get("knew", 0)
    to_review = session.get("to_review", 0)

    _card_sessions.pop(user_id, None)
    set_activity(user_id, None)

    await message.reply_text(
        texts.WORDS_SESSION_DONE.format(total=total, knew=knew, to_review=to_review),
        reply_markup=keyboards.main_keyboard(),
    )


async def start_words_with_topic(update, context, user_id, topic_name):
    """Запуск карточек со своей темой — сразу к выбору формата."""
    _card_sessions[user_id] = {"topic": topic_name}
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"wformat:{code}")]
        for code, label in texts.BTN_FORMAT.items()
    ]
    await update.message.reply_text(
        texts.WORDS_CHOOSE_FORMAT,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_card_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Досрочное завершение сессии карточек."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    try:
        await query.edit_message_text("Задание завершено.")
    except Exception:
        pass
    await _finish_session(query.message, user_id)
