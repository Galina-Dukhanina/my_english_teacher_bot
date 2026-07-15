import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import get_user, create_user, update_user, log_event
from bot import texts
from bot.services.reminders import CUSTOM_TIME_KEY, prompt_custom_reminder_time

logger = logging.getLogger(__name__)


# ---------- Вспомогательные функции для кнопок ----------


def _buttons_from_dict(options: dict, prefix: str):
    """Собрать вертикальный столбец кнопок из словаря {код: подпись}.
    prefix нужен, чтобы потом понять, к какому шагу относится нажатие."""
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"{prefix}:{code}")]
        for code, label in options.items()
    ]
    return InlineKeyboardMarkup(keyboard)


# ---------- Точка входа: /start ----------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    user_id = tg_user.id
    create_user(user_id, tg_user.username, tg_user.first_name)
    log_event(user_id, "start")

    existing = get_user(user_id)
    if existing and existing["onboarding_done"]:
        from bot.handlers.challenge import maybe_send_challenge_completion
        from bot.keyboards import main_keyboard
        from bot.services.challenge import challenge_goal_keyboard
        from bot.services.progress import format_welcome_back

        if await maybe_send_challenge_completion(update, user_id):
            await update.message.reply_text(
                format_welcome_back(user_id),
                reply_markup=main_keyboard(),
            )
            return

        profile = get_user(user_id)
        await update.message.reply_text(
            format_welcome_back(user_id),
            reply_markup=main_keyboard(),
        )
        if not profile.get("challenge_days") or not profile.get("challenge_start"):
            await update.message.reply_text(
                texts.ASK_CHALLENGE,
                reply_markup=challenge_goal_keyboard(),
            )
        return

    # Первый визит — онбординг
    update_user(user_id, onboarding_step="terms")
    await update.message.reply_text(texts.WELCOME)

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(texts.BTN_ACCEPT, callback_data="terms:accept")]]
    )
    await update.message.reply_text(texts.TERMS, reply_markup=keyboard)


# ---------- Обработчик нажатий кнопок онбординга ----------


async def handle_onboarding_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # убирает "часики" на кнопке

    user_id = query.from_user.id
    data = query.data  # например "level:beginner"
    step, value = data.split(":", 1)

    # --- Согласие принято ---
    if step == "terms":
        from datetime import datetime

        update_user(
            user_id,
            terms_accepted=1,
            terms_accepted_at=datetime.now().isoformat(),
            onboarding_step="level",
        )
        await query.edit_message_text(texts.TERMS + "\n\n✅ Принято")
        await query.message.reply_text(
            texts.ASK_LEVEL,
            reply_markup=_buttons_from_dict(texts.BTN_LEVELS, "level"),
        )

    # --- Выбран уровень ---
    elif step == "level":
        if value == "unknown":
            await query.edit_message_text(
                f"{texts.ASK_LEVEL}\n\n⏳ {texts.BTN_LEVELS['unknown']}"
            )
            from bot.handlers.level_test import start_level_test

            ok = await start_level_test(query, user_id, during_onboarding=True)
            if not ok:
                await query.message.reply_text(
                    texts.ASK_LEVEL,
                    reply_markup=_buttons_from_dict(texts.BTN_LEVELS, "level"),
                )
            return
        update_user(user_id, level=value, onboarding_step="goal")
        await query.edit_message_text(
            f"{texts.ASK_LEVEL}\n\n✅ {texts.BTN_LEVELS[value]}"
        )
        await query.message.reply_text(
            texts.ASK_GOAL,
            reply_markup=_buttons_from_dict(texts.BTN_GOALS, "goal"),
        )

    # --- Выбрана цель ---
    elif step == "goal":
        update_user(user_id, goal=value, style="friendly", onboarding_step="timezone")
        await query.edit_message_text(
            f"{texts.ASK_GOAL}\n\n✅ {texts.BTN_GOALS[value]}"
        )
        await query.message.reply_text(
            texts.ASK_TIMEZONE,
            reply_markup=_buttons_from_dict(texts.BTN_TIMEZONES, "timezone"),
        )

    # --- Выбран часовой пояс ---
    elif step == "timezone":
        update_user(user_id, timezone=value, onboarding_step="time")
        await query.edit_message_text(
            f"{texts.ASK_TIMEZONE}\n\n✅ {texts.BTN_TIMEZONES[value]}"
        )
        await query.message.reply_text(
            texts.ASK_TIME,
            reply_markup=_buttons_from_dict(texts.BTN_TIMES, "time"),
        )

    # --- Выбрано время — шаг вызова ---
    elif step == "time":
        if value == CUSTOM_TIME_KEY:
            await query.edit_message_text(
                f"{texts.ASK_TIME}\n\n✅ {texts.BTN_TIMES[value]}"
            )
            await prompt_custom_reminder_time(query.message, user_id)
            return
        update_user(user_id, reminder_time=value, onboarding_step="streakgoal")
        await query.edit_message_text(
            f"{texts.ASK_TIME}\n\n✅ {texts.BTN_TIMES[value]}"
        )
        await query.message.reply_text(
            texts.ASK_CHALLENGE,
            reply_markup=_buttons_from_dict(texts.BTN_CHALLENGE_DAYS, "streakgoal"),
        )
