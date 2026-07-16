import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import get_user, update_user, log_event
from bot import texts, keyboards
from bot.i18n import t, td
from bot.services.reminders import (
    CUSTOM_TIME_KEY,
    prompt_custom_reminder_time,
    reminder_time_keyboard,
    reminder_time_label,
)
from bot.services.analytics import get_admin_stats, format_admin_stats
from bot.services.premium_gate import sales_enabled
from config import ADMIN_USER_ID, DAILY_COST_LIMIT_USD

logger = logging.getLogger(__name__)


class _MessageUpdate:
    """Обёртка для вызова command-handler из callback-кнопки."""

    def __init__(self, message, user):
        self.message = message
        self.effective_user = user


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать inline-меню команд."""
    user_id = update.effective_user.id
    await keyboards.reply_main_menu(update.message, user_id)


async def refresh_user_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновить нижнюю клавиатуру (/keyboard)."""
    user_id = update.effective_user.id
    await update.message.reply_text(
        t("KEYBOARD_UPDATED", user_id=user_id),
        reply_markup=keyboards.main_keyboard(user_id),
    )


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок главного меню."""
    query = update.callback_query
    await query.answer()
    action = query.data.split(":", 1)[1]
    menu_items = td("MAIN_MENU_ITEMS", user_id=query.from_user.id)
    if action not in menu_items:
        return

    from database.db import set_activity
    from bot.handlers.settings import settings_command
    from bot.handlers.premium import premium_command
    from bot.handlers.feedback import feedback_command

    user_id = query.from_user.id
    set_activity(user_id, None)
    log_event(user_id, f"mainmenu_{action}")

    wrap = _MessageUpdate(query.message, query.from_user)

    if action == "settings":
        await settings_command(wrap, context)
    elif action == "reminders":
        await reminders_command(wrap, context)
    elif action == "progress":
        await progress_command(wrap, context)
    elif action == "premium":
        await premium_command(wrap, context)
    elif action == "feedback":
        await feedback_command(wrap, context)
    elif action == "help":
        await help_command(wrap, context)


# ---------- /help ----------


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    log_event(user_id, "help")
    key = "HELP_SALES" if sales_enabled() else "HELP"
    await update.message.reply_text(
        t(key, user_id=user_id),
        reply_markup=keyboards.main_keyboard(user_id),
    )


# ---------- /progress ----------


async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать прогресс и вызов пользователя."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user["onboarding_done"]:
        await update.message.reply_text(t("ONBOARDING_REQUIRED", user_id=user_id))
        return

    from bot.handlers.challenge import maybe_send_challenge_completion
    from bot.services.challenge import challenge_goal_keyboard
    from bot.services.progress import format_progress_text

    if await maybe_send_challenge_completion(update, user_id):
        user = get_user(user_id)

    log_event(user_id, "progress_view")
    await update.message.reply_text(
        format_progress_text(user_id),
        reply_markup=keyboards.main_keyboard(user_id),
    )

    user = get_user(user_id)
    if not user.get("challenge_days") or not user.get("challenge_start"):
        await update.message.reply_text(
            t("ASK_CHALLENGE", user_id=user_id),
            reply_markup=challenge_goal_keyboard(user_id),
        )


# ---------- /stats (admin) ----------


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сводка метрик — только для ADMIN_USER_ID."""
    user_id = update.effective_user.id
    if not ADMIN_USER_ID or user_id != ADMIN_USER_ID:
        await update.message.reply_text("Команда недоступна.")
        return

    stats = get_admin_stats()
    log_event(user_id, "admin_stats")
    await update.message.reply_text(
        format_admin_stats(stats, DAILY_COST_LIMIT_USD)
    )


# ---------- /style ----------


async def style_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать кнопки выбора стиля. Переиспользуем словарь стилей из онбординга."""
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"setstyle:{code}")]
        for code, label in texts.BTN_STYLES.items()
    ]
    await update.message.reply_text(
        texts.ASK_STYLE,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_style_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки смены стиля (вне онбординга)."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    _, style = query.data.split(":", 1)
    update_user(user_id, style=style)
    log_event(user_id, "style_changed")

    await query.edit_message_text(
        f"Готово! Теперь я объясняю в стиле «{texts.BTN_STYLES[style]}»."
    )


# ---------- /reminders ----------


async def reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущие настройки напоминаний + кнопки управления."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user:
        await update.message.reply_text(t("ONBOARDING_REQUIRED", user_id=user_id))
        return

    enabled = user["reminder_enabled"]
    time = user["reminder_time"]
    time_label = reminder_time_label(time) if time in texts.BTN_TIMES else time
    status = f"включены на {time_label}" if enabled else "выключены"

    keyboard = []
    if enabled:
        keyboard.append(
            [InlineKeyboardButton("Выключить напоминания", callback_data="rem:off")]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton("Включить напоминания", callback_data="rem:on")]
        )
    keyboard.extend(reminder_time_keyboard("remtime").inline_keyboard)

    await update.message.reply_text(
        f"Напоминания сейчас {status}.\n\nМожешь изменить время или выключить:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_reminders_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок управления напоминаниями."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    action, value = query.data.split(":", 1)

    if action == "rem":
        if value == "on":
            update_user(user_id, reminder_enabled=1)
            await query.edit_message_text("Напоминания включены.")
        else:
            update_user(user_id, reminder_enabled=0)
            await query.edit_message_text("Напоминания выключены.")
    elif action == "remtime":
        if value == CUSTOM_TIME_KEY:
            await prompt_custom_reminder_time(query.message, user_id)
            return
        update_user(user_id, reminder_time=value, reminder_enabled=1)
        await query.edit_message_text(
            texts.REMINDER_TIME_SAVED.format(time=reminder_time_label(value))
        )
