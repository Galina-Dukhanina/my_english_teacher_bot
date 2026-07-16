"""Premium — прохождение ежедневного урока в Telegram."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from bot.i18n import t
from bot.repositories.attempt_repo import AttemptRepository
from bot.repositories.learning_profile_repo import LearningProfileRepository
from bot.services.ai_gateway import check_writing
from bot.services.lesson_runner import KIND_LESSON, lesson_runner
from bot.services.session_store import save_session
from database.db import log_event

logger = logging.getLogger(__name__)


def _continue_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("BTN_LESSON_CONTINUE", user_id=user_id),
                    callback_data="lesson:go",
                )
            ]
        ]
    )


def _review_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("BTN_LESSON_REVIEW_KNEW", user_id=user_id),
                    callback_data="lesson:rev:1",
                )
            ],
            [
                InlineKeyboardButton(
                    t("BTN_LESSON_REVIEW_HINT", user_id=user_id),
                    callback_data="lesson:rev:2",
                ),
                InlineKeyboardButton(
                    t("BTN_LESSON_REVIEW_FORGOT", user_id=user_id),
                    callback_data="lesson:rev:0",
                ),
            ],
        ]
    )


def _review_next_keyboard(user_id: int, result_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("BTN_LESSON_REVIEW_NEXT", user_id=user_id),
                    callback_data=f"lesson:revnext:{result_code}",
                )
            ]
        ]
    )


def _lesson_header(session: dict, user_id: int) -> str:
    return t(
        "LESSON_HEADER",
        user_id=user_id,
        module=session.get("module_title", ""),
        lesson=session.get("lesson_title", ""),
        day=session.get("day_number", ""),
    )


def _current_review_item(step: dict) -> tuple[dict | None, int, int]:
    payload = step.get("payload") or {}
    items = payload.get("items") or []
    index = int(payload.get("index", 0))
    if index >= len(items):
        return None, index, len(items)
    return items[index], index + 1, len(items)


def render_step_message(session: dict, step: dict, user_id: int) -> str:
    header = _lesson_header(session, user_id)
    step_type = step["step_type"]
    payload = step.get("payload") or {}

    if step_type == "review":
        item, current, total = _current_review_item(step)
        if not item:
            return f"{header}\n\n{t('LESSON_REVIEW_DONE', user_id=user_id)}"
        return (
            f"{header}\n\n"
            f"{t('LESSON_STEP_REVIEW', user_id=user_id, current=current, total=total, phrase_ru=item.get('phrase_ru', ''))}"
        )

    if step_type == "phrase":
        en = payload.get("phrase_en", "")
        ru = payload.get("phrase_ru", "")
        body = t("LESSON_STEP_PHRASE", user_id=user_id, phrase_en=en, phrase_ru=ru)
        return f"{header}\n\n{body}"

    if step_type == "explain":
        title = payload.get("title_ru", "")
        body = payload.get("body_ru", "")
        return f"{header}\n\n{t('LESSON_STEP_EXPLAIN', user_id=user_id, title=title, body=body)}"

    if step_type == "exercise":
        question = payload.get("question", "")
        return f"{header}\n\n{t('LESSON_STEP_EXERCISE', user_id=user_id, question=question)}"

    if step_type == "apply":
        prompt = payload.get(
            "prompt_ru", t("LESSON_STEP_APPLY_DEFAULT", user_id=user_id)
        )
        return f"{header}\n\n{t('LESSON_STEP_APPLY', user_id=user_id, prompt=prompt)}"

    return f"{header}\n\n{t('LESSON_STEP_UNKNOWN', user_id=user_id)}"


def render_step_keyboard(step: dict, user_id: int) -> InlineKeyboardMarkup | None:
    step_type = step["step_type"]
    if step_type == "review":
        item, _, _ = _current_review_item(step)
        if not item:
            return _continue_keyboard(user_id)
        return _review_keyboard(user_id)

    if step_type in {"phrase", "explain"}:
        return _continue_keyboard(user_id)

    if step_type == "exercise":
        payload = step.get("payload") or {}
        options = payload.get("options") or []
        step_index = step.get("_index", 0)
        rows = [
            [InlineKeyboardButton(opt, callback_data=f"lesson:pick:{step_index}:{i}")]
            for i, opt in enumerate(options)
        ]
        rows.append(
            [
                InlineKeyboardButton(
                    t("BTN_LESSON_STOP", user_id=user_id),
                    callback_data="lesson:stop",
                )
            ]
        )
        return InlineKeyboardMarkup(rows)

    if step_type == "apply":
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        t("BTN_LESSON_STOP", user_id=user_id),
                        callback_data="lesson:stop",
                    )
                ]
            ]
        )

    return _continue_keyboard(user_id)


def premium_lesson_keyboard(user_id: int) -> InlineKeyboardMarkup | None:
    ok, reason = lesson_runner.can_offer_lesson(user_id)
    if not ok:
        return None
    if reason == "resume":
        label = t("BTN_LESSON_RESUME", user_id=user_id)
        data = "lesson:resume"
    else:
        label = t("BTN_LESSON_START", user_id=user_id)
        data = "lesson:start"
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=data)]])


async def send_current_step(message, user_id: int, session: dict):
    session["user_id"] = user_id
    step = lesson_runner.current_step(session)
    while step and step.get("step_type") == "review":
        payload = step.get("payload") or {}
        if not payload.get("items"):
            lesson_runner.advance(user_id, session)
            session = lesson_runner.get_session(user_id) or session
            step = lesson_runner.current_step(session)
        else:
            break

    if not step:
        await _finish(message, user_id, session)
        return

    step_index = session.get("step_index", 0)
    step = {**step, "_index": step_index}
    text = render_step_message(session, step, user_id)
    keyboard = render_step_keyboard(step, user_id)
    session["awaiting_text"] = step["step_type"] == "apply"
    save_session(user_id, KIND_LESSON, session)
    await message.reply_text(text, reply_markup=keyboard)


async def _finish(message, user_id: int, session: dict):
    summary = lesson_runner.finish_lesson(user_id, session)
    correct = summary.get("exercise_correct", 0)
    total = summary.get("exercise_total", 0)
    apply_passed = summary.get("apply_passed", 0)
    apply_total = summary.get("apply_total", 0)
    await message.reply_text(
        t(
            "LESSON_COMPLETE",
            user_id=user_id,
            correct=correct,
            total=total,
            apply_passed=apply_passed,
            apply_total=apply_total,
        )
    )
    log_event(user_id, "lesson_complete_ui")


async def _after_review_answer(query, user_id: int, session: dict, result_code: str):
    step = lesson_runner.current_step(session)
    if not step or step.get("step_type") != "review":
        return

    item, _, _ = _current_review_item(step)
    if not item:
        return

    if result_code == "2":
        hint_text = t(
            "LESSON_REVIEW_HINT",
            user_id=user_id,
            phrase_en=item.get("phrase_en", ""),
        )
        await query.edit_message_text(
            f"{render_step_message(session, step, user_id)}\n\n{hint_text}",
            reply_markup=_review_next_keyboard(user_id, "2"),
        )
        return

    outcome = lesson_runner.record_review_response(
        user_id, session, item["id"], result_code
    )
    if result_code == "0":
        feedback = t(
            "LESSON_REVIEW_WRONG",
            user_id=user_id,
            phrase_en=(outcome or {}).get("phrase_en", item.get("phrase_en", "")),
        )
        await query.edit_message_text(
            f"{render_step_message(session, step, user_id)}\n\n{feedback}",
            reply_markup=_review_next_keyboard(user_id, "0"),
        )
        return

    feedback = t("LESSON_REVIEW_CORRECT", user_id=user_id)
    await query.edit_message_text(
        f"{render_step_message(session, step, user_id)}\n\n{feedback}"
    )
    session = lesson_runner.advance_review(user_id, session)
    session = lesson_runner.get_session(user_id)
    if session:
        await send_current_step(query.message, user_id, session)


async def handle_lesson_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    parts = query.data.split(":")
    action = parts[1]

    if action == "start":
        session = lesson_runner.begin_next_lesson(user_id)
        if not session:
            await query.edit_message_text(t("LESSON_NONE", user_id=user_id))
            return
        log_event(user_id, "lesson_start_ui")
        await query.message.reply_text(t("LESSON_STARTED", user_id=user_id))
        await send_current_step(query.message, user_id, session)
        return

    if action == "resume":
        session = lesson_runner.resume_lesson(user_id)
        if not session:
            await query.edit_message_text(t("LESSON_EXPIRED", user_id=user_id))
            return
        await query.message.reply_text(t("LESSON_RESUMED", user_id=user_id))
        await send_current_step(query.message, user_id, session)
        return

    if action == "stop":
        lesson_runner.cancel_lesson(user_id)
        await query.edit_message_text(t("LESSON_STOPPED", user_id=user_id))
        return

    session = lesson_runner.get_session(user_id)
    if not session:
        await query.edit_message_text(t("LESSON_EXPIRED", user_id=user_id))
        return

    if action == "go":
        step = lesson_runner.current_step(session)
        if not step or step["step_type"] not in {"phrase", "explain"}:
            return
        if step["step_type"] == "phrase":
            lesson_runner.on_step_completed(user_id, session, step)
        lesson_runner.advance(user_id, session)
        session = lesson_runner.get_session(user_id)
        await send_current_step(query.message, user_id, session)
        return

    if action == "rev" and len(parts) == 3:
        await _after_review_answer(query, user_id, session, parts[2])
        return

    if action == "revnext" and len(parts) == 3:
        result_code = parts[2]
        step = lesson_runner.current_step(session)
        if not step or step.get("step_type") != "review":
            return
        item, _, _ = _current_review_item(step)
        if item and result_code == "2":
            lesson_runner.record_review_response(user_id, session, item["id"], "2")
        session = lesson_runner.advance_review(user_id, session)
        session = lesson_runner.get_session(user_id)
        if session:
            await send_current_step(query.message, user_id, session)
        return

    if action == "pick" and len(parts) == 4:
        step_index = int(parts[2])
        opt_index = int(parts[3])
        if step_index != session.get("step_index", 0):
            await query.edit_message_text(t("LESSON_EXPIRED", user_id=user_id))
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
        lesson_runner.record_exercise_result(user_id, session, correct=is_correct)
        if is_correct:
            feedback = t("LESSON_EXERCISE_CORRECT", user_id=user_id)
        else:
            feedback = t(
                "LESSON_EXERCISE_WRONG",
                user_id=user_id,
                answer=options[correct_idx] if correct_idx < len(options) else "—",
            )

        step = {**step, "_index": step_index}
        await query.edit_message_text(
            f"{render_step_message(session, step, user_id)}\n\n"
            f"{t('LESSON_YOUR_ANSWER', user_id=user_id, answer=chosen)}\n{feedback}"
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
            t("LESSON_APPLY_TOO_SHORT", user_id=user_id, min_words=min_words)
        )
        return True

    session["awaiting_text"] = False
    save_session(user_id, KIND_LESSON, session)
    await update.message.reply_text(t("LESSON_APPLY_CHECKING", user_id=user_id))
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    profile = LearningProfileRepository().get(user_id) or {}
    ctx = lesson_runner.lesson_context_for_apply(session)
    default_prompt = t("LESSON_STEP_APPLY_DEFAULT", user_id=user_id)
    result, error_message = check_writing(
        user_id,
        prompt_ru=payload.get("prompt_ru", default_prompt),
        user_text=text,
        cefr_level=profile.get("cefr_level") or "A1",
        phrase_en=ctx.get("phrase_en", ""),
        explain_ru=ctx.get("explain_ru", ""),
    )

    attempt_repo = AttemptRepository()
    if result:
        lesson_runner.record_apply_result(
            user_id,
            session,
            step,
            passed=result.passed,
            score=result.score,
        )
        attempt_repo.log_attempt(
            user_id,
            lesson_id=session.get("lesson_id"),
            lesson_step_id=step.get("step_id"),
            answer_text=text,
            result=result.raw or {},
            score=result.score,
        )
        if result.passed:
            feedback = t(
                "LESSON_APPLY_PASSED", user_id=user_id, feedback=result.feedback_ru
            )
        else:
            corrected = result.corrected_text or text
            feedback = t(
                "LESSON_APPLY_FAILED",
                user_id=user_id,
                feedback=result.feedback_ru,
                corrected=corrected,
            )
    else:
        session.setdefault("scores", {})["last_apply"] = text[:500]
        feedback = error_message or t("LESSON_APPLY_AI_UNAVAILABLE", user_id=user_id)
        save_session(user_id, KIND_LESSON, session)

    await update.message.reply_text(feedback)

    lesson_runner.advance(user_id, session)
    session = lesson_runner.get_session(user_id)
    if session:
        await send_current_step(update.message, user_id, session)
    else:
        await _finish(update.message, user_id, session)
    return True
