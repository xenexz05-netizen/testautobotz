import asyncio
import secrets
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from bot import StreamBot
from utils.database import db
from utils.decorators import check_banned
from utils.bot_utils import gen_links
from utils.force_channel import check_force_sub
from utils.rate_limiter import rate_limiter
from utils.logger import logger
from vars import Var

SUPPORTED_TYPES = (
    filters.document | filters.video | filters.photo | filters.audio |
    filters.voice | filters.animation | filters.video_note | filters.sticker
)


@StreamBot.on_message(SUPPORTED_TYPES & filters.private)
@check_banned
async def file_handler(client, message: Message):
    user = message.from_user
    if not user:
        return

    if not await db.is_user_exist(user.id):
        await db.add_user(user.id)

    if not await check_force_sub(client, message):
        return

    if rate_limiter.is_rate_limited(user.id):
        wait_time = rate_limiter.time_until_reset(user.id)
        await message.reply_text(
            f"⏳ You're sending files too fast!\n\n"
            f"Please wait **{wait_time} seconds** before sending another file.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Close", callback_data="close_panel")
            ]])
        )
        return

    status_msg = await message.reply_text("⏳ Processing your file, please wait...")

    try:
        try:
            stored_msg = await message.copy(chat_id=Var.BIN_CHANNEL)
        except FloodWait as e:
            await status_msg.edit_text(f"⏳ Rate limited by Telegram. Retrying in {e.value}s...")
            await asyncio.sleep(e.value)
            stored_msg = await message.copy(chat_id=Var.BIN_CHANNEL)

        rate_limiter.record_request(user.id)
        links = await gen_links(stored_msg)

        try:
            await status_msg.delete()
        except Exception:
            pass

        await message.reply_text(
            f"✅ **File stored successfully!**\n\n"
            f"📄 **Name:** `{links['media_name']}`\n"
            f"📦 **Size:** {links['media_size']}\n\n"
            f"🔗 **Your links are ready:**",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎬 Stream Now", url=links["stream_link"]),
                    InlineKeyboardButton("⬇️ Download", url=links["online_link"]),
                ]
            ]),
        )

    except FloodWait as e:
        await status_msg.edit_text(
            f"⏳ Telegram rate limit hit. Please try again in {e.value} seconds."
        )
    except Exception as e:
        error_id = secrets.token_hex(6)
        logger.error(f"file_handler [{error_id}]: {e}", exc_info=True)
        try:
            await status_msg.edit_text(
                f"❌ Something went wrong.\n**Error ID:** `{error_id}`\n\n"
                f"Make sure the bot is admin in the storage channel and try again."
            )
        except Exception:
            pass
