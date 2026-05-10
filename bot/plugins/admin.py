import asyncio
import os
import platform
import secrets
import subprocess
import time

import psutil
from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import StreamBot, multi_clients, work_loads
from utils.broadcast import broadcast_message
from utils.database import db
from utils.time_format import get_readable_time
from vars import Var

_start_time = time.time()


@StreamBot.on_message(filters.command("users") & filters.user(Var.OWNER_ID) & filters.private)
async def users_handler(client, message: Message):
    count = await db.total_users_count()
    await message.reply_text(
        f"👥 **Total Users:** `{count}`",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
            InlineKeyboardButton("❌ Close", callback_data="close_panel"),
        ]])
    )


@StreamBot.on_message(filters.command("status") & filters.user(Var.OWNER_ID) & filters.private)
async def status_handler(client, message: Message):
    uptime = get_readable_time(int(time.time() - _start_time))
    clients_info = "\n".join(
        f"  Client {cid}: {load} active streams"
        for cid, load in work_loads.items()
    )
    total_load = sum(work_loads.values())
    await message.reply_text(
        f"🤖 **Bot Status**\n\n"
        f"⏱ **Uptime:** {uptime}\n"
        f"👥 **Clients:** {len(multi_clients)}\n"
        f"📊 **Total Active Streams:** {total_load}\n\n"
        f"**Workload:**\n{clients_info}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
            InlineKeyboardButton("❌ Close", callback_data="close_panel"),
        ]])
    )


@StreamBot.on_message(filters.command("stats") & filters.user(Var.OWNER_ID) & filters.private)
async def stats_handler(client, message: Message):
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime = get_readable_time(int(time.time() - _start_time))
    await message.reply_text(
        f"📊 **System Stats**\n\n"
        f"⏱ **Bot Uptime:** {uptime}\n"
        f"🖥 **CPU:** {cpu}%\n"
        f"🧠 **RAM:** {mem.used // 1024**2}MB / {mem.total // 1024**2}MB ({mem.percent}%)\n"
        f"💾 **Disk:** {disk.used // 1024**3}GB / {disk.total // 1024**3}GB ({disk.percent}%)\n"
        f"🐍 **Python:** {platform.python_version()}\n"
        f"🖥 **OS:** {platform.system()} {platform.release()}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
            InlineKeyboardButton("❌ Close", callback_data="close_panel"),
        ]])
    )


@StreamBot.on_message(filters.command("broadcast") & filters.user(Var.OWNER_ID) & filters.private)
async def broadcast_handler(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text(
            "📢 **Broadcast**\n\nReply to a message with /broadcast to send it to all users.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Close", callback_data="close_panel")
            ]])
        )
        return
    await broadcast_message(client, message, mode="all")


@StreamBot.on_message(filters.command("ban") & filters.user(Var.OWNER_ID) & filters.private)
async def ban_handler(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("Usage: /ban <user_id>")
        return
    try:
        uid = int(args[1])
        await db.ban_user(uid)
        await message.reply_text(f"✅ User `{uid}` has been banned.")
    except ValueError:
        await message.reply_text("❌ Invalid user ID.")


@StreamBot.on_message(filters.command("unban") & filters.user(Var.OWNER_ID) & filters.private)
async def unban_handler(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("Usage: /unban <user_id>")
        return
    try:
        uid = int(args[1])
        await db.unban_user(uid)
        await message.reply_text(f"✅ User `{uid}` has been unbanned.")
    except ValueError:
        await message.reply_text("❌ Invalid user ID.")


@StreamBot.on_message(filters.command("shell") & filters.user(Var.OWNER_ID) & filters.private)
async def shell_handler(client, message: Message):
    cmd = message.text.split(None, 1)
    if len(cmd) < 2:
        await message.reply_text("Usage: /shell <command>")
        return
    try:
        result = subprocess.run(
            cmd[1], shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout or result.stderr or "No output"
        if len(output) > 4000:
            output = output[:4000] + "\n... (truncated)"
        await message.reply_text(f"```\n{output}\n```")
    except subprocess.TimeoutExpired:
        await message.reply_text("❌ Command timed out (30s limit)")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@StreamBot.on_message(filters.command("restart") & filters.user(Var.OWNER_ID) & filters.private)
async def restart_handler(client, message: Message):
    await message.reply_text("🔄 Restarting bot...")
    os.execv(__import__("sys").executable, [__import__("sys").executable] + __import__("sys").argv)


@StreamBot.on_message(filters.command("goforuser") & filters.user(Var.OWNER_ID) & filters.private)
async def goforuser_handler(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text(
            "📢 **DM Broadcast**\n\n"
            "Reply to any message (text, photo, video, sticker, document) "
            "with /goforuser to broadcast it to every user via DM.\n\n"
            "⚠️ This sends to ALL users. Use carefully.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Close", callback_data="close_panel")
            ]])
        )
        return
    await broadcast_message(client, message, mode="all")


