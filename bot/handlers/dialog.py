import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from database.db import get_user, log_event
from bot import memory, prompts
from bot.services.ai import get_ai_response

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик текстовых сообщений — основной диалог с AI."""
    user_id = update.effective_user.id
    text = update.message.text

    # --- Краевой случай: пустое сообщение ---
    if not text or not text.strip():
        await update.message.reply_text("Напиши мне что-нибудь текстом, и я отвечу.")
        return

    # --- Краевой случай: пользователь не прошел онбординг ---
    user = get_user(user_id)
    if not user or not user["onboarding_done"]:
        await update.message.reply_text(
            "Давай сначала настроим все под тебя. Нажми /start"
        )
        return

    # --- Собираем системный промпт под этого пользователя ---
    system_prompt = prompts.build_system_prompt(
        style=user["style"],
        level=user["level"] or "unknown",
    )

    # --- Добавляем сообщение пользователя в историю ---
    memory.add_message(user_id, "user", text)
    history = memory.get_history(user_id)

    # --- Показываем "печатает...", пока ждем AI ---
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )

    # --- Запрашиваем ответ у AI ---
    answer, usage = get_ai_response(system_prompt, history)

    # --- Сохраняем ответ в историю и отправляем пользователю ---
    memory.add_message(user_id, "assistant", answer)
    log_event(user_id, "dialog")

    # Пробуем отправить с Markdown-форматированием.
    # Если модель вставила кривую разметку и Telegram ругается —
    # отправляем обычным текстом, чтобы сообщение точно дошло.
    try:
        await update.message.reply_text(answer, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Markdown не распарсился, отправляю как обычный текст: {e}")
        await update.message.reply_text(answer)
