from aiohttp import web
from server.stream_routes import routes


async def web_server():
    # Increase client_max_size for large uploads; use fast aiohttp settings
    app = web.Application(
        client_max_size=50 * 1024 * 1024,  # 50 MB
    )

    # Enable TCP keep-alive at the application level
    # aiohttp passes these to the underlying asyncio transport
    app["tcp_keepalive"]         = True
    app["tcp_keepalive_idle"]    = 60
    app["tcp_keepalive_interval"] = 10
    app["tcp_keepalive_count"]   = 5

    app.add_routes(routes)
    return app
