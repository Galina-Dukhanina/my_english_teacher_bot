import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import (
    get_user,
    set_activity,
    set_pending_action,
    log_event,
    add_words_batch,
    get_words_to_review,
    review_word_result,
)
from bot import texts, keyboards
from bot.services.ai import generate_word_set
from bot.services.session_store import (
    KIND_CARDS,
    get_session,
    save_session,
    clear_session,
)
from bot.services.progress import record_activity, ACTIVITY_WORDS, ACTIVITY_REVIEW
from bot.services.limits import (
    check_and_consume,
    ACTION_WORDS_SESSION,
    get_limit_message,
)

logger = logging.getLogger(__name__)


def _load_session(user_id: int) -> dict | None:
    return get_session(user_id, KIND_CARDS)


def _store_session(user_id: int, session: dict):
    save_session(user_id, KIND_CARDS, session)


async def _reveal_self_check_card(context: ContextTypes.DEFAULT_TYPE):
    """Показать ответ карточки самопроверки через JobQueue (не блокирует бота)."""
    job = context.job
    data = job.data
    user_id = data["user_id"]
    session = _load_session(user_id)
    if not session or session.get("index") != data["index"]:
        return

    word = data["word"]
    transcription = data.get("transcription", "")
    translation = data.get("translation", "?")
    example = data.get("example", "")
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
    await context.bot.send_message(
        chat_id=data["chat_id"],
        text=answer_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


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
    _store_session(user_id, {"topic": topic_name})
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

    limit_result = check_and_consume(user_id, ACTION_WORDS_SESSION)
    if not limit_result.allowed:
        await query.edit_message_text(
            get_limit_message(limit_result) + "\n\n" + texts.PREMIUM_UPSELL,
            reply_markup=keyboards.premium_upsell_keyboard(),
        )
        return

    session = _load_session(user_id) or {}
    topic = session.get("topic", "общая лексика")
    session["format"] = fmt

    # Сообщение о генерации с темой и форматом
    fmt_name = texts.BTN_FORMAT.get(fmt, fmt)
    await query.edit_message_text(
        texts.WORDS_GENERATING.format(topic=topic, fmt=fmt_name)
    )

    user = get_user(user_id)
    words = generate_word_set(topic, user["level"] or "unknown", count=10, user_id=user_id)

    if not words:
        await query.message.reply_text(
            texts.WORDS_GEN_ERROR, reply_markup=keyboards.main_keyboard()
        )
        clear_session(user_id, KIND_CARDS)
        return

    # Слова НЕ сохраняем сразу — сохраним только те, что пользователь "не знал"
    log_event(user_id, "words_session")
    session["words"] = words
    session["index"] = 0
    session["knew"] = 0
    _store_session(user_id, session)

    try:
        await _show_card(query.message, context, user_id)
    except Exception as e:
        logger.error(f"Ошибка показа карточки: {e}")
        await query.message.reply_text(
            texts.WORDS_GEN_ERROR, reply_markup=keyboards.main_keyboard()
        )


async def _show_card(message, context, user_id):
    """Показать текущую карточку в выбранном формате."""
    session = _load_session(user_id)
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
        # EN → RU: английское слово, варианты — переводы
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
            f"Выбери перевод на русский:\n\n{word.upper()}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif fmt == "options_reverse":
        # RU → EN: русское слово, варианты — английские слова
        prompt = card.get("translation", "?")
        correct = card.get("word", "?")
        others = [
            w.get("word")
            for i, w in enumerate(words)
            if i != index and w.get("word") and w.get("word") != correct
        ]
        random.shuffle(others)
        distractors = others[:3]
        options = distractors + [correct]
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
            f"Выбери перевод на английский:\n\n{prompt.capitalize()}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await message.reply_text(f"Вспомни перевод:\n\n{word.upper()}")
        context.job_queue.run_once(
            _reveal_self_check_card,
            when=5,
            data={
                "user_id": user_id,
                "chat_id": message.chat_id,
                "index": index,
                "word": word,
                "translation": card.get("translation", "?"),
                "transcription": card.get("transcription", ""),
                "example": card.get("example", ""),
            },
            name=f"card_reveal_{user_id}_{index}",
        )


async def handle_card_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа: 'варианты' (wans) или 'самопроверка' (wself)."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action, value = query.data.split(":", 1)

    session = _load_session(user_id)
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
    mode = session.get("mode", "learn")

    if mode == "review":
        # Режим повторения: обновляем статус слова в словаре
        word_id = card.get("id")
        if word_id:
            review_word_result(word_id, knew)
        if knew:
            session["knew"] += 1
            # Проверим, освоено ли слово теперь (3 верных подряд)
            if card.get("times_reviewed", 0) + 1 >= 3:
                session["mastered_now"] = session.get("mastered_now", 0) + 1
    else:
        # Режим изучения: не знал — сохраняем слово в словарь
        if not knew:
            add_words_batch(user_id, [card], session.get("topic", ""))
            session["to_review"] = session.get("to_review", 0) + 1
        else:
            session["knew"] += 1

    # Для формата "варианты" показываем результат
    if action == "wans":
        transcription = card.get("transcription", "")
        fmt = session.get("format", "options")
        if fmt == "options_reverse":
            pair = f"{card.get('translation')} — {card.get('word')}"
        else:
            pair = f"{card.get('word')} — {card.get('translation', '?')}"
        if knew:
            feedback = f"✅ Верно!\n\n{pair}\nЧитать как:\n{transcription}"
        else:
            feedback = f"❌ Правильный ответ:\n\n{pair}\nЧитать как:\n{transcription}"
        try:
            await query.edit_message_text(feedback)
        except Exception:
            pass

    # Переход к следующей карточке
    session["index"] += 1
    _store_session(user_id, session)
    try:
        await _show_card(query.message, context, user_id)
    except Exception as e:
        logger.error(f"Ошибка показа следующей карточки: {e}")


async def _finish_session(message, user_id):
    """Завершить сессию, показать итог."""
    session = _load_session(user_id) or {}
    total = len(session.get("words", []))
    knew = session.get("knew", 0)
    mode = session.get("mode", "learn")

    clear_session(user_id, KIND_CARDS)
    set_activity(user_id, None)

    if mode == "review":
        record_activity(user_id, ACTIVITY_REVIEW)
    else:
        record_activity(user_id, ACTIVITY_WORDS)

    if mode == "review":
        mastered = session.get("mastered_now", 0)
        text = texts.REVIEW_DONE.format(total=total, knew=knew, mastered=mastered)
    else:
        to_review = session.get("to_review", 0)
        text = texts.WORDS_SESSION_DONE.format(
            total=total, knew=knew, to_review=to_review
        )

    await message.reply_text(text, reply_markup=keyboards.main_keyboard())


async def start_words_with_topic(update, context, user_id, topic_name):
    """Запуск карточек со своей темой — сразу к выбору формата."""
    _store_session(user_id, {"topic": topic_name})
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


async def start_review(source, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Запуск повторения слов из словаря (неосвоенные)."""
    message = source.message if hasattr(source, "message") else source

    words = get_words_to_review(user_id, limit=10)
    if not words:
        await message.reply_text(
            texts.REVIEW_NO_WORDS, reply_markup=keyboards.main_keyboard()
        )
        return

    set_activity(user_id, "review")
    log_event(user_id, "review_session")

    # Готовим сессию. Формат повторения — всегда "варианты" (быстрее и проще).
    # Слова уже содержат word, translation, transcription. options может не быть —
    # сгенерируем простые заглушки или используем самопроверку.
    session = {
        "mode": "review",
        "words": words,
        "index": 0,
        "knew": 0,
        "mastered_now": 0,
        "format": "timer",  # для повторения используем самопроверку
    }
    _store_session(user_id, session)

    await message.reply_text(texts.REVIEW_START.format(count=len(words)))
    await _show_card(message, context, user_id)
