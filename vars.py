import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv("config.env")


def _bool(val: str) -> bool:
    if not val:
        return False
    return val.strip().lower() in ("true", "1", "yes", "t", "y")


class Var:
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))
    BIN_CHANNEL: int = int(os.getenv("BIN_CHANNEL", "0"))

    DATABASE_URL: str = (
        os.getenv("DATABASE_URL") or
        os.getenv("POSTGRES_URL") or
        os.getenv("POSTGRESQL_URL") or
        os.getenv("DB_URL") or
        ""
    )

    _missing = []
    if not API_ID:
        _missing.append("API_ID")
    if not API_HASH:
        _missing.append("API_HASH")
    if not BOT_TOKEN:
        _missing.append("BOT_TOKEN")
    if not OWNER_ID:
        _missing.append("OWNER_ID")
    if not BIN_CHANNEL:
        _missing.append("BIN_CHANNEL")

    if _missing:
        raise ValueError(
            f"\n\n❌ MISSING REQUIRED ENV VARS: {', '.join(_missing)}\n"
            f"Set the following environment variables in Railway:\n"
            f"  API_ID      → from my.telegram.org\n"
            f"  API_HASH    → from my.telegram.org\n"
            f"  BOT_TOKEN   → from @BotFather on Telegram\n"
            f"  OWNER_ID    → send any message to @userinfobot\n"
            f"  BIN_CHANNEL → private channel ID, add bot as admin\n"
        )

    if not DATABASE_URL:
        raise ValueError(
            "\n\n❌ MISSING: DATABASE_URL\n"
            "Go to https://neon.tech → create free project → copy connection string\n"
            "Add it to Railway Variables as DATABASE_URL\n"
            "Format: postgresql://user:pass@host/dbname?sslmode=require\n"
        )

    FQDN: str = os.getenv("FQDN", "localhost")
    HAS_SSL: bool = _bool(os.getenv("HAS_SSL", "True"))
    NO_PORT: bool = _bool(os.getenv("NO_PORT", "True"))
    PORT: int = int(os.getenv("PORT", "8080"))

    _protocol: str = "https" if _bool(os.getenv("HAS_SSL", "True")) else "http"
    _port_seg: str = "" if _bool(os.getenv("NO_PORT", "True")) else f":{int(os.getenv('PORT', '8080'))}"
    URL: str = f"{_protocol}://{os.getenv('FQDN', 'localhost')}{_port_seg}/"

    WORKERS: int = int(os.getenv("WORKERS", "8"))
    SLEEP_THRESHOLD: int = int(os.getenv("SLEEP_THRESHOLD", "600"))
    PING_INTERVAL: int = int(os.getenv("PING_INTERVAL", "840"))

    # Force subscription channel — hardcoded to PrimeAutoBotz
    FORCE_CHANNEL_ID: int = -1003792781847

    MAX_BATCH_FILES: int = int(os.getenv("MAX_BATCH_FILES", "50"))
    RATE_LIMIT_ENABLED: bool = _bool(os.getenv("RATE_LIMIT_ENABLED", "False"))
    MAX_FILES_PER_PERIOD: int = int(os.getenv("MAX_FILES_PER_PERIOD", "5"))
    RATE_LIMIT_PERIOD_MINUTES: int = int(os.getenv("RATE_LIMIT_PERIOD_MINUTES", "1"))
    GLOBAL_RATE_LIMIT: bool = _bool(os.getenv("GLOBAL_RATE_LIMIT", "False"))
    MAX_GLOBAL_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_GLOBAL_REQUESTS_PER_MINUTE", "60"))

    MULTI_CLIENT: bool = False
    NAME: str = os.getenv("NAME", "PrimeAutoBotz")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "filetolink_05bot")
