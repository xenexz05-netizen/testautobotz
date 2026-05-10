from pyrogram import Client
from vars import Var

StreamBot = Client(
    name="File2LinkBot",
    api_id=Var.API_ID,
    api_hash=Var.API_HASH,
    bot_token=Var.BOT_TOKEN,
    workers=Var.WORKERS,
    sleep_threshold=Var.SLEEP_THRESHOLD,
    in_memory=True,
)

multi_clients: dict = {}
work_loads: dict = {}
