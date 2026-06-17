# Постоянная клавиатура с кнопками-инструментами.
from telegram import ReplyKeyboardMarkup
from bot import texts


def main_keyboard():
    """Постоянная клавиатура снизу: меню активностей + инструменты."""
    keyboard = [
        [texts.BTN_MENU],
        [texts.BTN_PRONOUNCE, texts.BTN_MEANING],
        [texts.BTN_LANG],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )
