"""Premium-диагностика навыков."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.i18n import t
from bot.services.diagnostic_service import (
    KIND_DIAGNOSTIC,
    QUESTIONS,
    can_take_diagnostic,
    format_skill_profile,
    save_diagnostic_result,
)
from bot.services.session_store import clear_session, get_session, save_session
from database.db import log_event

logger = logging.getLogger(__name__)


def _question_keyboard(q_index: int, q) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(opt, callback_data=f"diag:{q_index}:{opt_idx}")]
        for opt_idx, opt in enumerate(q.options)
    ]
    return InlineKeyboardMarkup(rows)


def diagnostic_keyboard(user_id: int | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("BTN_DIAGNOSTIC_START", user_id=user_id),
                    callback_data="diag:start",
                )
            ]
        ]
    )


def _blocked_message(reason: str, user_id: int) -> str:
    if reason == "not_premium":
        return t("DIAG_NOT_PREMIUM", user_id=user_id)
    if reason == "setup_required":
        return t("DIAG_SETUP_REQUIRED", user_id=user_id)
    if reason == "already_done":
        return t("DIAG_ALREADY_DONE", user_id=user_id)
    return t("DIAG_UNAVAILABLE", user_id=user_id)


async def start_diagnostic(message, user_id: int) -> bool:
    allowed, reason = can_take_diagnostic(user_id)
    if not allowed:
        await message.reply_text(_blocked_message(reason, user_id))
        return False

    save_session(
        user_id,
        KIND_DIAGNOSTIC,
        {"index": 0, "answers": []},
    )
    log_event(user_id, "diagnostic_start")
    await message.reply_text(t("DIAG_INTRO", user_id=user_id))
    await _send_question(message, user_id, 0)
    return True


async def _send_question(message, user_id: int, index: int):
    q = QUESTIONS[index]
    total = len(QUESTIONS)
    header = t("DIAG_QUESTION", user_id=user_id, n=index + 1, total=total)
    body = q.text
    if q.passage:
        body = f"{q.passage}\n\n{q.text}"
    await message.reply_text(
        f"{header}\n\n{body}",
        reply_markup=_question_keyboard(index, q),
    )


async def handle_diagnostic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    parts = query.data.split(":")
    action = parts[1]

    if action == "start":
        allowed, reason = can_take_diagnostic(user_id)
        if not allowed:
            await query.edit_message_text(_blocked_message(reason, user_id))
            return
        save_session(user_id, KIND_DIAGNOSTIC, {"index": 0, "answers": []})
        log_event(user_id, "diagnostic_start")
        await query.edit_message_text(t("DIAG_INTRO", user_id=user_id))
        await _send_question(query.message, user_id, 0)
        return

    session = get_session(user_id, KIND_DIAGNOSTIC)
    if not session:
        await query.edit_message_text(t("DIAG_EXPIRED", user_id=user_id))
        return

    q_index = int(parts[1])
    opt_idx = int(parts[2])

    if q_index != session.get("index", 0):
        await query.edit_message_text(t("DIAG_EXPIRED", user_id=user_id))
        clear_session(user_id, KIND_DIAGNOSTIC)
        return

    q = QUESTIONS[q_index]
    is_correct = opt_idx == q.correct
    answers = session.get("answers", [])
    answers.append(is_correct)
    session["answers"] = answers

    chosen = q.options[opt_idx]
    correct = q.options[q.correct]
    feedback = (
        t("DIAG_CORRECT", user_id=user_id)
        if is_correct
        else t("DIAG_WRONG", user_id=user_id, answer=correct)
    )

    next_index = q_index + 1
    session["index"] = next_index
    save_session(user_id, KIND_DIAGNOSTIC, session)

    shown = q.text
    if q.passage:
        shown = f"{q.passage}\n\n{q.text}"
    await query.edit_message_text(
        f"{t('DIAG_QUESTION', user_id=user_id, n=q_index + 1, total=len(QUESTIONS))}\n\n"
        f"{shown}\n\n"
        f"{t('DIAG_YOUR_ANSWER', user_id=user_id, answer=chosen)}\n{feedback}"
    )

    if next_index < len(QUESTIONS):
        await _send_question(query.message, user_id, next_index)
        return

    await _finish(query.message, user_id, answers)


async def _finish(message, user_id: int, answers: list[bool]):
    skills = save_diagnostic_result(user_id, answers)
    clear_session(user_id, KIND_DIAGNOSTIC)
    log_event(user_id, "diagnostic_done")
    await message.reply_text(
        t(
            "DIAG_RESULT",
            user_id=user_id,
            profile=format_skill_profile(skills),
        )
    )
    from bot.handlers.premium_lesson import premium_lesson_keyboard

    markup = premium_lesson_keyboard(user_id)
    if markup:
        await message.reply_text(
            t("DIAG_AFTER_SETUP_LESSON", user_id=user_id),
            reply_markup=markup,
        )


def needs_diagnostic(user_id: int) -> bool:
    allowed, _ = can_take_diagnostic(user_id)
    return allowed
