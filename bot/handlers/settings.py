"""Настройки профиля — без повторного онбординга."""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import get_user, update_user, log_event
from bot import texts
from bot import keyboards
from bot.handlers import commands
from bot.handlers.dialog import start_language
from bot.services.reminders import CUSTOM_TIME_KEY, prompt_custom_reminder_time

logger = logging.getLogger(__name__)


async def _require_onboarding(update: Update) -> bool:
    user = get_user(update.effective_user.id)
    if not user or not user["onboarding_done"]:
        await update.message.reply_text("Сначала пройди онбординг: /start")
        return False
    return True


def _settings_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(texts.BTN_SETTINGS_LANG, callback_data="settings:lang")],
            [InlineKeyboardButton(texts.BTN_SETTINGS_LEVEL, callback_data="settings:level")],
            [InlineKeyboardButton(texts.BTN_SETTINGS_GOAL, callback_data="settings:goal")],
            [
                InlineKeyboardButton(
                    texts.BTN_SETTINGS_TIMEZONE, callback_data="settings:timezone"
                )
            ],
            [
                InlineKeyboardButton(
                    texts.BTN_SETTINGS_REMINDERS, callback_data="settings:reminders"
                )
            ],
            [
                InlineKeyboardButton(
                    texts.BTN_SETTINGS_CHALLENGE, callback_data="settings:challenge"
                )
            ],
        ]
    )


def _buttons_from_dict(options: dict, prefix: str):
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"{prefix}:{code}")]
        for code, label in options.items()
    ]
    keyboard.append(
        [InlineKeyboardButton(texts.BTN_SETTINGS_BACK, callback_data="settings:menu")]
    )
    return InlineKeyboardMarkup(keyboard)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /settings — меню настроек."""
    if update.message and not await _require_onboarding(update):
        return

    user_id = update.effective_user.id
    log_event(user_id, "settings_open")

    await update.message.reply_text(
        texts.SETTINGS_MENU,
        reply_markup=keyboards.main_keyboard(),
    )
    await update.message.reply_text(
        "Выбери:",
        reply_markup=_settings_keyboard(),
    )


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    if not user or not user["onboarding_done"]:
        await query.edit_message_text("Сначала пройди онбординг: /start")
        return

    action = query.data.split(":", 1)[1]

    if action == "menu":
        await query.edit_message_text(
            texts.SETTINGS_MENU, reply_markup=_settings_keyboard()
        )
        return

    if action == "lang":

        class _Wrap:
            message = query.message

        await start_language(_Wrap(), context, user_id)
        return

    if action == "level":
        await query.edit_message_text(
            texts.ASK_LEVEL,
            reply_markup=_buttons_from_dict(texts.BTN_LEVELS, "setlevel"),
        )
        return

    if action == "goal":
        await query.edit_message_text(
            texts.ASK_GOAL,
            reply_markup=_buttons_from_dict(texts.BTN_GOALS, "setgoal"),
        )
        return

    if action == "timezone":
        await query.edit_message_text(
            texts.ASK_TIMEZONE,
            reply_markup=_buttons_from_dict(texts.BTN_TIMEZONES, "settimezone"),
        )
        return

    if action == "reminders":

        class _Wrap:
            message = query.message

        await commands.reminders_command(_Wrap(), context)
        return

    if action == "challenge":
        from bot.services.challenge import challenge_goal_keyboard

        await query.edit_message_text(
            texts.ASK_CHALLENGE,
            reply_markup=challenge_goal_keyboard(),
        )


async def handle_profile_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение уровня, цели, timezone из настроек."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    step, value = query.data.split(":", 1)

    labels = {
        "setlevel": texts.BTN_LEVELS,
        "setgoal": texts.BTN_GOALS,
        "settimezone": texts.BTN_TIMEZONES,
        "settime": texts.BTN_TIMES,
    }
    field_map = {
        "setlevel": "level",
        "setgoal": "goal",
        "settimezone": "timezone",
        "settime": "reminder_time",
    }

    if step not in labels:
        return

    if step == "settime" and value == CUSTOM_TIME_KEY:
        await prompt_custom_reminder_time(query.message, user_id)
        return

    if value not in labels[step]:
        return

    fields = {field_map[step]: value}
    if step == "settime":
        fields["reminder_enabled"] = 1
    update_user(user_id, **fields)
    log_event(user_id, f"settings_{field_map[step]}")

    label = labels[step][value]
    await query.edit_message_text(
        texts.SETTINGS_SAVED.format(setting=label)
        + "\n\n/settings — изменить ещё что-то"
    )
