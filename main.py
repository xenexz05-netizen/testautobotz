import asyncio
import sys

import uvloop

# Set event loop policy BEFORE any imports that create the Client/Dispatcher.
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from aiohttp import web
from pyrogram import idle
from pyrogram.errors import FloodWait

from bot import StreamBot, multi_clients, work_loads
from bot.clients import initialize_clients, cleanup_clients
from server import web_server
from utils.custom_dl import evict_expired
from utils.database import db
from utils.keepalive import ping_server
from utils.logger import logger
from vars import Var

import time


def load_plugins():
    import bot.plugins.start
    import bot.plugins.stream
    import bot.plugins.admin
    import bot.plugins.callbacks
    print("   ✓ Plugins loaded")


async def set_commands():
    from pyrogram.types import (
        BotCommand,
        BotCommandScopeChat,
        BotCommandScopeDefault,
        BotCommandScopeAllPrivateChats,
        BotCommandScopeAllGroupChats,
    )

    for scope in [
        BotCommandScopeDefault(),
        BotCommandScopeAllPrivateChats(),
        BotCommandScopeAllGroupChats(),
    ]:
        try:
            await StreamBot.delete_bot_commands(scope=scope)
        except Exception:
            pass

    admin_cmds = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "How to use the bot"),
        BotCommand("about", "About PrimeAutoBotz"),
        BotCommand("goforuser", "Broadcast a message to all users via DM"),
        BotCommand("pushinfo", "Set or clear the stream page announcement banner"),
        BotCommand("broadcast", "Broadcast a message to all users"),
        BotCommand("users", "Show total registered users"),
        BotCommand("status", "Show bot status and active streams"),
        BotCommand("stats", "Show system CPU RAM and disk usage"),
        BotCommand("ban", "Ban a user from using the bot"),
        BotCommand("unban", "Unban a previously banned user"),
        BotCommand("shell", "Run a shell command on the server"),
        BotCommand("restart", "Restart the bot process"),
    ]
    try:
        await StreamBot.set_bot_commands(
            admin_cmds,
            scope=BotCommandScopeChat(chat_id=Var.OWNER_ID)
        )
    except Exception:
        pass


async def memory_cleanup_job():
    """
    Evict expired message + file-info cache entries every 5 minutes.
    Safe for active streams — stream_file() holds its own Message reference
    locally, so removing from the cache dict doesn't interrupt delivery.
    """
    while True:
        await asyncio.sleep(300)
        try:
            count = evict_expired()
            if count:
                logger.debug(f"Memory cleanup: evicted {count} expired cache entries")
        except Exception as e:
            logger.warning(f"Memory cleanup error: {e}")


async def main():
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║          PRIMEAUTOBOTZ — STARTING UP 🚀                  ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # CRITICAL: asyncio.run() always creates a brand-new event loop.
    StreamBot.dispatcher.loop = asyncio.get_event_loop()

    try:
        await db.connect()
        print("   ✓ PostgreSQL connected")
    except Exception as e:
        print(f"\n❌ DATABASE CONNECTION FAILED: {e}")
        print("   Check your DATABASE_URL variable in Railway settings.")
        sys.exit(1)

    load_plugins()
    await asyncio.sleep(0)

    while True:
        try:
            await StreamBot.start()
            break
        except FloodWait as e:
            print(f"   ⏳ FloodWait: sleeping {e.value}s before retry...")
            await asyncio.sleep(e.value + 5)
        except Exception as e:
            print(f"\n❌ BOT START FAILED: {e}")
            print("   Check your BOT_TOKEN and API_ID/API_HASH variables.\n")
            sys.exit(1)

    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username
    print(f"   ✓ Bot started as @{StreamBot.username}")

    await initialize_clients()

    try:
        await set_commands()
        print("   ✓ Bot commands registered")
    except Exception as e:
        print(f"   ⚠ Commands not set: {e}")

    try:
        runner = web.AppRunner(await web_server())
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", Var.PORT)
        await site.start()
        print(f"   ✓ Web server started on port {Var.PORT}")
        print(f"   ✓ Public URL: {Var.URL}")
    except Exception as e:
        print(f"\n❌ WEB SERVER FAILED: {e}")
        sys.exit(1)

    asyncio.create_task(ping_server())
    print("   ✓ Keep-alive ping started")

    asyncio.create_task(memory_cleanup_job())
    print("   ✓ Memory cleanup job started (every 5 min)")

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║             BOT IS RUNNING ✅                            ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    await idle()

    await cleanup_clients()
    await StreamBot.stop()
    await db.close()
    await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except ValueError as e:
        print(e)
        sys.exit(1)
