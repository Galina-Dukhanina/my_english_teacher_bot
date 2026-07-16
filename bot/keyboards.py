# Постоянная клавиатура с кнопками-инструментами.
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from bot.i18n import t, td


def main_keyboard(user_id: int | None = None):
    """Постоянная клавиатура снизу: активности, инструменты, главное меню."""
    keyboard = [
        [
            t("BTN_MENU", user_id=user_id),
            t("BTN_PRONOUNCE", user_id=user_id),
            t("BTN_MEANING", user_id=user_id),
        ],
        [
            t("BTN_LANG", user_id=user_id),
            t("BTN_MAIN", user_id=user_id),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


def main_menu_keyboard(user_id: int | None = None):
    """Inline-меню команд (настройки, прогресс, help и т.д.)."""
    items = td("MAIN_MENU_ITEMS", user_id=user_id)
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"mainmenu:{code}")]
        for code, label in items.items()
    ]
    return InlineKeyboardMarkup(keyboard)


async def reply_main_menu(message, user_id: int | None = None):
    """Главное меню: обновить клавиатуру + inline-команды."""
    await message.reply_text(
        t("MAIN_MENU", user_id=user_id),
        reply_markup=main_keyboard(user_id),
    )
    await message.reply_text("👇", reply_markup=main_menu_keyboard(user_id))


def premium_upsell_keyboard(user_id: int | None = None):
    """Inline-кнопка перехода к /premium."""
    from bot.services.premium_gate import sales_enabled

    if sales_enabled():
        label = t("PREMIUM_UPSELL_BTN_SALES", user_id=user_id)
    else:
        label = t("PREMIUM_UPSELL_BTN", user_id=user_id)
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data="prem:info")]]
    )
