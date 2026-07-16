"""Команды /premium и admin /grant_premium."""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    ADMIN_USER_ID,
    PREMIUM_PRICE_MONTH,
    PREMIUM_PRICE_YEAR,
    PREMIUM_DAYS_MONTH,
    PREMIUM_DAYS_YEAR,
    PAYMENT_PROVIDER,
)
from bot.services.premium_gate import sales_enabled
from bot import texts, keyboards
from bot.services.subscription import is_premium, grant_premium
from bot.services.payments import PaymentRequest, get_payment_provider
from bot.services.profile_service import profile_service
from bot.handlers.premium_onboarding import premium_setup_keyboard
from bot.handlers.diagnostic import diagnostic_keyboard, needs_diagnostic
from bot.handlers.daily_phrase import premium_menu_keyboard
from database.db import get_user, log_event

logger = logging.getLogger(__name__)

_PLANS = {
    "month": (PREMIUM_PRICE_MONTH, PREMIUM_DAYS_MONTH, texts.PREMIUM_PLAN_MONTH),
    "year": (PREMIUM_PRICE_YEAR, PREMIUM_DAYS_YEAR, texts.PREMIUM_PLAN_YEAR),
}


def _premium_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    texts.PREMIUM_BTN_MONTH.format(price=int(PREMIUM_PRICE_MONTH)),
                    callback_data="prem:month",
                )
            ],
            [
                InlineKeyboardButton(
                    texts.PREMIUM_BTN_YEAR.format(price=int(PREMIUM_PRICE_YEAR)),
                    callback_data="prem:year",
                )
            ],
        ]
    )


async def _send_premium_ready(message, user_id: int, until: str):
    if needs_diagnostic(user_id):
        await message.reply_text(
            texts.PREMIUM_ACTIVE_NEED_DIAG.format(until=until),
            reply_markup=diagnostic_keyboard(),
        )
        return
    markup = premium_menu_keyboard(user_id)
    await message.reply_text(
        texts.PREMIUM_ACTIVE_READY.format(until=until),
        reply_markup=markup or keyboards.main_keyboard(),
    )


async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or not user["onboarding_done"]:
        await update.message.reply_text("Сначала пройди онбординг: /start")
        return

    log_event(user_id, "premium_view")
    if is_premium(user_id):
        until = user.get("premium_until") or "без срока"
        if profile_service.needs_premium_setup(user_id):
            await update.message.reply_text(
                texts.PREMIUM_ACTIVE_SETUP.format(until=until),
                reply_markup=premium_setup_keyboard(),
            )
        else:
            await _send_premium_ready(update.message, user_id, until)
        return

    if not sales_enabled():
        await update.message.reply_text(
            texts.PREMIUM_COMING_SOON,
            reply_markup=keyboards.main_keyboard(),
        )
        return

    await update.message.reply_text(
        texts.PREMIUM_INTRO,
        reply_markup=_premium_keyboard(),
    )


async def handle_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка prem:info, prem:month, prem:year."""
    query = update.callback_query
    _, action = query.data.split(":", 1)

    if action == "info":
        await query.answer()
        user = get_user(query.from_user.id)
        if user and is_premium(query.from_user.id):
            until = user.get("premium_until") or "без срока"
            if profile_service.needs_premium_setup(query.from_user.id):
                await query.edit_message_text(
                    texts.PREMIUM_ACTIVE_SETUP.format(until=until),
                    reply_markup=premium_setup_keyboard(),
                )
            else:
                if needs_diagnostic(query.from_user.id):
                    await query.edit_message_text(
                        texts.PREMIUM_ACTIVE_NEED_DIAG.format(until=until),
                        reply_markup=diagnostic_keyboard(),
                    )
                else:
                    markup = premium_menu_keyboard(query.from_user.id)
                    await query.edit_message_text(
                        texts.PREMIUM_ACTIVE_READY.format(until=until),
                        reply_markup=markup,
                    )
            return
        if not sales_enabled():
            await query.edit_message_text(texts.PREMIUM_COMING_SOON)
            return
        await query.edit_message_text(
            texts.PREMIUM_INTRO,
            reply_markup=_premium_keyboard(),
        )
        return

    if not sales_enabled():
        await query.answer()
        await query.edit_message_text(texts.PREMIUM_COMING_SOON)
        return

    await _handle_premium_plan(update, context)


async def _handle_premium_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    _, plan = query.data.split(":", 1)

    if plan not in _PLANS:
        return

    if is_premium(user_id):
        await query.edit_message_text(texts.PREMIUM_ALREADY)
        return

    amount, days, description = _PLANS[plan]
    provider = get_payment_provider()

    try:
        response = provider.create_payment(
            PaymentRequest(
                user_id=user_id,
                plan=plan,
                amount=amount,
                description=description,
            )
        )
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        await query.edit_message_text(texts.PREMIUM_PAY_ERROR)
        return

    log_event(user_id, f"premium_checkout_{plan}")

    if response.payment_url:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(texts.PREMIUM_BTN_PAY, url=response.payment_url)]]
        )
        await query.edit_message_text(
            texts.PREMIUM_PAY_LINK.format(amount=int(amount), plan=description),
            reply_markup=keyboard,
        )
    elif response.message:
        await query.edit_message_text(response.message)
        if PAYMENT_PROVIDER == "manual" and ADMIN_USER_ID and user_id != ADMIN_USER_ID:
            user = query.from_user
            name = user.first_name or "Пользователь"
            username = f"@{user.username}" if user.username else f"id:{user_id}"
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=(
                        f"💳 Заявка на Premium\n\n"
                        f"От: {name} ({username})\n"
                        f"Тариф: {description}\n\n"
                        f"/grant_premium {user_id}"
                    ),
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить admin о premium: {e}")
        elif PAYMENT_PROVIDER == "manual" and ADMIN_USER_ID and user_id == ADMIN_USER_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=(
                        f"💳 Заявка на Premium (твой аккаунт)\n"
                        f"/grant_premium {user_id}"
                    ),
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить admin о premium: {e}")
    else:
        await query.edit_message_text(texts.PREMIUM_PAY_ERROR)


async def grant_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /grant_premium USER_ID [DAYS]"""
    admin_id = update.effective_user.id
    if not ADMIN_USER_ID or admin_id != ADMIN_USER_ID:
        await update.message.reply_text("Команда недоступна.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Использование: /grant_premium USER_ID [DAYS]\n"
            f"По умолчанию {PREMIUM_DAYS_MONTH} дней."
        )
        return

    try:
        target_id = int(args[0])
        days = int(args[1]) if len(args) > 1 else PREMIUM_DAYS_MONTH
    except ValueError:
        await update.message.reply_text("USER_ID и DAYS должны быть числами.")
        return

    if not get_user(target_id):
        await update.message.reply_text("Пользователь не найден в базе.")
        return

    grant_premium(target_id, days, notify=False)
    log_event(admin_id, f"grant_premium_{target_id}")

    await update.message.reply_text(
        texts.PREMIUM_GRANTED.format(user_id=target_id, days=days)
    )
    if PAYMENT_PROVIDER == "manual":
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=texts.PREMIUM_ACTIVATED_USER.format(days=days),
                reply_markup=premium_setup_keyboard(),
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить user {target_id}: {e}")
