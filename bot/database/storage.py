
from pathlib import Path
import time

import aiosqlite

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "superquest.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_games (
                user_id INTEGER NOT NULL,
                game_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, game_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS contests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                title TEXT NOT NULL,
                task TEXT NOT NULL,
                criteria TEXT NOT NULL,
                prize_som INTEGER NOT NULL CHECK (prize_som > 0),
                starts_at INTEGER NOT NULL,
                ends_at INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                CHECK (ends_at > starts_at)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contest_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                media_type TEXT NOT NULL
                    CHECK (media_type IN ('video', 'document')),
                file_id TEXT NOT NULL,
                file_unique_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (
                        status IN ('pending', 'approved', 'rejected')
                    ),
                accepted_terms_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                reviewed_at INTEGER,
                reviewed_by INTEGER,
                FOREIGN KEY (contest_id) REFERENCES contests(id),
                UNIQUE (contest_id, file_unique_id)
            )
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_submissions_user
            ON submissions (user_id, id DESC)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_submissions_status
            ON submissions (status, id DESC)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_contests_dates
            ON contests (starts_at, ends_at)
        """)

        await db.commit()


async def get_user_games(user_id: int) -> set[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT game_id FROM user_games WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()

    return {row[0] for row in rows}


async def toggle_user_game(
    user_id: int,
    game_id: str
) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT 1 FROM user_games
            WHERE user_id = ? AND game_id = ?
            """,
            (user_id, game_id)
        ) as cursor:
            exists = await cursor.fetchone()

        if exists:
            await db.execute(
                """
                DELETE FROM user_games
                WHERE user_id = ? AND game_id = ?
                """,
                (user_id, game_id)
            )
            selected = False
        else:
            await db.execute(
                """
                INSERT OR IGNORE INTO user_games
                (user_id, game_id)
                VALUES (?, ?)
                """,
                (user_id, game_id)
            )
            selected = True

        await db.commit()

    return selected


async def create_contest(
    data: dict,
    admin_id: int
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO contests (
                game_id, title, task, criteria, prize_som,
                starts_at, ends_at, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM contests WHERE id = ?",
            (contest_id,)
        ) as cursor:
            row = await cursor.fetchone()

    return dict(row) if row else None


async def list_contests(
    category: str,
    limit: int = 10
) -> list[dict]:
    now = int(time.time())

    conditions = {
        "active": (
            "starts_at <= ? AND ends_at > ?",
            (now, now)
        ),
        "upcoming": ("starts_at > ?", (now,)),
        "finished": ("ends_at <= ?", (now,)),
        "all": ("1=1", ())
    }

    if category not in conditions:
        return []

    where, params = conditions[category]

    order = (
        "id DESC"
        if category in {"finished", "all"}
        else "starts_at ASC"
    )

    query = (
        f"SELECT * FROM contests WHERE {where} "
        f"ORDER BY {order} LIMIT ?"
    )

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            query,
            (*params, limit)
        ) as cursor:
            rows = await cursor.fetchall()

    return [dict(row) for row in rows]


async def add_submission(
    contest_id: int,
    user_id: int,
    media_type: str,
    file_id: str,
    file_unique_id: str,
    accepted_terms_at: int
) -> tuple[str, int | None]:

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("BEGIN IMMEDIATE")

        async with db.execute(
            """
            SELECT starts_at, ends_at
            FROM contests WHERE id = ?
            """,
            (contest_id,)
        ) as cursor:
            times = await cursor.fetchone()

        if times is None:
            return "missing", None

        now = int(time.time())

        if not (times[0] <= now < times[1]):
            return "closed", None

        async with db.execute(
            """
            SELECT 1 FROM submissions
            WHERE contest_id = ? AND file_unique_id = ?
            """,
            (contest_id, file_unique_id)
        ) as cursor:
            if await cursor.fetchone():
                return "duplicate", None

        async with db.execute(
            """
            SELECT COUNT(*) FROM submissions
            WHERE contest_id = ? AND user_id = ?
            """,
            (contest_id, user_id)
        ) as cursor:
            count = (await cursor.fetchone())[0]

        if count >= 3:
            return "limit", None

        cursor = await db.execute(
            """
            INSERT INTO submissions (
                contest_id, user_id, media_type, file_id,
                file_unique_id, accepted_terms_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contest_id,
                user_id,
                media_type,
                file_id,
                file_unique_id,
                accepted_terms_at,
                now
            )
        )

        await db.commit()
        return "created", int(cursor.lastrowid)


async def get_submission(
    submission_id: int
) -> dict | None:

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT
                s.*,
                c.title AS contest_title,
                c.game_id
            FROM submissions s
            JOIN contests c ON c.id = s.contest_id
            WHERE s.id = ?
            """,
            (submission_id,)
        ) as cursor:
            row = await cursor.fetchone()

    return dict(row) if row else None


async def get_user_submissions(
    user_id: int,
    limit: int = 15
) -> list[dict]:

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT
                s.*,
                c.title AS contest_title,
                c.game_id
            FROM submissions s
            JOIN contests c ON c.id = s.contest_id
            WHERE s.user_id = ?
            ORDER BY s.id DESC
            LIMIT ?
            """,
            (user_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()

    return [dict(row) for row in rows]


async def get_pending_submissions(
    limit: int = 20
) -> list[dict]:

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT
                s.*,
                c.title AS contest_title,
                c.game_id
            FROM submissions s
            JOIN contests c ON c.id = s.contest_id
            WHERE s.status = 'pending'
            ORDER BY s.id ASC
            LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()

    return [dict(row) for row in rows]


async def review_submission(
    submission_id: int,
    status: str,
    admin_id: int
) -> bool:

    if status not in {"approved", "rejected"}:
        return False

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE submissions
            SET status = ?,
                reviewed_at = ?,
                reviewed_by = ?
            WHERE id = ? AND status = 'pending'
            """,
            (
                status,
                int(time.time()),
                admin_id,
                submission_id
            )
        )

        await db.commit()
        return cursor.rowcount == 1
