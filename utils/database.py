import asyncpg
from utils.logger import logger
from vars import Var


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    is_authorized BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS banned (
    user_id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    data JSONB NOT NULL DEFAULT '{}'
);
"""


class Database:
    def __init__(self):
        self._pool = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(
            Var.DATABASE_URL,
            min_size=2,
            max_size=10,
            statement_cache_size=0,
        )
        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_TABLES_SQL)
        logger.info("PostgreSQL connected and tables ready")

    async def add_user(self, user_id: int):
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    user_id
                )
        except Exception as e:
            logger.error(f"add_user error: {e}")

    async def is_user_exist(self, user_id: int) -> bool:
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT 1 FROM users WHERE user_id=$1", user_id
                )
            return bool(row)
        except Exception:
            return False

    async def get_all_users(self):
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("SELECT user_id FROM users")
            return rows
        except Exception:
            return []

    async def total_users_count(self) -> int:
        try:
            async with self._pool.acquire() as conn:
                val = await conn.fetchval("SELECT COUNT(*) FROM users")
            return val or 0
        except Exception:
            return 0

    async def delete_user(self, user_id: int):
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM users WHERE user_id=$1", user_id
                )
        except Exception as e:
            logger.error(f"delete_user error: {e}")

    async def ban_user(self, user_id: int):
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO banned (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
                    user_id
                )
        except Exception as e:
            logger.error(f"ban_user error: {e}")

    async def unban_user(self, user_id: int):
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM banned WHERE user_id=$1", user_id
                )
        except Exception as e:
            logger.error(f"unban_user error: {e}")

    async def is_banned(self, user_id: int) -> bool:
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT 1 FROM banned WHERE user_id=$1", user_id
                )
            return bool(row)
        except Exception:
            return False

    async def authorize_user(self, user_id: int):
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO users (user_id, is_authorized) VALUES ($1, TRUE)
                       ON CONFLICT (user_id) DO UPDATE SET is_authorized=TRUE""",
                    user_id
                )
        except Exception as e:
            logger.error(f"authorize_user error: {e}")

    async def is_authorized(self, user_id: int) -> bool:
        try:
            async with self._pool.acquire() as conn:
                val = await conn.fetchval(
                    "SELECT is_authorized FROM users WHERE user_id=$1", user_id
                )
            return bool(val)
        except Exception:
            return False

    async def set_pushinfo(self, info: dict):
        import json
        try:
            json_str = json.dumps(info)
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO settings (key, data)
                       VALUES ('pushinfo', $1::jsonb)
                       ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data""",
                    json_str
                )
        except Exception as e:
            logger.error(f"set_pushinfo error: {e}")

    async def get_pushinfo(self) -> dict:
        import json
        try:
            async with self._pool.acquire() as conn:
                val = await conn.fetchval(
                    "SELECT data FROM settings WHERE key='pushinfo'"
                )
            if val is None:
                return {}
            if isinstance(val, str):
                return json.loads(val)
            if isinstance(val, dict):
                return val
            return {}
        except Exception:
            return {}

    async def close(self):
        if self._pool:
            await self._pool.close()


db = Database()
