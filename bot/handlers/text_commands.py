"""Русские текстовые команды (без слэша)."""

import re

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot import texts
from bot.handlers import commands, settings, feedback, premium

_TEXT_HANDLERS = {
    texts.CMD_STYLE: commands.style_command,
    texts.CMD_SETTINGS: settings.settings_command,
    texts.CMD_REMINDERS: commands.reminders_command,
    texts.CMD_PROGRESS: commands.progress_command,
    texts.CMD_PREMIUM: premium.premium_command,
    texts.CMD_HELP: commands.help_command,
    texts.CMD_FEEDBACK: feedback.feedback_command,
    "Premium": premium.premium_command,
    "Помощь": commands.help_command,
    "Оставить отзыв": feedback.feedback_command,
}

_PATTERN = re.compile(
    r"^(" + "|".join(re.escape(k) for k in _TEXT_HANDLERS) + r")$",
    re.IGNORECASE,
)


async def handle_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    handler = _TEXT_HANDLERS.get(text)
    if not handler:
        for key, fn in _TEXT_HANDLERS.items():
            if key.lower() == text.lower():
                handler = fn
                break
    if handler:
        await handler(update, context)


def text_command_handler() -> MessageHandler:
    return MessageHandler(filters.TEXT & ~filters.COMMAND & _PATTERN, handle_text_command)
