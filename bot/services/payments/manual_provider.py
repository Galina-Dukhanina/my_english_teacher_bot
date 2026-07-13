"""Ручная оплата — для dev и тестирования UI premium."""

import uuid

from bot import texts
from bot.services.payments import PaymentRequest, PaymentResponse
from database.db import create_payment_record


class ManualProvider:
    name = "manual"

    def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        payment_id = f"manual_{uuid.uuid4().hex[:12]}"
        create_payment_record(
            request.user_id,
            self.name,
            payment_id,
            request.plan,
            request.amount,
        )
        return PaymentResponse(
            provider_payment_id=payment_id,
            payment_url=None,
            message=texts.PREMIUM_MANUAL_USER,
        )
