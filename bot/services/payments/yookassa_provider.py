"""ЮKassa — создание платежа и обработка webhook."""

import logging
import uuid

from config import (
    YOOKASSA_SHOP_ID,
    YOOKASSA_SECRET_KEY,
    PAYMENT_RETURN_URL,
    PREMIUM_DAYS_MONTH,
    PREMIUM_DAYS_YEAR,
)
from bot.services.payments import PaymentRequest, PaymentResponse
from bot.services.subscription import complete_payment
from database.db import create_payment_record

logger = logging.getLogger(__name__)

_PLAN_DAYS = {"month": PREMIUM_DAYS_MONTH, "year": PREMIUM_DAYS_YEAR}


class YooKassaProvider:
    name = "yookassa"

    def __init__(self):
        if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
            raise ValueError("YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY обязательны")

    def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        from yookassa import Configuration, Payment

        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY

        idempotence_key = str(uuid.uuid4())
        payment = Payment.create(
            {
                "amount": {
                    "value": f"{request.amount:.2f}",
                    "currency": "RUB",
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": PAYMENT_RETURN_URL,
                },
                "capture": True,
                "description": request.description,
                "metadata": {
                    "user_id": str(request.user_id),
                    "plan": request.plan,
                },
            },
            idempotence_key,
        )

        create_payment_record(
            request.user_id,
            self.name,
            payment.id,
            request.plan,
            request.amount,
        )

        url = payment.confirmation.confirmation_url if payment.confirmation else None
        return PaymentResponse(
            provider_payment_id=payment.id,
            payment_url=url,
        )


def process_yookassa_notification(body: dict) -> bool:
    """Обработать webhook от ЮKassa. True если premium активирован."""
    from yookassa.domain.notification import WebhookNotificationFactory

    try:
        notification = WebhookNotificationFactory().create(body)
        payment_obj = notification.object
        if payment_obj.status != "succeeded":
            return False

        metadata = payment_obj.metadata or {}
        user_id = int(metadata.get("user_id", 0))
        plan = metadata.get("plan", "month")
        if not user_id:
            record = None
            from database.db import get_payment_by_provider_id

            record = get_payment_by_provider_id(payment_obj.id)
            if record:
                user_id = record["user_id"]
                plan = record.get("plan") or plan

        if not user_id:
            logger.error(f"YooKassa webhook: user_id не найден для {payment_obj.id}")
            return False

        days = _PLAN_DAYS.get(plan, PREMIUM_DAYS_MONTH)
        complete_payment(payment_obj.id, user_id, plan, days)
        return True
    except Exception as e:
        logger.exception(f"Ошибка обработки YooKassa webhook: {e}")
        return False
