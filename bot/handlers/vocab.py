"""Premium: ручное добавление слов в словарь."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot import texts, keyboards
from bot.i18n import t
from bot.services.premium_gate import PremiumFeature, check_feature, feature_denied_text
from database.db import (
    get_user,
    set_pending_action,
    add_words_batch,
    sync_progress_words,
    log_event,
)

logger = logging.getLogger(__name__)

_SEPARATORS = (" — ", " – ", " - ", "—", "–", "-")


def _parse_word_line(text: str) -> tuple[str, str] | None:
    """Разобрать «word — перевод»."""
    text = text.strip()
    for sep in _SEPARATORS:
        if sep in text:
            word, translation = text.split(sep, 1)
            word, translation = word.strip(), translation.strip()
            if word and translation:
                return word, translation
    return None


async def addword_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /addword — только Premium."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user["onboarding_done"]:
        await update.message.reply_text(
            t("ONBOARDING_REQUIRED", user_id=user_id)
        )
        return

    access = check_feature(user_id, PremiumFeature.ADDWORD)
    if not access.allowed:
        await update.message.reply_text(
            feature_denied_text(PremiumFeature.ADDWORD, user_id),
            reply_markup=keyboards.premium_upsell_keyboard(user_id),
        )
        return

    # Аргументы: /addword apple — яблоко
    if context.args:
        parsed = _parse_word_line(" ".join(context.args))
        if parsed:
            await _save_word(update, user_id, parsed[0], parsed[1])
            return
        await update.message.reply_text(texts.ADDWORD_FORMAT)
        return

    set_pending_action(user_id, "wait_add_word")
    await update.message.reply_text(texts.ADDWORD_ASK)


async def handle_add_word_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, text: str
):
    """Обработка текста после /addword без аргументов."""
    set_pending_action(user_id, None)
    parsed = _parse_word_line(text)
    if not parsed:
        await update.message.reply_text(
            texts.ADDWORD_FORMAT, reply_markup=keyboards.main_keyboard()
        )
        return
    await _save_word(update, user_id, parsed[0], parsed[1])


async def _save_word(update, user_id, word, translation):
    add_words_batch(
        user_id,
        [{"word": word, "translation": translation, "transcription": "", "example": ""}],
        "вручную",
    )
    sync_progress_words(user_id)
    log_event(user_id, "add_word")
    await update.message.reply_text(
        texts.ADDWORD_SAVED.format(word=word, translation=translation),
        reply_markup=keyboards.main_keyboard(),
    )
