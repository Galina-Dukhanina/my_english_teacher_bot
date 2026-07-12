"""FastAPI webhook для ЮKassa."""

import json
import logging

from fastapi import FastAPI, Request, Response

from bot.services.payments.yookassa_provider import process_yookassa_notification

logger = logging.getLogger(__name__)

app = FastAPI(title="English Teacher Bot Webhooks")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    body_bytes = await request.body()
    try:
        body = json.loads(body_bytes)
    except json.JSONDecodeError:
        return Response(status_code=400)

    if process_yookassa_notification(body):
        logger.info("YooKassa payment processed")
    return Response(status_code=200)
