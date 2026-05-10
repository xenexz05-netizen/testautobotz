START_MSG = """
**Welcome to File2Link Bot!** 🎬

Send me any file and I'll generate a permanent streaming + download link for you.

**Supported:** Documents, Videos, Photos, Audio, Voice, GIFs, Stickers

Just forward or send any file here!
"""

HELP_MSG = """
**How to use File2Link Bot:**

1. Send or forward any file to me in private chat
2. I'll copy it to secure storage and generate links
3. Use the **Stream Now** button to watch in browser
4. Use the **Download** button to download directly

**Tips:**
- Links are permanent and never expire
- Videos support timeline seeking in the browser
- You can send up to {max_batch} files at once

**Commands:**
/start — Start the bot
/help — Show this help
/about — About this bot
"""

ABOUT_MSG = """
**File2Link Bot** v2.0

A high-speed Telegram file streaming bot powered by:
• pyrofork + TgCrypto (fastest MTProto)
• uvloop (libuv event loop)
• aiohttp (zero-buffer streaming)
• PostgreSQL via asyncpg (permanent storage)

**Creator:** [@takezo_5](https://t.me/takezo_5)
**Updates:** [@PrimeAutoBotz](https://t.me/PrimeAutoBotz)
"""

PROCESSING_MSG = "⏳ Processing your file, please wait..."

BANNED_MSG = "❌ You are banned from using this bot."

FORCE_SUB_MSG = """
**You must join our channel first!**

Please join the channel below and then try again.
"""

BROADCAST_PROGRESS = "📢 **Broadcast in progress...**\n\n✅ Sent: {sent}\n❌ Failed: {failed}\n🗑 Removed: {removed}\n⏱ Time: {time}"

BROADCAST_DONE = "📢 **Broadcast complete!**\n\n✅ Sent: {sent}\n❌ Failed: {failed}\n🗑 Removed: {removed}\n⏱ Time: {time}"

BROADCAST_CANCELLED = "🛑 **Broadcast cancelled.**\n\n✅ Sent: {sent}\n❌ Failed: {failed}\n🗑 Removed: {removed}"
