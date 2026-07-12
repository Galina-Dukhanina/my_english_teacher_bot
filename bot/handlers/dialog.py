import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from database.db import (
    get_user,
    log_event,
    set_pending_action,
    get_pending_action,
    update_user,
    should_show_menu,
    mark_menu_shown,
)

from bot import memory, prompts, texts, keyboards
from bot.handlers import activities
from config import ADMIN_USER_ID
from bot.services.ai import get_ai_response, check_limit_alert_pending
from bot.services.cost_control import LIMIT_EXCEEDED_MESSAGE
from bot.services.progress import record_activity, ACTIVITY_DIALOG
from bot.services.limits import check_and_consume, ACTION_MESSAGES, get_limit_message
from bot.services.subscription import is_premium, save_word_from_meaning

logger = logging.getLogger(__name__)


def _strip_markdown(text: str) -> str:
    """Убрать markdown-разметку, которую модель иногда вставляет."""
    text = re.sub(r"#{1,6}\s*", "", text)  # заголовки ###
    text = text.replace("**", "").replace("__", "")  # жирный
    text = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"\1", text)  # *курсив*
    text = text.replace("`", "")  # код
    return text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик текста: кнопки, режим ожидания или обычный диалог."""
    user_id = update.effective_user.id
    text = update.message.text

    # --- Краевой случай: пустое сообщение ---
    if not text or not text.strip():
        await update.message.reply_text("Напиши мне что-нибудь текстом, и я отвечу.")
        return

    # --- Краевой случай: не прошел онбординг ---
    user = get_user(user_id)
    if not user or not user["onboarding_done"]:
        await update.message.reply_text(
            "Давай сначала настроим все под тебя. Нажми /start"
        )
        return

    # --- Нажата кнопка? (одно определение на оба случая) ---
    is_button = text in (
        texts.BTN_MENU,
        texts.BTN_PRONOUNCE,
        texts.BTN_MEANING,
        texts.BTN_LANG,
    )

    # --- Авто-показ меню при первом сообщении за день ---
    # Не показываем, если: это кнопка, бот чего-то ждет, ИЛИ пользователь уже в режиме.
    if (
        not is_button
        and not get_pending_action(user_id)
        and not user["current_activity"]
        and should_show_menu(user_id)
    ):
        mark_menu_shown(user_id)
        await activities.show_activity_menu(update, context)
        return

    # --- Нажата кнопка? Сбрасываем зависшее ожидание ---
    if is_button:
        set_pending_action(user_id, None)  # выход из любого ожидания

    # --- Нажата кнопка-инструмент? ---
    if text == texts.BTN_MENU:
        await activities.show_activity_menu(update, context)
        return
    if text == texts.BTN_PRONOUNCE:
        await start_pronounce(update, context, user_id)
        return
    if text == texts.BTN_MEANING:
        await start_meaning(update, context, user_id)
        return
    if text == texts.BTN_LANG:
        await start_language(update, context, user_id)
        return

    # --- Бот ждет слово (после нажатия кнопки)? ---
    pending = get_pending_action(user_id)
    if pending == "wait_pronounce":
        set_pending_action(user_id, None)  # сбрасываем ожидание
        await _send_ai_reply(
            update,
            context,
            user_id,
            user,
            special=f"Покажи, как читается слово или фраза '{text}'. "
            f"Дай транскрипцию в формате IPA и русскими буквами. Кратко.",
        )
        return
    if pending == "wait_meaning":
        set_pending_action(user_id, None)
        word = text.strip()
        answer = await _send_ai_reply(
            update,
            context,
            user_id,
            user,
            special=f"Объясни простыми словами, что значит '{word}', "
            f"и приведи пример употребления. Кратко.",
        )
        if answer and answer != LIMIT_EXCEEDED_MESSAGE:
            if is_premium(user_id):
                save_word_from_meaning(user_id, word, answer)
                await update.message.reply_text(texts.PREMIUM_WORD_SAVED)
            else:
                await update.message.reply_text(texts.PREMIUM_WORD_HINT)
        return

    if pending == "wait_topic":
        set_pending_action(user_id, None)
        from database.db import set_activity, set_topic

        set_activity(user_id, "talk")
        set_topic(user_id, text)
        await update.message.reply_text(
            f"Отлично, говорим про «{text}». Начинай — напиши что-нибудь по-английски.",
            reply_markup=keyboards.main_keyboard(),
        )
        return

    if pending == "wait_words_topic":
        set_pending_action(user_id, None)
        from bot.handlers.cards import start_words_with_topic

        await start_words_with_topic(update, context, user_id, text)
        return

    if pending == "wait_feedback":
        from bot.handlers.feedback import submit_feedback

        await submit_feedback(update, context, user_id, text)
        return

    if pending == "wait_add_word":
        from bot.handlers.vocab import handle_add_word_input

        await handle_add_word_input(update, context, user_id, text)
        return

    # --- Активный режим (кроме talk): подсказка, не уводим в свободный диалог ---
    activity = user.get("current_activity")
    if activity and activity != "talk" and activity in texts.ACTIVITY_NAMES:
        await update.message.reply_text(
            texts.ACTIVITY_BUSY.format(
                activity=texts.ACTIVITY_NAMES[activity],
                menu=texts.BTN_MENU,
            ),
            reply_markup=keyboards.main_keyboard(),
        )
        return

    # --- Обычный диалог ---
    await _send_ai_reply(update, context, user_id, user, user_text=text)


async def _send_ai_reply(update, context, user_id, user, user_text=None, special=None):
    """Общая функция: собрать промпт, позвать AI, отправить ответ.
    user_text — обычное сообщение пользователя (идет в историю).
    special — служебная инструкция для инструментов (НЕ идет в общую историю).
    Возвращает текст ответа (без markdown) или None."""
    limit_result = check_and_consume(user_id, ACTION_MESSAGES)
    if not limit_result.allowed:
        await update.message.reply_text(
            get_limit_message(limit_result) + "\n\n" + texts.PREMIUM_UPSELL,
            reply_markup=keyboards.premium_upsell_keyboard(),
        )
        return None
    # Собираем системный промпт с учетом языка объяснений
    system_prompt = prompts.build_system_prompt(
        style=user["style"],
        level=user["level"] or "unknown",
        explanation_language=user["explanation_language"],
        topic=user["current_topic"],
    )

    if special:
        # Для инструментов: разовый запрос, не засоряем историю диалога
        history = memory.get_history(user_id) + [{"role": "user", "content": special}]
    else:
        # Обычный диалог: сохраняем в память
        memory.add_message(user_id, "user", user_text)
        history = memory.get_history(user_id)

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    answer, usage = get_ai_response(system_prompt, history, user_id=user_id)

    if usage.get("limit_reached") and check_limit_alert_pending() and ADMIN_USER_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text="⚠️ Достигнут дневной лимит расходов на AI (DAILY_COST_LIMIT_USD).",
            )
        except Exception as e:
            logger.error(f"Не удалось отправить алерт о лимите admin: {e}")

    if not special and answer != LIMIT_EXCEEDED_MESSAGE:
        memory.add_message(user_id, "assistant", answer)
    log_event(user_id, "dialog")
    if not special and answer != LIMIT_EXCEEDED_MESSAGE:
        record_activity(user_id, ACTIVITY_DIALOG)

    # Чистим разметку и отправляем обычным текстом — надежно, без сбоев парсинга.
    clean_answer = _strip_markdown(answer)
    await update.message.reply_text(
        clean_answer,
        reply_markup=keyboards.main_keyboard(),
    )
    return clean_answer


# ---------- Инструменты (вызываются кнопками) ----------


async def start_pronounce(update, context, user_id):
    """Кнопка 'Как читается' — ждем слово для транскрипции."""
    set_pending_action(user_id, "wait_pronounce")
    await update.message.reply_text(texts.ASK_WORD_PRONOUNCE)


async def start_meaning(update, context, user_id):
    """Кнопка 'Непонятно слово' — ждем слово для объяснения."""
    set_pending_action(user_id, "wait_meaning")
    await update.message.reply_text(texts.ASK_WORD_MEANING)


async def start_language(update, context, user_id):
    """Кнопка 'Язык правил' — показываем выбор языка объяснений."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    user = get_user(user_id)
    current = texts.LANG_NAMES.get(user["explanation_language"], "автоматически")

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"setlang:{code}")]
        for code, label in texts.BTN_LANGS.items()
    ]
    await update.message.reply_text(
        texts.ASK_LANG.format(current=current),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_language_button(update, context):
    """Обработка выбора языка объяснений."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    _, lang = query.data.split(":", 1)
    update_user(user_id, explanation_language=lang)
    memory.clear_history(user_id)  # сбрасываем историю, чтобы убрать инерцию языка
    await query.edit_message_text(
        texts.LANG_CHANGED.format(lang=texts.LANG_NAMES[lang])
    )
