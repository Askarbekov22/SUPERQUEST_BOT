
import time

import aiosqlite

from bot.database.storage import DB_PATH


async def ensure_contests_table():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS contests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                title TEXT NOT NULL,
                task TEXT NOT NULL,
                criteria TEXT NOT NULL,
                prize_som INTEGER NOT NULL,
                starts_at INTEGER NOT NULL,
                ends_at INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)
        await db.commit()


async def create_contest(
    data: dict,
    admin_id: int
) -> int:

    await ensure_contests_table()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO contests (
                game_id,
                title,
                task,
                criteria,
                prize_som,
                starts_at,
                ends_at,
                created_by,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["game_id"],
                data["title"],
                data["task"],
                data["criteria"],
                data["prize_som"],
                data["starts_at"],
                data["ends_at"],
                admin_id,
                int(time.time())
            )
        )

        await db.commit()
        return int(cursor.lastrowid)


async def get_contest(
    contest_id: int
) -> dict | None:

    await ensure_contests_table()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM contests WHERE id = ?",
            (contest_id,)
        ) as cursor:
            row = await cursor.fetchone()

    return dict(row) if row else None


async def list_contests(
    category: str = "active",
    limit: int = 20
) -> list[dict]:

    await ensure_contests_table()

    now = int(time.time())

    filters = {
        "active": (
            "starts_at <= ? AND ends_at > ?",
            (now, now)
        ),
        "upcoming": (
            "starts_at > ?",
            (now,)
        ),
        "finished": (
            "ends_at <= ?",
            (now,)
        ),
        "all": (
            "1 = 1",
            ()
        )
    }

    if category not in filters:
        return []

    condition, params = filters[category]

    ordering = (
        "id DESC"
        if category in ("all", "finished")
        else "starts_at ASC"
    )

    query = (
        f"SELECT * FROM contests "
        f"WHERE {condition} "
        f"ORDER BY {ordering} LIMIT ?"
    )

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            query,
            (*params, limit)
        ) as cursor:
            rows = await cursor.fetchall()

    return [dict(row) for row in rows]
