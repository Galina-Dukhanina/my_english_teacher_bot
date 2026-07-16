# Постоянная клавиатура с кнопками-инструментами.
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from bot import texts


def main_keyboard():
    """Постоянная клавиатура снизу: активности, инструменты, главное меню."""
    keyboard = [
        [texts.BTN_MENU, texts.BTN_PRONOUNCE, texts.BTN_MEANING],
        [texts.BTN_LANG, texts.BTN_MAIN],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


def main_menu_keyboard():
    """Inline-меню команд (настройки, прогресс, help и т.д.)."""
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"mainmenu:{code}")]
        for code, label in texts.MAIN_MENU_ITEMS.items()
    ]
    return InlineKeyboardMarkup(keyboard)


async def reply_main_menu(message):
    """Главное меню: обновить клавиатуру + inline-команды."""
    await message.reply_text(texts.MAIN_MENU, reply_markup=main_keyboard())
    await message.reply_text("👇", reply_markup=main_menu_keyboard())


def premium_upsell_keyboard():
    """Inline-кнопка перехода к /premium."""
    from bot.services.premium_gate import sales_enabled

    label = "⭐ Premium" if sales_enabled() else "⭐ Premium (скоро)"
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data="prem:info")]]
    )
