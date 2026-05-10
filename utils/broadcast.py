import asyncio
import secrets
import time
from pyrogram import Client
from pyrogram.errors import (
    FloodWait, UserIsBlocked, UserDeactivated,
    PeerIdInvalid, InputUserDeactivated
)
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.database import db
from utils.logger import logger
from utils.time_format import get_readable_time

_cancel_flags: dict = {}


async def broadcast_message(client: Client, message: Message, mode: str = "all"):
    broadcast_id = secrets.token_hex(8)
    _cancel_flags[broadcast_id] = False

    msg_to_send = message.reply_to_message
    start_time = time.time()
    sent = failed = removed = 0

    status_msg = await message.reply_text(
        "📢 **Broadcast started...**\n\n✅ Sent: 0\n❌ Failed: 0\n🗑 Removed: 0\n⏱ Time: 0s",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🛑 Cancel", callback_data=f"cancel_{broadcast_id}")
        ]])
    )

    async def do_broadcast():
        nonlocal sent, failed, removed
        try:
            users = await db.get_all_users()
        except Exception as e:
            logger.error(f"Broadcast: failed to fetch users: {e}")
            await status_msg.edit_text("❌ Broadcast failed: could not fetch users.")
            return

        for user in users:
            if _cancel_flags.get(broadcast_id):
                break
            try:
                user_id = user["user_id"]
            except (KeyError, TypeError):
                continue

            try:
                try:
                    await msg_to_send.copy(user_id)
                    sent += 1
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    await msg_to_send.copy(user_id)
                    sent += 1
            except (UserIsBlocked, UserDeactivated, InputUserDeactivated, PeerIdInvalid):
                await db.delete_user(user_id)
                removed += 1
            except Exception as e:
                logger.warning(f"Broadcast fail {user_id}: {e}")
                failed += 1

            total = sent + failed + removed
            if total > 0 and total % 20 == 0:
                try:
                    elapsed = get_readable_time(int(time.time() - start_time))
                    await status_msg.edit_text(
                        f"📢 **Broadcast in progress...**\n\n"
                        f"✅ Sent: {sent}\n❌ Failed: {failed}\n"
                        f"🗑 Removed: {removed}\n⏱ Time: {elapsed}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(
                                "🛑 Cancel",
                                callback_data=f"cancel_{broadcast_id}"
                            )
                        ]])
                    )
                except Exception:
                    pass
            await asyncio.sleep(0.05)

        elapsed = get_readable_time(int(time.time() - start_time))
        cancelled = _cancel_flags.get(broadcast_id, False)
        final = (
            f"🛑 **Broadcast cancelled.**\n\n"
            f"✅ Sent: {sent}\n❌ Failed: {failed}\n🗑 Removed: {removed}"
            if cancelled else
            f"📢 **Broadcast complete!**\n\n"
            f"✅ Sent: {sent}\n❌ Failed: {failed}\n"
            f"🗑 Removed: {removed}\n⏱ Time: {elapsed}"
        )
        try:
            await status_msg.edit_text(final)
        except Exception:
            pass
        _cancel_flags.pop(broadcast_id, None)

    asyncio.create_task(do_broadcast())
    return broadcast_id


def cancel_broadcast(broadcast_id: str) -> bool:
    if broadcast_id in _cancel_flags:
        _cancel_flags[broadcast_id] = True
        return True
    return False
