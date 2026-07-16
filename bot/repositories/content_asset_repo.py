"""Медиа-контент (аудио для listening — этап 13)."""

import json

from database.db import get_connection


class ContentAssetRepository:
    def get_by_slug(self, slug: str) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM content_assets WHERE slug = ?",
            (slug,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def upsert(
        self,
        slug: str,
        kind: str,
        *,
        path: str | None = None,
        telegram_file_id: str | None = None,
        meta: dict | None = None,
    ) -> int:
        meta_json = json.dumps(meta or {}, ensure_ascii=False)
        conn = get_connection()
        existing = conn.execute(
            "SELECT id FROM content_assets WHERE slug = ?",
            (slug,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE content_assets
                SET kind = ?, path = ?, telegram_file_id = ?, meta_json = ?
                WHERE slug = ?
                """,
                (kind, path, telegram_file_id, meta_json, slug),
            )
            asset_id = existing["id"]
        else:
            cur = conn.execute(
                """
                INSERT INTO content_assets (slug, kind, path, telegram_file_id, meta_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (slug, kind, path, telegram_file_id, meta_json),
            )
            asset_id = cur.lastrowid
        conn.commit()
        conn.close()
        return asset_id
