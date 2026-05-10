from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import StreamBot
from utils.database import db
from utils.decorators import check_banned
from utils.messages import START_MSG, HELP_MSG, ABOUT_MSG
from vars import Var


@StreamBot.on_message(filters.command("start") & filters.private)
@check_banned
async def start_handler(client, message: Message):
    user = message.from_user
    if user and not await db.is_user_exist(user.id):
        await db.add_user(user.id)
    await message.reply_text(
        START_MSG,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📖 Help", callback_data="help"),
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
            ],
            [
                InlineKeyboardButton("📢 Updates", url="https://t.me/PrimeAutoBotz"),
                InlineKeyboardButton("❌ Close", callback_data="close_panel"),
            ],
        ]),
        disable_web_page_preview=True,
    )


@StreamBot.on_message(filters.command("help") & filters.private)
@check_banned
async def help_handler(client, message: Message):
    await message.reply_text(
        HELP_MSG.format(max_batch=Var.MAX_BATCH_FILES),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Home", callback_data="home"),
            InlineKeyboardButton("❌ Close", callback_data="close_panel"),
        ]]),
    )


@StreamBot.on_message(filters.command("about") & filters.private)
@check_banned
async def about_handler(client, message: Message):
    await message.reply_text(
        ABOUT_MSG,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Home", callback_data="home"),
            InlineKeyboardButton("❌ Close", callback_data="close_panel"),
        ]]),
        disable_web_page_preview=False,
    )
