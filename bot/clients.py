import asyncio
import os
from pyrogram import Client
from bot import StreamBot, multi_clients, work_loads
from utils.logger import logger
from vars import Var


async def initialize_clients():
    multi_clients[0] = StreamBot
    work_loads[0] = 0
    print("   ✓ Primary client registered")

    extra_tokens = {}
    for i in range(1, 21):
        token = os.getenv(f"MULTI_TOKEN{i}", "").strip()
        if token:
            extra_tokens[i] = token

    if not extra_tokens:
        print("   ℹ No additional tokens — single client mode")
        return

    async def start_client(client_id: int, token: str):
        try:
            client = Client(
                name=f"client_{client_id}",
                api_id=Var.API_ID,
                api_hash=Var.API_HASH,
                bot_token=token,
                workers=Var.WORKERS,
                sleep_threshold=Var.SLEEP_THRESHOLD,
                max_concurrent_transmissions=1000,
                in_memory=True,
                no_updates=True
            )
            await client.start()
            work_loads[client_id] = 0
            print(f"   ✓ Extra client {client_id} started")
            return client_id, client
        except Exception as e:
            logger.error(f"Failed to start extra client {client_id}: {e}")
            return None

    results = await asyncio.gather(*[
        start_client(i, t) for i, t in extra_tokens.items()
    ])
    for result in results:
        if result:
            cid, client = result
            multi_clients[cid] = client

    if len(multi_clients) > 1:
        Var.MULTI_CLIENT = True
        print(f"   ✓ Multi-client mode: {len(multi_clients)} total clients")


async def cleanup_clients():
    for cid, client in multi_clients.items():
        if cid == 0:
            continue
        try:
            await client.stop()
        except Exception as e:
            logger.error(f"Error stopping client {cid}: {e}")
