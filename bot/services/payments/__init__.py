"""Типы и фабрика платёжных провайдеров."""

from dataclasses import dataclass
from typing import Protocol

from config import PAYMENT_PROVIDER


@dataclass
class PaymentRequest:
    user_id: int
    plan: str
    amount: float
    description: str


@dataclass
class PaymentResponse:
    provider_payment_id: str
    payment_url: str | None
    message: str | None = None


class PaymentProvider(Protocol):
    name: str

    def create_payment(self, request: PaymentRequest) -> PaymentResponse:
        ...


def get_payment_provider() -> PaymentProvider:
    if PAYMENT_PROVIDER == "yookassa":
        from bot.services.payments.yookassa_provider import YooKassaProvider

        return YooKassaProvider()
    from bot.services.payments.manual_provider import ManualProvider

    return ManualProvider()
