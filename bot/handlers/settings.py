"""Настройки профиля — без повторного онбординга."""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import get_user, update_user, log_event
from bot import texts
from bot import keyboards
from bot.i18n import t, td, get_ui_language, set_ui_language, lang_label, SUPPORTED
from bot.handlers import commands
from bot.handlers.dialog import start_language
from bot.services.reminders import CUSTOM_TIME_KEY, prompt_custom_reminder_time

logger = logging.getLogger(__name__)


async def _require_onboarding(update: Update) -> bool:
    user = get_user(update.effective_user.id)
    if not user or not user["onboarding_done"]:
        await update.message.reply_text(
            t("ONBOARDING_REQUIRED", user_id=update.effective_user.id)
        )
        return False
    return True


def _settings_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("BTN_SETTINGS_UI_LANG", user_id=user_id),
                    callback_data="settings:uilang",
                )
            ],
            [
                InlineKeyboardButton(
                    t("BTN_SETTINGS_LANG", user_id=user_id),
                    callback_data="settings:lang",
                )
            ],
            [
                InlineKeyboardButton(
                    t("BTN_SETTINGS_LEVEL", user_id=user_id),
                    callback_data="settings:level",
                )
            ],
            [
                InlineKeyboardButton(
                    t("BTN_SETTINGS_GOAL", user_id=user_id),
                    callback_data="settings:goal",
                )
            ],
            [
                InlineKeyboardButton(
                    t("BTN_SETTINGS_TIMEZONE", user_id=user_id),
                    callback_data="settings:timezone",
                )
            ],
            [
                InlineKeyboardButton(
                    t("BTN_SETTINGS_REMINDERS", user_id=user_id),
                    callback_data="settings:reminders",
                )
            ],
            [
                InlineKeyboardButton(
                    t("BTN_SETTINGS_CHALLENGE", user_id=user_id),
                    callback_data="settings:challenge",
                )
            ],
        ]
    )


def _buttons_from_dict(options: dict, prefix: str, user_id: int):
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"{prefix}:{code}")]
        for code, label in options.items()
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                t("BTN_SETTINGS_BACK", user_id=user_id),
                callback_data="settings:menu",
            )
        ]
    )
    return InlineKeyboardMarkup(keyboard)


def _ui_lang_keyboard(user_id: int):
    current = get_ui_language(user_id)
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✓ ' if code == current else ''}{lang_label(code)}",
                callback_data=f"setuilang:{code}",
            )
        ]
        for code in SUPPORTED
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                t("BTN_SETTINGS_BACK", user_id=user_id),
                callback_data="settings:menu",
            )
        ]
    )
    return InlineKeyboardMarkup(keyboard)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /settings — меню настроек."""
    if update.message and not await _require_onboarding(update):
        return

    user_id = update.effective_user.id
    log_event(user_id, "settings_open")

    await update.message.reply_text(
        t("SETTINGS_MENU", user_id=user_id),
        reply_markup=keyboards.main_keyboard(user_id),
    )
    await update.message.reply_text(
        t("CHOOSE_OPTION", user_id=user_id),
        reply_markup=_settings_keyboard(user_id),
    )


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)
    if not user or not user["onboarding_done"]:
        await query.edit_message_text(t("ONBOARDING_REQUIRED", user_id=user_id))
        return

    action = query.data.split(":", 1)[1]

    if action == "menu":
        await query.edit_message_text(
            t("SETTINGS_MENU", user_id=user_id),
            reply_markup=_settings_keyboard(user_id),
        )
        return

    if action == "uilang":
        current = lang_label(get_ui_language(user_id))
        await query.edit_message_text(
            t("ASK_UI_LANG", user_id=user_id, current=current),
            reply_markup=_ui_lang_keyboard(user_id),
        )
        return

    if action == "lang":

        class _Wrap:
            message = query.message

        await start_language(_Wrap(), context, user_id)
        return

    if action == "level":
        await query.edit_message_text(
            t("ASK_LEVEL", user_id=user_id),
            reply_markup=_buttons_from_dict(
                td("BTN_LEVELS", user_id=user_id), "setlevel", user_id
            ),
        )
        return

    if action == "goal":
        await query.edit_message_text(
            t("ASK_GOAL", user_id=user_id),
            reply_markup=_buttons_from_dict(
                td("BTN_GOALS", user_id=user_id), "setgoal", user_id
            ),
        )
        return

    if action == "timezone":
        await query.edit_message_text(
            t("ASK_TIMEZONE", user_id=user_id),
            reply_markup=_buttons_from_dict(
                td("BTN_TIMEZONES", user_id=user_id), "settimezone", user_id
            ),
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
            t("ASK_CHALLENGE", user_id=user_id),
            reply_markup=challenge_goal_keyboard(user_id),
        )


async def handle_profile_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение уровня, цели, timezone, UI language из настроек."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    step, value = query.data.split(":", 1)

    if step == "setuilang":
        if value not in SUPPORTED:
            return
        set_ui_language(user_id, value)
        log_event(user_id, "settings_ui_language")
        label = lang_label(value)
        await query.edit_message_text(
            t("UI_LANG_CHANGED", user_id=user_id, lang=label)
            + t("SETTINGS_MORE", user_id=user_id)
        )
        await query.message.reply_text(
            t("KEYBOARD_UPDATED", user_id=user_id),
            reply_markup=keyboards.main_keyboard(user_id),
        )
        return

    labels = {
        "setlevel": td("BTN_LEVELS", user_id=user_id),
        "setgoal": td("BTN_GOALS", user_id=user_id),
        "settimezone": td("BTN_TIMEZONES", user_id=user_id),
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

    if step == "setlevel" and value == "unknown":
        levels = td("BTN_LEVELS", user_id=user_id)
        await query.edit_message_text(
            f"{t('ASK_LEVEL', user_id=user_id)}\n\n⏳ {levels['unknown']}"
        )
        from bot.handlers.level_test import start_level_test

        ok = await start_level_test(query, user_id, during_onboarding=False)
        if not ok:
            await query.message.reply_text(
                t("ASK_LEVEL", user_id=user_id),
                reply_markup=_buttons_from_dict(
                    td("BTN_LEVELS", user_id=user_id), "setlevel", user_id
                ),
            )
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
        t("SETTINGS_SAVED", user_id=user_id, setting=label)
        + t("SETTINGS_MORE", user_id=user_id)
    )