@StreamBot.on_message(filters.command("pushinfo") & filters.user(Var.OWNER_ID) & filters.private)
async def pushinfo_handler(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text(
            "📡 **Stream Page Announcement**\n\n"
            "Reply to a **text**, **photo**, or **video** message with /pushinfo.\n"
            "It will appear as a banner on the stream page.\n\n"
            "To **clear** the banner, reply to a message containing only: `clear`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Close", callback_data="close_panel")
            ]])
        )
        return

    replied = message.reply_to_message
    content_html = ""

    if replied.text and replied.text.strip().lower() == "clear":
        await db.set_pushinfo({"content": None})
        await message.reply_text(
            "✅ **Stream page banner cleared.**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Close", callback_data="close_panel")
            ]])
        )
        return

    if replied.text:
        import re
        safe_text = replied.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        url_pattern = re.compile(r'(https?://[^\s<>"]+|www\.[^\s<>"]+|t\.me/[^\s<>"]+)')
        linked_text = url_pattern.sub(
            lambda m: f'<a href="{m.group(0)}" target="_blank" '
                      f'style="color:#00ff88;text-decoration:underline;">'
                      f'{m.group(0)}</a>',
            safe_text
        )
        content_html = f"<p style='margin:0;line-height:1.6;'>{linked_text}</p>"

    elif replied.photo:
        import base64
        import os as _os
        try:
            photo_path = await replied.download()
            with open(photo_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            _os.remove(photo_path)
            caption = ""
            if replied.caption:
                safe_cap = replied.caption.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                caption = f"<p style='margin:8px 0 0 0;font-size:14px;color:#c8d8e4;'>{safe_cap}</p>"
            content_html = (
                f'<img src="data:image/jpeg;base64,{b64}" '
                f'style="max-width:100%;border-radius:8px;display:block;">'
                f'{caption}'
            )
        except Exception as e:
            await message.reply_text(f"❌ Failed to process photo: {e}")
            return

    elif replied.video or replied.animation:
        caption = replied.caption or "Video announcement"
        safe_cap = caption.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        content_html = f"<p style='margin:0;'>📹 {safe_cap}</p>"

    elif replied.caption:
        safe_cap = replied.caption.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        content_html = f"<p style='margin:0;'>{safe_cap}</p>"

    else:
        await message.reply_text(
            "❌ Unsupported message type. Send text, photo, or video.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Close", callback_data="close_panel")
            ]])
        )
        return

    await db.set_pushinfo({"content": content_html})
    await message.reply_text(
        "✅ **Stream page banner updated!**\n\n"
        "The announcement now appears on all stream page visits.\n"
        "Reply to a message containing `clear` with /pushinfo to remove it.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🌐 View Stream Page", url=Var.URL),
            InlineKeyboardButton("❌ Close", callback_data="close_panel"),
        ]])
    )
