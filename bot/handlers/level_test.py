"""Тест на уровень — онбординг и настройки."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot import texts
from bot.services.level_test import (
    KIND_LEVEL_TEST,
    QUESTIONS,
    can_take_level_test,
    save_level_result,
    score_to_level,
)
from bot.services.session_store import clear_session, get_session, save_session
from database.db import get_user, log_event, update_user

logger = logging.getLogger(__name__)


def _goal_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(label, callback_data=f"goal:{code}")]
        for code, label in texts.BTN_GOALS.items()
    ]
    return InlineKeyboardMarkup(rows)


def _question_keyboard(q_index: int, q) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(opt, callback_data=f"ltest:{q_index}:{opt_idx}")]
        for opt_idx, opt in enumerate(q.options)
    ]
    return InlineKeyboardMarkup(rows)


async def start_level_test(
    target,
    user_id: int,
    *,
    during_onboarding: bool = False,
):
    """Запустить тест. target — message или callback query."""
    message = target.message if hasattr(target, "message") else target

    allowed, reason = can_take_level_test(
        user_id, during_onboarding=during_onboarding
    )
    if not allowed:
        text = _blocked_message(user_id, reason)
        if hasattr(target, "edit_message_text"):
            await target.edit_message_text(text)
        else:
            await message.reply_text(text)
        return False

    save_session(
        user_id,
        KIND_LEVEL_TEST,
        {
            "index": 0,
            "score": 0,
            "during_onboarding": during_onboarding,
        },
    )
    log_event(user_id, "level_test_start")
    await message.reply_text(texts.LEVEL_TEST_INTRO)
    await _send_question(message, user_id, 0)
    return True


def _blocked_message(user_id: int, reason: str) -> str:
    user = get_user(user_id)
    level = user.get("level") if user else None
    if level in texts.BTN_LEVELS and level != "unknown":
        level_label = texts.BTN_LEVELS[level]
    elif level == "unknown":
        level_label = "не определён"
    else:
        level_label = level or "—"

    if reason == "free_once":
        return texts.LEVEL_TEST_FREE_ONCE.format(level=level_label)
    if reason.startswith("premium_wait:"):
        days = reason.split(":", 1)[1]
        return texts.LEVEL_TEST_PREMIUM_WAIT.format(days=days)
    return texts.LEVEL_TEST_UNAVAILABLE


async def _send_question(message, user_id: int, index: int):
    q = QUESTIONS[index]
    total = len(QUESTIONS)
    text = texts.LEVEL_TEST_QUESTION.format(
        n=index + 1,
        total=total,
        question=q.text,
    )
    await message.reply_text(
        text,
        reply_markup=_question_keyboard(index, q),
    )


async def handle_level_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    session = get_session(user_id, KIND_LEVEL_TEST)
    if not session:
        await query.edit_message_text(texts.LEVEL_TEST_EXPIRED)
        return

    _, q_index_str, opt_str = query.data.split(":", 2)
    q_index = int(q_index_str)
    opt_idx = int(opt_str)

    if q_index != session.get("index", 0):
        await query.edit_message_text(texts.LEVEL_TEST_EXPIRED)
        clear_session(user_id, KIND_LEVEL_TEST)
        return

    q = QUESTIONS[q_index]
    if opt_idx == q.correct:
        session["score"] = session.get("score", 0) + q.weight

    chosen = q.options[opt_idx]
    correct = q.options[q.correct]
    if opt_idx == q.correct:
        feedback = texts.LEVEL_TEST_CORRECT
    else:
        feedback = texts.LEVEL_TEST_WRONG.format(answer=correct)

    next_index = q_index + 1
    session["index"] = next_index
    save_session(user_id, KIND_LEVEL_TEST, session)

    await query.edit_message_text(
        f"{texts.LEVEL_TEST_QUESTION.format(n=q_index + 1, total=len(QUESTIONS), question=q.text)}\n\n"
        f"Твой ответ: {chosen}\n{feedback}"
    )

    if next_index < len(QUESTIONS):
        await _send_question(query.message, user_id, next_index)
        return

    await _finish_test(query.message, user_id, session)


async def _finish_test(message, user_id: int, session: dict):
    level = score_to_level(session.get("score", 0))
    save_level_result(user_id, level)
    clear_session(user_id, KIND_LEVEL_TEST)
    log_event(user_id, f"level_test_{level}")

    label = texts.BTN_LEVELS[level]
    await message.reply_text(texts.LEVEL_TEST_RESULT.format(level=label))

    if session.get("during_onboarding"):
        update_user(user_id, onboarding_step="goal")
        await message.reply_text(
            texts.ASK_GOAL,
            reply_markup=_goal_keyboard(),
        )
    else:
        await message.reply_text(
            texts.SETTINGS_SAVED.format(setting=label)
            + "\n\n/settings — изменить ещё что-то"
        )
