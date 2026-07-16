"""Каталог модулей, уроков и шагов."""

import json

from database.db import get_connection


class CurriculumRepository:
    def get_module(self, module_id: int) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM curriculum_modules WHERE id = ? AND is_active = 1",
            (module_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def find_modules(
        self,
        *,
        goal: str,
        cefr_level: str,
        stage: int | None = None,
    ) -> list[dict]:
        conn = get_connection()
        query = """
            SELECT * FROM curriculum_modules
            WHERE goal = ? AND cefr_level = ? AND is_active = 1
        """
        params: list = [goal, cefr_level]
        if stage is not None:
            query += " AND stage = ?"
            params.append(stage)
        query += " ORDER BY sort_order, week_number, id"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_lesson(self, lesson_id: int) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM curriculum_lessons WHERE id = ? AND is_active = 1",
            (lesson_id,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def list_lessons(self, module_id: int) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT * FROM curriculum_lessons
            WHERE module_id = ? AND is_active = 1
            ORDER BY day_number, id
            """,
            (module_id,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def list_steps(self, lesson_id: int) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT * FROM lesson_steps
            WHERE lesson_id = ?
            ORDER BY sort_order, id
            """,
            (lesson_id,),
        ).fetchall()
        conn.close()
        steps = []
        for row in rows:
            step = dict(row)
            try:
                step["payload"] = json.loads(step.pop("payload_json"))
            except (TypeError, json.JSONDecodeError):
                step["payload"] = {}
            steps.append(step)
        return steps

    def insert_module(self, data: dict) -> int:
        conn = get_connection()
        cur = conn.execute(
            """
            INSERT INTO curriculum_modules (
                goal, cefr_level, stage, week_number, sort_order,
                title, outcome_ru, core_ratio, target_ratio, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["goal"],
                data["cefr_level"],
                data.get("stage", 1),
                data.get("week_number", 1),
                data.get("sort_order", 0),
                data["title"],
                data.get("outcome_ru"),
                data.get("core_ratio", 0.7),
                data.get("target_ratio", 0.3),
                data.get("is_active", 1),
            ),
        )
        module_id = cur.lastrowid
        conn.commit()
        conn.close()
        return module_id

    def insert_lesson(self, data: dict) -> int:
        conn = get_connection()
        cur = conn.execute(
            """
            INSERT INTO curriculum_lessons (
                module_id, day_number, title, estimated_minutes, is_active
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["module_id"],
                data["day_number"],
                data["title"],
                data.get("estimated_minutes", 15),
                data.get("is_active", 1),
            ),
        )
        lesson_id = cur.lastrowid
        conn.commit()
        conn.close()
        return lesson_id

    def insert_step(self, data: dict) -> int:
        conn = get_connection()
        payload = data.get("payload") or {}
        cur = conn.execute(
            """
            INSERT INTO lesson_steps (lesson_id, sort_order, step_type, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                data["lesson_id"],
                data["sort_order"],
                data["step_type"],
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        step_id = cur.lastrowid
        conn.commit()
        conn.close()
        return step_id
