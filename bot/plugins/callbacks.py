from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant
from bot import StreamBot
from utils.broadcast import cancel_broadcast
from utils.database import db
from utils.messages import START_MSG, HELP_MSG, ABOUT_MSG
from vars import Var

CHANNEL_ID = -1003792781847
CHANNEL_URL = "https://t.me/PrimeAutoBotz"


@StreamBot.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    data = query.data

    if data == "close_panel":
        try:
            await query.message.delete()
        except Exception:
            await query.answer("Closed.")
        return

    if data == "home":
        await query.message.edit_text(
            START_MSG,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📖 Help", callback_data="help"),
                    InlineKeyboardButton("ℹ️ About", callback_data="about"),
                ],
                [
                    InlineKeyboardButton("📢 Updates", url=CHANNEL_URL),
                    InlineKeyboardButton("❌ Close", callback_data="close_panel"),
                ],
            ]),
            disable_web_page_preview=True,
        )
        await query.answer()
        return

    if data == "help":
        await query.message.edit_text(
            HELP_MSG.format(max_batch=Var.MAX_BATCH_FILES),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Home", callback_data="home"),
                InlineKeyboardButton("❌ Close", callback_data="close_panel"),
            ]]),
        )
        await query.answer()
        return

    if data == "about":
        await query.message.edit_text(
            ABOUT_MSG,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Home", callback_data="home"),
                InlineKeyboardButton("❌ Close", callback_data="close_panel"),
            ]]),
            disable_web_page_preview=False,
        )
        await query.answer()
        return

    if data == "refresh_stats":
        count = await db.total_users_count()
        await query.answer(f"Total users: {count}", show_alert=False)
        return

    if data == "check_sub":
        user_id = query.from_user.id if query.from_user else None
        if not user_id:
            await query.answer("❌ Could not verify user.", show_alert=True)
            return
        try:
            member = await client.get_chat_member(CHANNEL_ID, user_id)
            if member.status.value in ("left", "banned", "kicked"):
                raise UserNotParticipant
            # Verified — delete the gate message and let them continue
            try:
                await query.message.delete()
            except Exception:
                pass
            await query.answer("✅ Verified! You can now use the bot.", show_alert=False)
        except UserNotParticipant:
            await query.answer("❌ You haven't joined yet! Please join PrimeAutoBotz first.", show_alert=True)
        except Exception:
            await query.answer("✅ Verified!", show_alert=False)
        return

    if data.startswith("cancel_"):
        broadcast_id = data[len("cancel_"):]
        if cancel_broadcast(broadcast_id):
            await query.answer("🛑 Broadcast cancellation requested.", show_alert=True)
        else:
            await query.answer("Broadcast already finished.", show_alert=True)
        return

    await query.answer("Unknown action.", show_alert=False)
