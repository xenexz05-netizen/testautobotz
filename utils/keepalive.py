import asyncio
import aiohttp
from utils.logger import logger
from vars import Var


async def ping_server():
    await asyncio.sleep(60)
    ping_url = f"{Var.URL}cdn-check"

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(
                    ping_url,
                    headers={
                        "Cache-Control": "no-cache, no-store",
                        "Pragma": "no-cache",
                        "X-Ping-Source": "File2Link-Keepalive",
                    },
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    logger.debug(f"Keep-alive ping → {resp.status}")
            except asyncio.TimeoutError:
                logger.warning("Keep-alive ping timed out")
            except Exception as e:
                logger.warning(f"Keep-alive ping failed: {e}")

            await asyncio.sleep(Var.PING_INTERVAL)
