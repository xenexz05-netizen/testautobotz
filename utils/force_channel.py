from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from vars import Var

CHANNEL_ID = -1003792781847
CHANNEL_USERNAME = "PrimeAutoBotz"
CHANNEL_URL = f"https://t.me/{CHANNEL_USERNAME}"


async def check_force_sub(client: Client, message: Message) -> bool:
    """Check if user is subscribed to PrimeAutoBotz. Returns True if OK, False otherwise."""
    user_id = None
    # Support both Message and CallbackQuery-derived message
    try:
        if hasattr(message, 'from_user') and message.from_user:
            user_id = message.from_user.id
    except Exception:
        pass

    if not user_id:
        return True

    try:
        member = await client.get_chat_member(CHANNEL_ID, user_id)
        if member.status.value in ("left", "banned", "kicked"):
            raise UserNotParticipant
        return True
    except UserNotParticipant:
        await message.reply_text(
            "⚠️ **Access Restricted!**\n\n"
            "You must join **PrimeAutoBotz** channel to use this bot.\n\n"
            "👇 Click below to join, then press ✅ Check Joined.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📢 Join PrimeAutoBotz", url=CHANNEL_URL),
                    InlineKeyboardButton("✅ Check Joined", callback_data="check_sub"),
                ]
            ])
        )
        return False
    except Exception:
        # If we can't verify, let them through to not block on API errors
        return True
