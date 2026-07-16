"""Premium-диагностика навыков."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot import texts
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


def diagnostic_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    texts.BTN_DIAGNOSTIC_START,
                    callback_data="diag:start",
                )
            ]
        ]
    )


async def start_diagnostic(message, user_id: int) -> bool:
    allowed, reason = can_take_diagnostic(user_id)
    if not allowed:
        text = _blocked_message(reason)
        await message.reply_text(text)
        return False

    save_session(
        user_id,
        KIND_DIAGNOSTIC,
        {"index": 0, "answers": []},
    )
    log_event(user_id, "diagnostic_start")
    await message.reply_text(texts.DIAG_INTRO)
    await _send_question(message, 0)
    return True


def _blocked_message(reason: str) -> str:
    if reason == "not_premium":
        return texts.DIAG_NOT_PREMIUM
    if reason == "setup_required":
        return texts.DIAG_SETUP_REQUIRED
    if reason == "already_done":
        return texts.DIAG_ALREADY_DONE
    return texts.DIAG_UNAVAILABLE


async def _send_question(message, index: int):
    q = QUESTIONS[index]
    total = len(QUESTIONS)
    header = texts.DIAG_QUESTION.format(n=index + 1, total=total)
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
            await query.edit_message_text(_blocked_message(reason))
            return
        save_session(user_id, KIND_DIAGNOSTIC, {"index": 0, "answers": []})
        log_event(user_id, "diagnostic_start")
        await query.edit_message_text(texts.DIAG_INTRO)
        await _send_question(query.message, 0)
        return

    session = get_session(user_id, KIND_DIAGNOSTIC)
    if not session:
        await query.edit_message_text(texts.DIAG_EXPIRED)
        return

    q_index = int(parts[1])
    opt_idx = int(parts[2])

    if q_index != session.get("index", 0):
        await query.edit_message_text(texts.DIAG_EXPIRED)
        clear_session(user_id, KIND_DIAGNOSTIC)
        return

    q = QUESTIONS[q_index]
    is_correct = opt_idx == q.correct
    answers = session.get("answers", [])
    answers.append(is_correct)
    session["answers"] = answers

    chosen = q.options[opt_idx]
    correct = q.options[q.correct]
    feedback = texts.DIAG_CORRECT if is_correct else texts.DIAG_WRONG.format(answer=correct)

    next_index = q_index + 1
    session["index"] = next_index
    save_session(user_id, KIND_DIAGNOSTIC, session)

    shown = q.text
    if q.passage:
        shown = f"{q.passage}\n\n{q.text}"
    await query.edit_message_text(
        f"{texts.DIAG_QUESTION.format(n=q_index + 1, total=len(QUESTIONS))}\n\n"
        f"{shown}\n\n"
        f"Твой ответ: {chosen}\n{feedback}"
    )

    if next_index < len(QUESTIONS):
        await _send_question(query.message, next_index)
        return

    await _finish(query.message, user_id, answers)


async def _finish(message, user_id: int, answers: list[bool]):
    skills = save_diagnostic_result(user_id, answers)
    clear_session(user_id, KIND_DIAGNOSTIC)
    log_event(user_id, "diagnostic_done")
    await message.reply_text(
        texts.DIAG_RESULT.format(profile=format_skill_profile(skills))
    )


def needs_diagnostic(user_id: int) -> bool:
    allowed, _ = can_take_diagnostic(user_id)
    return allowed
