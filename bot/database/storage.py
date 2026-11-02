
from pathlib import Path

import aiosqlite


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "superquest.db"


async def init_db():
    """Создание таблиц при запуске бота."""

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_games (
                user_id INTEGER NOT NULL,
                game_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, game_id)
            )
        """)

        await db.commit()


async def get_user_games(user_id: int) -> set[str]:
    """Получить выбранные игры пользователя."""

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT game_id
            FROM user_games
            WHERE user_id = ?
            """,
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()

    return {row[0] for row in rows}


async def toggle_user_game(
    user_id: int,
    game_id: str
) -> bool:
    """
    Добавить или удалить игру.

    Возвращает True, если игра выбрана.
    Возвращает False, если игра удалена.
    """

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT 1
            FROM user_games
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
