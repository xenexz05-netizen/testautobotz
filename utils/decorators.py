import functools
from pyrogram.types import Message
from utils.database import db
from utils.logger import logger
from vars import Var


def check_banned(func):
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        try:
            user_id = message.from_user.id if message.from_user else None
            if user_id:
                try:
                    if await db.is_banned(user_id):
                        await message.reply_text("❌ You are banned from using this bot.")
                        return
                except Exception as e:
                    logger.warning(f"check_banned DB error (allowing through): {e}")
        except Exception as e:
            logger.warning(f"check_banned unexpected error: {e}")
        return await func(client, message, *args, **kwargs)
    return wrapper


def owner_only(func):
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        user_id = message.from_user.id if message.from_user else None
        if user_id != Var.OWNER_ID:
            await message.reply_text("❌ This command is for the bot owner only.")
            return
        return await func(client, message, *args, **kwargs)
    return wrapper
