"""Premium — прохождение ежедневного урока в Telegram."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot import texts
from bot.services.lesson_runner import KIND_LESSON, lesson_runner
from bot.services.session_store import save_session
from database.db import log_event

logger = logging.getLogger(__name__)


def _continue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(texts.BTN_LESSON_CONTINUE, callback_data="lesson:go")]]
    )


def _lesson_header(session: dict) -> str:
    return texts.LESSON_HEADER.format(
        module=session.get("module_title", ""),
        lesson=session.get("lesson_title", ""),
        day=session.get("day_number", ""),
    )


def render_step_message(session: dict, step: dict) -> str:
    header = _lesson_header(session)
    step_type = step["step_type"]
    payload = step.get("payload") or {}

    if step_type == "review":
        return f"{header}\n\n{texts.LESSON_STEP_REVIEW}"

    if step_type == "phrase":
        en = payload.get("phrase_en", "")
        ru = payload.get("phrase_ru", "")
        body = texts.LESSON_STEP_PHRASE.format(phrase_en=en, phrase_ru=ru)
        return f"{header}\n\n{body}"

    if step_type == "explain":
        title = payload.get("title_ru", "")
        body = payload.get("body_ru", "")
        return f"{header}\n\n{texts.LESSON_STEP_EXPLAIN.format(title=title, body=body)}"

    if step_type == "exercise":
        question = payload.get("question", "")
        return f"{header}\n\n{texts.LESSON_STEP_EXERCISE.format(question=question)}"

    if step_type == "apply":
        prompt = payload.get("prompt_ru", texts.LESSON_STEP_APPLY_DEFAULT)
        return f"{header}\n\n{texts.LESSON_STEP_APPLY.format(prompt=prompt)}"

    return f"{header}\n\n{texts.LESSON_STEP_UNKNOWN}"


def render_step_keyboard(step: dict) -> InlineKeyboardMarkup | None:
    step_type = step["step_type"]
    if step_type in {"review", "phrase", "explain"}:
        return _continue_keyboard()

    if step_type == "exercise":
        payload = step.get("payload") or {}
        options = payload.get("options") or []
        step_index = step.get("_index", 0)
        rows = [
            [InlineKeyboardButton(opt, callback_data=f"lesson:pick:{step_index}:{i}")]
            for i, opt in enumerate(options)
        ]
        rows.append(
            [InlineKeyboardButton(texts.BTN_LESSON_STOP, callback_data="lesson:stop")]
        )
        return InlineKeyboardMarkup(rows)

    if step_type == "apply":
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(texts.BTN_LESSON_STOP, callback_data="lesson:stop")]]
        )

    return _continue_keyboard()


def premium_lesson_keyboard(user_id: int) -> InlineKeyboardMarkup | None:
    ok, reason = lesson_runner.can_offer_lesson(user_id)
    if not ok:
        return None
    if reason == "resume":
        label = texts.BTN_LESSON_RESUME
        data = "lesson:resume"
    else:
        label = texts.BTN_LESSON_START
        data = "lesson:start"
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=data)]])


async def send_current_step(message, user_id: int, session: dict):
    step_index = session.get("step_index", 0)
    step = lesson_runner.current_step(session)
    if not step:
        await _finish(message, user_id, session)
        return

    step = {**step, "_index": step_index}
    text = render_step_message(session, step)
    keyboard = render_step_keyboard(step)
    session["awaiting_text"] = step["step_type"] == "apply"
    save_session(user_id, KIND_LESSON, session)
    await message.reply_text(text, reply_markup=keyboard)


async def _finish(message, user_id: int, session: dict):
    summary = lesson_runner.finish_lesson(user_id, session)
    correct = summary.get("exercise_correct", 0)
    total = summary.get("exercise_total", 0)
    await message.reply_text(
        texts.LESSON_COMPLETE.format(correct=correct, total=total)
    )
    log_event(user_id, "lesson_complete_ui")


async def handle_lesson_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    parts = query.data.split(":")
    action = parts[1]

    if action == "start":
        session = lesson_runner.begin_next_lesson(user_id)
        if not session:
            await query.edit_message_text(texts.LESSON_NONE)
            return
        log_event(user_id, "lesson_start_ui")
        await query.message.reply_text(texts.LESSON_STARTED)
        await send_current_step(query.message, user_id, session)
        return

    if action == "resume":
        session = lesson_runner.resume_lesson(user_id)
        if not session:
            await query.edit_message_text(texts.LESSON_EXPIRED)
            return
        await query.message.reply_text(texts.LESSON_RESUMED)
        await send_current_step(query.message, user_id, session)
        return

    if action == "stop":
        lesson_runner.cancel_lesson(user_id)
        await query.edit_message_text(texts.LESSON_STOPPED)
        return

    session = lesson_runner.get_session(user_id)
    if not session:
        await query.edit_message_text(texts.LESSON_EXPIRED)
        return

    if action == "go":
        step = lesson_runner.current_step(session)
        if not step or step["step_type"] not in {"review", "phrase", "explain"}:
            return
        lesson_runner.advance(user_id, session)
        session = lesson_runner.get_session(user_id)
        await send_current_step(query.message, user_id, session)
        return

    if action == "pick" and len(parts) == 4:
        step_index = int(parts[2])
        opt_index = int(parts[3])
        if step_index != session.get("step_index", 0):
            await query.edit_message_text(texts.LESSON_EXPIRED)
            lesson_runner.cancel_lesson(user_id)
            return

        step = lesson_runner.current_step(session)
        if not step or step["step_type"] != "exercise":
            return

        payload = step.get("payload") or {}
        options = payload.get("options") or []
        correct_idx = int(payload.get("correct", 0))
        if opt_index < 0 or opt_index >= len(options):
            return

        chosen = options[opt_index]
        is_correct = opt_index == correct_idx
        lesson_runner.record_exercise_result(session, correct=is_correct)
        if is_correct:
            feedback = texts.LESSON_EXERCISE_CORRECT
        else:
            feedback = texts.LESSON_EXERCISE_WRONG.format(
                answer=options[correct_idx] if correct_idx < len(options) else "—"
            )

        await query.edit_message_text(
            f"{render_step_message(session, step)}\n\n"
            f"Твой ответ: {chosen}\n{feedback}"
        )

        lesson_runner.advance(user_id, session)
        session = lesson_runner.get_session(user_id)
        if session:
            await send_current_step(query.message, user_id, session)
        return


async def handle_lesson_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    session = lesson_runner.get_session(user_id)
    if not session or not session.get("awaiting_text"):
        return False

    step = lesson_runner.current_step(session)
    if not step or step["step_type"] != "apply":
        return False

    text = (update.message.text or "").strip()
    payload = step.get("payload") or {}
    min_words = int(payload.get("min_words", 3))
    words = [w for w in text.split() if w]
    if len(words) < min_words:
        await update.message.reply_text(
            texts.LESSON_APPLY_TOO_SHORT.format(min_words=min_words)
        )
        return True

    session.setdefault("scores", {})["last_apply"] = text[:500]
    session["awaiting_text"] = False
    save_session(user_id, KIND_LESSON, session)
    await update.message.reply_text(texts.LESSON_APPLY_SAVED)

    lesson_runner.advance(user_id, session)
    session = lesson_runner.get_session(user_id)
    if session:
        await send_current_step(update.message, user_id, session)
    else:
        await _finish(update.message, user_id, session)
    return True
