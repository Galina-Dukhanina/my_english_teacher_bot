"""Premium setup — пошаговая настройка программы обучения."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.i18n import t, td
from bot.services.profile_service import (
    STEP_DAILY_MINUTES,
    STEP_EXAM_DATE,
    STEP_EXAM_TYPE,
    STEP_INTERESTS,
    STEP_PROFESSION,
    STEP_WEAK_SKILL,
    profile_service,
)
from bot.services.subscription import is_premium
from database.db import get_user, log_event

logger = logging.getLogger(__name__)


def _buttons(options: dict[str, str], prefix: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(label, callback_data=f"{prefix}:{code}")]
        for code, label in options.items()
    ]
    return InlineKeyboardMarkup(rows)


async def _send_step(message, user_id: int, step: str):
    if step == STEP_PROFESSION:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        t("BTN_PREMIUM_SKIP", user_id=user_id),
                        callback_data="premsetup:skip",
                    )
                ]
            ]
        )
        await message.reply_text(
            t("PREMIUM_SETUP_PROFESSION", user_id=user_id),
            reply_markup=keyboard,
        )
        return

    if step == STEP_DAILY_MINUTES:
        await message.reply_text(
            t("PREMIUM_SETUP_MINUTES", user_id=user_id),
            reply_markup=_buttons(td("BTN_PREMIUM_MINUTES", user_id=user_id), "premsetup:min"),
        )
        return

    if step == STEP_EXAM_TYPE:
        await message.reply_text(
            t("PREMIUM_SETUP_EXAM_TYPE", user_id=user_id),
            reply_markup=_buttons(td("BTN_EXAM_TYPES", user_id=user_id), "premsetup:exam"),
        )
        return

    if step == STEP_EXAM_DATE:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        t("BTN_PREMIUM_SKIP", user_id=user_id),
                        callback_data="premsetup:skipdate",
                    )
                ]
            ]
        )
        await message.reply_text(
            t("PREMIUM_SETUP_EXAM_DATE", user_id=user_id),
            reply_markup=keyboard,
        )
        return

    if step == STEP_WEAK_SKILL:
        await message.reply_text(
            t("PREMIUM_SETUP_WEAK_SKILL", user_id=user_id),
            reply_markup=_buttons(td("BTN_WEAK_SKILLS", user_id=user_id), "premsetup:weak"),
        )
        return

    if step == STEP_INTERESTS:
        await message.reply_text(
            t("PREMIUM_SETUP_INTERESTS", user_id=user_id),
            reply_markup=_buttons(
                td("BTN_PREMIUM_INTERESTS", user_id=user_id), "premsetup:int"
            ),
        )
        return


async def start_premium_setup(message, user_id: int) -> bool:
    if not is_premium(user_id):
        await message.reply_text(t("PREMIUM_SETUP_NOT_PREMIUM", user_id=user_id))
        return False

    user = get_user(user_id)
    if not user or not user["onboarding_done"]:
        await message.reply_text(t("ONBOARDING_REQUIRED", user_id=user_id))
        return False

    if not profile_service.needs_premium_setup(user_id):
        await message.reply_text(t("PREMIUM_SETUP_ALREADY", user_id=user_id))
        return False

    step = profile_service.start_setup(user_id)
    await message.reply_text(t("PREMIUM_SETUP_INTRO", user_id=user_id))
    await _send_step(message, user_id, step)
    return True


async def handle_premium_setup_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not is_premium(user_id):
        await query.edit_message_text(t("PREMIUM_SETUP_NOT_PREMIUM", user_id=user_id))
        return

    session = profile_service.get_setup_session(user_id)
    if not session:
        await query.edit_message_text(t("PREMIUM_SETUP_EXPIRED", user_id=user_id))
        return

    step = profile_service.current_step(session)
    data = query.data.split(":", 2)
    skip_label = t("BTN_PREMIUM_SKIP", user_id=user_id)

    if data[1] == "skip" and step == STEP_PROFESSION:
        await query.edit_message_text(
            f"{t('PREMIUM_SETUP_PROFESSION', user_id=user_id)}\n\n⏭ {skip_label}"
        )
        next_step = profile_service.save_answer(user_id, session, "profession", None)
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, user_id, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "skipdate" and step == STEP_EXAM_DATE:
        await query.edit_message_text(
            f"{t('PREMIUM_SETUP_EXAM_DATE', user_id=user_id)}\n\n⏭ {skip_label}"
        )
        next_step = profile_service.save_answer(user_id, session, "exam_date", None)
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, user_id, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "min" and step == STEP_DAILY_MINUTES:
        minutes = int(data[2])
        minute_labels = td("BTN_PREMIUM_MINUTES", user_id=user_id)
        label = minute_labels.get(str(minutes), str(minutes))
        await query.edit_message_text(
            f"{t('PREMIUM_SETUP_MINUTES', user_id=user_id)}\n\n✅ {label}"
        )
        next_step = profile_service.save_answer(user_id, session, "daily_minutes", minutes)
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, user_id, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "exam" and step == STEP_EXAM_TYPE:
        exam_type = data[2]
        exam_types = td("BTN_EXAM_TYPES", user_id=user_id)
        if exam_type not in exam_types:
            return
        await query.edit_message_text(
            f"{t('PREMIUM_SETUP_EXAM_TYPE', user_id=user_id)}\n\n✅ {exam_types[exam_type]}"
        )
        next_step = profile_service.save_answer(user_id, session, "exam_type", exam_type)
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, user_id, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "weak" and step == STEP_WEAK_SKILL:
        skill = data[2]
        weak_skills = td("BTN_WEAK_SKILLS", user_id=user_id)
        if skill not in weak_skills:
            return
        await query.edit_message_text(
            f"{t('PREMIUM_SETUP_WEAK_SKILL', user_id=user_id)}\n\n✅ {weak_skills[skill]}"
        )
        next_step = profile_service.save_answer(user_id, session, "weak_skill", skill)
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, user_id, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "int" and step == STEP_INTERESTS:
        interest = data[2]
        interests = td("BTN_PREMIUM_INTERESTS", user_id=user_id)
        if interest not in interests:
            return
        await query.edit_message_text(
            f"{t('PREMIUM_SETUP_INTERESTS', user_id=user_id)}\n\n✅ {interests[interest]}"
        )
        next_step = profile_service.save_answer(user_id, session, "interests", [interest])
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, user_id, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "start":
        if profile_service.get_setup_session(user_id):
            profile_service.cancel_setup(user_id)
        step = profile_service.start_setup(user_id)
        await query.edit_message_text(t("PREMIUM_SETUP_INTRO", user_id=user_id))
        await _send_step(query.message, user_id, step)
        return


async def handle_setup_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """True, если сообщение обработано setup-ом."""
    user_id = update.effective_user.id
    session = profile_service.get_setup_session(user_id)
    if not session:
        return False

    step = profile_service.current_step(session)
    text = (update.message.text or "").strip()
    if not text:
        return True

    if step == STEP_PROFESSION:
        if len(text) > 120:
            await update.message.reply_text(
                t("PREMIUM_SETUP_PROFESSION_TOO_LONG", user_id=user_id)
            )
            return True
        next_step = profile_service.save_answer(user_id, session, "profession", text)
        session = profile_service.get_setup_session(user_id)
        await update.message.reply_text(
            t("PREMIUM_SETUP_SAVED_PROFESSION", user_id=user_id, value=text)
        )
        if next_step:
            await _send_step(update.message, user_id, next_step)
        else:
            await _finish_setup(update.message, user_id, session)
        return True

    if step == STEP_EXAM_DATE:
        if len(text) > 80:
            await update.message.reply_text(
                t("PREMIUM_SETUP_EXAM_DATE_TOO_LONG", user_id=user_id)
            )
            return True
        next_step = profile_service.save_answer(user_id, session, "exam_date", text)
        session = profile_service.get_setup_session(user_id)
        await update.message.reply_text(
            t("PREMIUM_SETUP_SAVED_EXAM_DATE", user_id=user_id, value=text)
        )
        if next_step:
            await _send_step(update.message, user_id, next_step)
        else:
            await _finish_setup(update.message, user_id, session)
        return True

    await update.message.reply_text(t("PREMIUM_SETUP_USE_BUTTONS", user_id=user_id))
    return True


async def _finish_setup(message, user_id: int, session: dict):
    from bot.handlers.diagnostic import diagnostic_keyboard, needs_diagnostic
    from bot.handlers.premium_lesson import premium_lesson_keyboard

    profile = profile_service.complete_setup(user_id, session)
    goal_label = td("BTN_GOALS", user_id=user_id).get(
        profile.get("goal") or "", profile.get("goal") or "—"
    )
    minutes = profile.get("daily_minutes") or "—"
    if needs_diagnostic(user_id):
        await message.reply_text(
            t("DIAG_AFTER_SETUP", user_id=user_id),
            reply_markup=diagnostic_keyboard(user_id),
        )
        return

    markup = premium_lesson_keyboard(user_id)
    await message.reply_text(
        t("PREMIUM_SETUP_DONE", user_id=user_id, goal=goal_label, minutes=minutes),
    )
    if markup:
        await message.reply_text(
            t("DIAG_AFTER_SETUP_LESSON", user_id=user_id),
            reply_markup=markup,
        )
    log_event(user_id, "premium_setup_complete_ui")


def premium_setup_keyboard(user_id: int | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("BTN_PREMIUM_SETUP", user_id=user_id),
                    callback_data="premsetup:start",
                )
            ]
        ]
    )
