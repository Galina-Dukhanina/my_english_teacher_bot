"""Premium setup — пошаговая настройка программы обучения."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot import texts
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


async def _send_step(message, step: str):
    if step == STEP_PROFESSION:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(texts.BTN_PREMIUM_SKIP, callback_data="premsetup:skip")]]
        )
        await message.reply_text(texts.PREMIUM_SETUP_PROFESSION, reply_markup=keyboard)
        return

    if step == STEP_DAILY_MINUTES:
        await message.reply_text(
            texts.PREMIUM_SETUP_MINUTES,
            reply_markup=_buttons(texts.BTN_PREMIUM_MINUTES, "premsetup:min"),
        )
        return

    if step == STEP_EXAM_TYPE:
        await message.reply_text(
            texts.PREMIUM_SETUP_EXAM_TYPE,
            reply_markup=_buttons(texts.BTN_EXAM_TYPES, "premsetup:exam"),
        )
        return

    if step == STEP_EXAM_DATE:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(texts.BTN_PREMIUM_SKIP, callback_data="premsetup:skipdate")]]
        )
        await message.reply_text(texts.PREMIUM_SETUP_EXAM_DATE, reply_markup=keyboard)
        return

    if step == STEP_WEAK_SKILL:
        await message.reply_text(
            texts.PREMIUM_SETUP_WEAK_SKILL,
            reply_markup=_buttons(texts.BTN_WEAK_SKILLS, "premsetup:weak"),
        )
        return

    if step == STEP_INTERESTS:
        await message.reply_text(
            texts.PREMIUM_SETUP_INTERESTS,
            reply_markup=_buttons(texts.BTN_PREMIUM_INTERESTS, "premsetup:int"),
        )
        return


async def start_premium_setup(message, user_id: int) -> bool:
    if not is_premium(user_id):
        await message.reply_text(texts.PREMIUM_SETUP_NOT_PREMIUM)
        return False

    user = get_user(user_id)
    if not user or not user["onboarding_done"]:
        await message.reply_text("Сначала пройди онбординг: /start")
        return False

    if not profile_service.needs_premium_setup(user_id):
        await message.reply_text(texts.PREMIUM_SETUP_ALREADY)
        return False

    step = profile_service.start_setup(user_id)
    await message.reply_text(texts.PREMIUM_SETUP_INTRO)
    await _send_step(message, step)
    return True


async def handle_premium_setup_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not is_premium(user_id):
        await query.edit_message_text(texts.PREMIUM_SETUP_NOT_PREMIUM)
        return

    session = profile_service.get_setup_session(user_id)
    if not session:
        await query.edit_message_text(texts.PREMIUM_SETUP_EXPIRED)
        return

    step = profile_service.current_step(session)
    data = query.data.split(":", 2)

    if data[1] == "skip" and step == STEP_PROFESSION:
        await query.edit_message_text(
            f"{texts.PREMIUM_SETUP_PROFESSION}\n\n⏭ {texts.BTN_PREMIUM_SKIP}"
        )
        next_step = profile_service.save_answer(user_id, session, "profession", None)
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "skipdate" and step == STEP_EXAM_DATE:
        await query.edit_message_text(
            f"{texts.PREMIUM_SETUP_EXAM_DATE}\n\n⏭ {texts.BTN_PREMIUM_SKIP}"
        )
        next_step = profile_service.save_answer(user_id, session, "exam_date", None)
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "min" and step == STEP_DAILY_MINUTES:
        minutes = int(data[2])
        label = texts.BTN_PREMIUM_MINUTES.get(str(minutes), str(minutes))
        await query.edit_message_text(
            f"{texts.PREMIUM_SETUP_MINUTES}\n\n✅ {label}"
        )
        next_step = profile_service.save_answer(user_id, session, "daily_minutes", minutes)
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "exam" and step == STEP_EXAM_TYPE:
        exam_type = data[2]
        if exam_type not in texts.BTN_EXAM_TYPES:
            return
        await query.edit_message_text(
            f"{texts.PREMIUM_SETUP_EXAM_TYPE}\n\n✅ {texts.BTN_EXAM_TYPES[exam_type]}"
        )
        next_step = profile_service.save_answer(user_id, session, "exam_type", exam_type)
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "weak" and step == STEP_WEAK_SKILL:
        skill = data[2]
        if skill not in texts.BTN_WEAK_SKILLS:
            return
        await query.edit_message_text(
            f"{texts.PREMIUM_SETUP_WEAK_SKILL}\n\n✅ {texts.BTN_WEAK_SKILLS[skill]}"
        )
        next_step = profile_service.save_answer(user_id, session, "weak_skill", skill)
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "int" and step == STEP_INTERESTS:
        interest = data[2]
        if interest not in texts.BTN_PREMIUM_INTERESTS:
            return
        await query.edit_message_text(
            f"{texts.PREMIUM_SETUP_INTERESTS}\n\n✅ {texts.BTN_PREMIUM_INTERESTS[interest]}"
        )
        next_step = profile_service.save_answer(user_id, session, "interests", [interest])
        session = profile_service.get_setup_session(user_id)
        if next_step:
            await _send_step(query.message, next_step)
        else:
            await _finish_setup(query.message, user_id, session)
        return

    if data[1] == "start":
        if profile_service.get_setup_session(user_id):
            profile_service.cancel_setup(user_id)
        step = profile_service.start_setup(user_id)
        await query.edit_message_text(texts.PREMIUM_SETUP_INTRO)
        await _send_step(query.message, step)
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
            await update.message.reply_text(texts.PREMIUM_SETUP_PROFESSION_TOO_LONG)
            return True
        next_step = profile_service.save_answer(user_id, session, "profession", text)
        session = profile_service.get_setup_session(user_id)
        await update.message.reply_text(texts.PREMIUM_SETUP_SAVED_PROFESSION.format(value=text))
        if next_step:
            await _send_step(update.message, next_step)
        else:
            await _finish_setup(update.message, user_id, session)
        return True

    if step == STEP_EXAM_DATE:
        if len(text) > 80:
            await update.message.reply_text(texts.PREMIUM_SETUP_EXAM_DATE_TOO_LONG)
            return True
        next_step = profile_service.save_answer(user_id, session, "exam_date", text)
        session = profile_service.get_setup_session(user_id)
        await update.message.reply_text(texts.PREMIUM_SETUP_SAVED_EXAM_DATE.format(value=text))
        if next_step:
            await _send_step(update.message, next_step)
        else:
            await _finish_setup(update.message, user_id, session)
        return True

    await update.message.reply_text(texts.PREMIUM_SETUP_USE_BUTTONS)
    return True


async def _finish_setup(message, user_id: int, session: dict):
    profile = profile_service.complete_setup(user_id, session)
    goal_label = texts.BTN_GOALS.get(profile.get("goal") or "", profile.get("goal") or "—")
    minutes = profile.get("daily_minutes") or "—"
    await message.reply_text(
        texts.PREMIUM_SETUP_DONE.format(goal=goal_label, minutes=minutes)
    )
    log_event(user_id, "premium_setup_complete_ui")


def premium_setup_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    texts.BTN_PREMIUM_SETUP,
                    callback_data="premsetup:start",
                )
            ]
        ]
    )
