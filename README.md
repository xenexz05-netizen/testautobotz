# PrimeAutoBotz — File2Link Bot

High-speed Telegram file streaming bot. Deploy on Railway free tier.

## Railway Deployment

### Required Environment Variables

Set these in Railway → Variables:

| Variable | Description |
|---|---|
| `API_ID` | From https://my.telegram.org |
| `API_HASH` | From https://my.telegram.org |
| `BOT_TOKEN` | From @BotFather on Telegram |
| `OWNER_ID` | Your Telegram user ID (from @userinfobot) |
| `BIN_CHANNEL` | Private channel ID where files are stored (bot must be admin) |
| `DATABASE_URL` | PostgreSQL connection string (free at https://neon.tech) |
| `FQDN` | Your Railway public domain (e.g. `yourapp.up.railway.app`) |
| `PORT` | `8080` (Railway default) |
| `HAS_SSL` | `True` |
| `NO_PORT` | `True` |

### Deploy Steps

1. Push this folder to a GitHub repo
2. Go to https://railway.app → New Project → Deploy from GitHub repo
3. Add all environment variables listed above
4. Railway will auto-detect Python and start the bot

### Force Subscription

Users must join **@PrimeAutoBotz** (channel ID: `-1003792781847`) before using the bot.
This is hardcoded and requires no configuration.

### Speed Features

- 2 MB chunk size for fast streaming
- 4-chunk prefetch queue per stream
- 10-minute message metadata cache (1000 entry cap)
- Memory cleanup job every 5 minutes (safe for active streams)
- uvloop for maximum async throughput
