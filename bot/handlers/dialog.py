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
)
from bot import memory, prompts, texts, keyboards
from bot.handlers import activities
from bot.services.ai import get_ai_response

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
        await _send_ai_reply(
            update,
            context,
            user_id,
            user,
            special=f"Объясни простыми словами, что значит '{text}', "
            f"и приведи пример употребления. Кратко.",
        )
        return

    # --- Обычный диалог ---
    await _send_ai_reply(update, context, user_id, user, user_text=text)


async def _send_ai_reply(update, context, user_id, user, user_text=None, special=None):
    """Общая функция: собрать промпт, позвать AI, отправить ответ.
    user_text — обычное сообщение пользователя (идет в историю).
    special — служебная инструкция для инструментов (НЕ идет в общую историю)."""
    # Собираем системный промпт с учетом языка объяснений
    system_prompt = prompts.build_system_prompt(
        style=user["style"],
        level=user["level"] or "unknown",
        explanation_language=user["explanation_language"],
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

    answer, usage = get_ai_response(system_prompt, history)

    if not special:
        memory.add_message(user_id, "assistant", answer)
    log_event(user_id, "dialog")

    # Чистим разметку и отправляем обычным текстом — надежно, без сбоев парсинга.
    clean_answer = _strip_markdown(answer)
    await update.message.reply_text(
        clean_answer,
        reply_markup=keyboards.main_keyboard(),
    )


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
