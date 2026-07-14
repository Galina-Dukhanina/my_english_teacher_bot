import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "bot_database.db"
uid = 348070164

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("=== user ===")
for r in c.execute(
    "SELECT user_id, timezone, challenge_days, challenge_start FROM users WHERE user_id=?",
    (uid,),
):
    print(dict(r))

print("\n=== challenge_active_days ===")
for r in c.execute(
    "SELECT active_date FROM challenge_active_days WHERE user_id=? ORDER BY active_date",
    (uid,),
):
    print(r["active_date"])

print("\n=== progress ===")
for r in c.execute("SELECT * FROM progress WHERE user_id=?", (uid,)):
    print(dict(r))

print("\n=== events by date ===")
for r in c.execute(
    """
    SELECT date(created_at) AS d, event_type, COUNT(*) AS n
    FROM events WHERE user_id=?
    GROUP BY date(created_at), event_type
    ORDER BY d DESC, event_type
    LIMIT 50
    """,
    (uid,),
):
    print(f"{r['d']}  {r['event_type']:25} {r['n']}")

c.close()
