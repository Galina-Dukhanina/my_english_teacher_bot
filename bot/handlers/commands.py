import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.db import get_user, update_user, log_event
from bot import texts

logger = logging.getLogger(__name__)


# ---------- /help ----------


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_event(update.effective_user.id, "help")
    await update.message.reply_text(texts.HELP)


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
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("Сначала пройди онбординг: /start")
        return

    enabled = user["reminder_enabled"]
    time = user["reminder_time"]
    status = f"включены на {time}" if enabled else "выключены"

    keyboard = []
    if enabled:
        keyboard.append(
            [InlineKeyboardButton("Выключить напоминания", callback_data="rem:off")]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton("Включить напоминания", callback_data="rem:on")]
        )
    # Кнопки смены времени
    keyboard.append(
        [
            InlineKeyboardButton(label, callback_data=f"remtime:{value}")
            for value, label in texts.BTN_TIMES.items()
        ]
    )

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
        update_user(user_id, reminder_time=value, reminder_enabled=1)
        await query.edit_message_text(f"Готово! Буду напоминать в {value}.")
