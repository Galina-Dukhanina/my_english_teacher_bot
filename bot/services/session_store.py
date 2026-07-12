"""Хранение активных сессий (карточки, упражнения) в SQLite."""

from database.db import get_session_payload, save_session_payload, delete_session

KIND_CARDS = "cards"
KIND_GRAMMAR = "grammar"


def get_session(user_id: int, kind: str) -> dict | None:
    return get_session_payload(user_id, kind)


def save_session(user_id: int, kind: str, data: dict):
    save_session_payload(user_id, kind, data)


def clear_session(user_id: int, kind: str):
    delete_session(user_id, kind)
