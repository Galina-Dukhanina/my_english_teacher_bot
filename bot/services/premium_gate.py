"""Единая проверка доступа к Premium и upsell-сообщения."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from config import (
    PAYMENT_PROVIDER,
    PREMIUM_SALES_ENABLED,
    YOOKASSA_SECRET_KEY,
    YOOKASSA_SHOP_ID,
)
from bot.services.profile_service import profile_service
from bot.services.subscription import is_premium


class PremiumFeature(StrEnum):
    PROGRAM = "program"
    SAVE_WORD = "save_word"
    ADDWORD = "addword"
    UNLIMITED = "unlimited"


class PremiumDenyReason(StrEnum):
    OK = "ok"
    NOT_PREMIUM = "not_premium"
    SETUP_REQUIRED = "setup_required"
    SALES_DISABLED = "sales_disabled"


@dataclass(frozen=True)
class PremiumAccess:
    allowed: bool
    reason: str = PremiumDenyReason.OK


def sales_enabled() -> bool:
    return PREMIUM_SALES_ENABLED


def check_subscription(user_id: int) -> PremiumAccess:
    if not is_premium(user_id):
        return PremiumAccess(False, PremiumDenyReason.NOT_PREMIUM)
    return PremiumAccess(True)


def check_program(user_id: int) -> PremiumAccess:
    access = check_subscription(user_id)
    if not access.allowed:
        return access
    if profile_service.needs_premium_setup(user_id):
        return PremiumAccess(False, PremiumDenyReason.SETUP_REQUIRED)
    return PremiumAccess(True)


def check_feature(user_id: int, feature: PremiumFeature) -> PremiumAccess:
    if feature == PremiumFeature.PROGRAM:
        return check_program(user_id)
    if feature in {
        PremiumFeature.SAVE_WORD,
        PremiumFeature.ADDWORD,
        PremiumFeature.UNLIMITED,
    }:
        return check_subscription(user_id)
    return PremiumAccess(True)


def upsell_text(reason: str, *, feature: PremiumFeature | None = None) -> str:
    from bot import texts

    del feature
    if reason == PremiumDenyReason.SETUP_REQUIRED:
        return texts.PREMIUM_SETUP_REQUIRED_SHORT
    if reason == PremiumDenyReason.SALES_DISABLED:
        return texts.PREMIUM_COMING_SOON
    if sales_enabled():
        return texts.PREMIUM_UPSELL_SALES
    return texts.PREMIUM_UPSELL


def feature_denied_text(feature: PremiumFeature) -> str:
    from bot import texts

    mapping = {
        PremiumFeature.SAVE_WORD: texts.PREMIUM_WORD_HINT,
        PremiumFeature.ADDWORD: texts.ADDWORD_PREMIUM_ONLY,
        PremiumFeature.PROGRAM: texts.PREMIUM_PROGRAM_ONLY,
    }
    if sales_enabled():
        sales_mapping = {
            PremiumFeature.SAVE_WORD: texts.PREMIUM_WORD_HINT_SALES,
            PremiumFeature.ADDWORD: texts.ADDWORD_PREMIUM_ONLY_SALES,
            PremiumFeature.PROGRAM: texts.PREMIUM_PROGRAM_ONLY_SALES,
        }
        return sales_mapping.get(feature, upsell_text(PremiumDenyReason.NOT_PREMIUM))
    return mapping.get(feature, upsell_text(PremiumDenyReason.NOT_PREMIUM))


def premium_help_line() -> str:
    from bot import texts

    if sales_enabled():
        return texts.PREMIUM_HELP_LINE_SALES
    return texts.PREMIUM_HELP_LINE_DEV


def validate_sales_configuration() -> list[str]:
    """Предупреждения при старте бота."""
    warnings: list[str] = []
    if not sales_enabled():
        return warnings
    if PAYMENT_PROVIDER == "yookassa":
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            warnings.append(
                "PREMIUM_SALES_ENABLED=true, но YooKassa credentials не заданы"
            )
    elif PAYMENT_PROVIDER == "manual":
        warnings.append(
            "PREMIUM_SALES_ENABLED=true с PAYMENT_PROVIDER=manual — "
            "только для dev, не для prod"
        )
    else:
        warnings.append(f"Неизвестный PAYMENT_PROVIDER: {PAYMENT_PROVIDER}")
    return warnings
