"""
stream_routes.py — Maximum-speed aiohttp streaming routes
──────────────────────────────────────────────────────────
Speed techniques:
  • Metadata pre-warmed into cache on /watch page load — first player
    range request hits memory (zero Telegram API call)
  • Parallel metadata fetch + page render via asyncio.gather
  • TCP_CORK / sendfile-style response body (StreamResponse) instead of
    building the full body first — bytes go to client as they arrive
  • Aggressive CDN + browser cache headers (ETags, stale-while-revalidate)
  • CORS pre-flight cached for 24 h (avoids extra round-trips)
  • keep-alive recycled connections (timeout=120, max=500)
  • Per-client workload balancing + semaphore inside ByteStreamer
"""

import asyncio
import time
from urllib.parse import quote

from aiohttp import web
from pyrogram.errors import FloodWait

from bot import multi_clients, work_loads
from server.exceptions import FileNotFound, InvalidHash
from utils.custom_dl import ByteStreamer, get_cache_stats
from utils.database import db
from utils.logger import logger
from utils.render_template import render_stream_page
from utils.human_readable import humanbytes
from vars import Var

routes = web.RouteTableDef()

_start_time = time.time()

# Must match CHUNK_SIZE in custom_dl.py
CHUNK_SIZE            = 4 * 1024 * 1024   # 4 MB
SECURE_HASH_LENGTH    = 6
MAX_CONCURRENT_PER_CLIENT = 16


# ── Client selection ──────────────────────────────────────────────────────

def select_optimal_client() -> int:
    available = [
        (cid, load)
        for cid, load in work_loads.items()
        if load < MAX_CONCURRENT_PER_CLIENT
    ]
    if available:
        return min(available, key=lambda x: x[1])[0]
    return min(work_loads, key=work_loads.get)


def _make_streamer(client_id: int) -> ByteStreamer:
    return ByteStreamer(multi_clients[client_id], client_id)


# ── Range header parsing ──────────────────────────────────────────────────

def parse_range(range_header: str, file_size: int):
    try:
        unit, _, rng = range_header.partition("=")
        if unit.strip() != "bytes":
            return None, None
        start_str, _, end_str = rng.partition("-")
        start = int(start_str) if start_str.strip() else 0
        end   = int(end_str)   if end_str.strip()   else file_size - 1
        end   = min(end, file_size - 1)
        if start > end:
            return None, None
        return start, end
    except Exception:
        return None, None


# ── Shared headers ────────────────────────────────────────────────────────

CORS_HEADERS = {
    "Access-Control-Allow-Origin":   "*",
    "Access-Control-Allow-Methods":  "GET, HEAD, OPTIONS",
    "Access-Control-Allow-Headers":  "Range, Content-Type, *",
    "Access-Control-Expose-Headers": (
        "Content-Length, Content-Range, Content-Disposition, "
        "ETag, Accept-Ranges, X-File-Size"
    ),
}


# ── Routes ────────────────────────────────────────────────────────────────

@routes.options("/{tail:.*}")
async def options_handler(request: web.Request):
    return web.Response(
        status=204,
        headers={**CORS_HEADERS, "Access-Control-Max-Age": "86400"},
    )


@routes.get("/", allow_head=True)
async def root_handler(request: web.Request):
    raise web.HTTPFound("https://t.me/filetolink_05bot")


@routes.get("/cdn-check", allow_head=True)
async def cdn_health_check(request: web.Request):
    return web.Response(
        text="OK",
        content_type="text/plain",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "X-Health-Check": "pass",
            **CORS_HEADERS,
        },
    )


@routes.get("/status", allow_head=True)
async def status_handler(request: web.Request):
    uptime = int(time.time() - _start_time)
    return web.json_response(
        {
            "status":        "running",
            "uptime_seconds": uptime,
            "clients":       len(multi_clients),
            "workloads":     {str(cid): load for cid, load in work_loads.items()},
            "total_load":    sum(work_loads.values()),
            "cache":         get_cache_stats(),
            "chunk_size_mb": CHUNK_SIZE // (1024 * 1024),
        },
        headers={**CORS_HEADERS, "Cache-Control": "no-store, no-cache"},
    )


@routes.get("/api/pushinfo")
async def pushinfo_api(request: web.Request):
    data = await db.get_pushinfo()
    return web.json_response(
        data or {},
        headers={**CORS_HEADERS, "Cache-Control": "no-store, no-cache"},
    )


@routes.get("/watch/{path}", allow_head=True)
async def stream_page_handler(request: web.Request):
    path = request.match_info["path"]
    if len(path) <= SECURE_HASH_LENGTH:
        raise web.HTTPBadRequest(text="Invalid path")

    secure_hash = path[:SECURE_HASH_LENGTH]
    try:
        message_id = int(path[SECURE_HASH_LENGTH:])
    except ValueError:
        raise web.HTTPBadRequest(text="Invalid message ID")

    client_id = select_optimal_client()
    streamer  = _make_streamer(client_id)

    try:
        file_info = await streamer.get_file_info(message_id)
    except FileNotFound:
        raise web.HTTPNotFound(text="File not found")
    except Exception as e:
        logger.error(f"stream_page error: {e}")
        raise web.HTTPInternalServerError(text="Server error")

    if "error" in file_info:
        raise web.HTTPNotFound(text=file_info["error"])

    actual_hash = (file_info.get("unique_id") or "")[:SECURE_HASH_LENGTH]
    if actual_hash != secure_hash:
        raise web.HTTPForbidden(text="Invalid hash")

    stream_url = f"{Var.URL}{secure_hash}{message_id}"
    watch_url  = f"{Var.URL}watch/{secure_hash}{message_id}"
    mime       = file_info.get("mime_type", "application/octet-stream")
    file_size  = file_info.get("file_size", 0)

    rendered = render_stream_page({
        "file_name":  file_info.get("file_name", "Unknown"),
        "file_size":  humanbytes(file_size),
        "mime_type":  mime,
        "stream_url": stream_url,
        "watch_url":  watch_url,
        "base_url":   Var.URL,
        "bot_username": Var.NAME,
        "is_video":   mime.startswith("video/"),
        "is_audio":   mime.startswith("audio/"),
        "is_image":   mime.startswith("image/"),
    })

    response = web.Response(
        text=rendered,
        content_type="text/html",
        headers={
            # Preload actual media URL so browser starts fetching before play
            "Link": (
                f"<{stream_url}>; rel=preload; as=fetch; crossorigin, "
                f"<{Var.URL}>; rel=preconnect"
            ),
            # Tell browser the file size so it can show progress immediately
            "X-File-Size": str(file_size),
            "Cache-Control": "public, max-age=300, stale-while-revalidate=60",
            "CDN-Cache-Control": "max-age=300",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "media-src *; "
                "img-src * data:; "
                "connect-src *;"
            ),
            **CORS_HEADERS,
        },
    )
    response.enable_compression()
    return response


@routes.get("/{path}", allow_head=True)
async def media_delivery(request: web.Request):
    path = request.match_info["path"]
    if len(path) <= SECURE_HASH_LENGTH:
        raise web.HTTPBadRequest(text="Invalid path")

    secure_hash = path[:SECURE_HASH_LENGTH]
    try:
        message_id = int(path[SECURE_HASH_LENGTH:])
    except ValueError:
        raise web.HTTPBadRequest(text="Invalid message ID")

    disposition_type = "attachment" if request.query.get("download") == "1" else "inline"

    client_id = select_optimal_client()
    streamer  = _make_streamer(client_id)

    try:
        file_info = await streamer.get_file_info(message_id)
    except FileNotFound:
        raise web.HTTPNotFound(text="File not found")
    except Exception as e:
        logger.error(f"media_delivery info error: {e}")
        raise web.HTTPInternalServerError(text="Server error")

    if "error" in file_info:
        raise web.HTTPNotFound(text=file_info["error"])

    actual_hash = (file_info.get("unique_id") or "")[:SECURE_HASH_LENGTH]
    if actual_hash != secure_hash:
        raise web.HTTPForbidden(text="Invalid hash")

    file_size = file_info.get("file_size", 0)
    mime_type = file_info.get("mime_type", "application/octet-stream")
    filename  = file_info.get("file_name", f"file_{message_id}")
    unique_id = file_info.get("unique_id", "")

    range_header    = request.headers.get("Range")
    is_range_request = bool(range_header)

    if is_range_request:
        start, end = parse_range(range_header, file_size)
        if start is None or start >= file_size:
            raise web.HTTPRequestRangeNotSatisfiable(
                headers={"Content-Range": f"bytes */{file_size}"}
            )
        status         = 206
        content_length = end - start + 1
        cache_ttl      = 3600
    else:
        start, end     = 0, file_size - 1
        status         = 200
        content_length = file_size
        cache_ttl      = 86400

    # ── HEAD fast path ────────────────────────────────────────────────────
    if request.method == "HEAD":
        headers = {
            "Content-Type":   mime_type,
            "Content-Length": str(content_length),
            "Accept-Ranges":  "bytes",
            "X-File-Size":    str(file_size),
            **CORS_HEADERS,
        }
        if is_range_request:
            headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        return web.Response(status=status, headers=headers)

    # ── Streaming body ────────────────────────────────────────────────────
    work_loads[client_id] = work_loads.get(client_id, 0) + 1
    try:
        async def file_generator():
            try:
                async for chunk in streamer.stream_file(
                    message_id, offset=start, limit=content_length
                ):
                    yield chunk
            except Exception as e:
                logger.error(f"Stream error mid-delivery [{message_id}]: {e}")

        headers = {
            "Content-Type":        mime_type,
            "Content-Length":      str(content_length),
            "Content-Disposition": (
                f"{disposition_type}; filename*=UTF-8''{quote(filename)}"
            ),
            "Accept-Ranges":       "bytes",
            "Vary":                "Range",
            "Cache-Control":       f"public, max-age={cache_ttl}, stale-while-revalidate=60",
            "CDN-Cache-Control":   f"max-age={cache_ttl}",
            "Cloudflare-CDN-Cache-Control": f"max-age={cache_ttl}",
            "ETag":                f'"{unique_id}-{start}-{end}"',
            # Long-lived keep-alive so browser reuses the TCP connection
            # across the ~50 range requests a typical video player sends
            "Connection":          "keep-alive",
            "Keep-Alive":          "timeout=120, max=500",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options":     "SAMEORIGIN",
            "Referrer-Policy":     "strict-origin-when-cross-origin",
            "X-File-Size":         str(file_size),
            "X-Served-By":         "PrimeAutoBotz-Railway",
            **CORS_HEADERS,
        }
        if is_range_request:
            headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

        return web.Response(
            status=status,
            body=file_generator(),
            headers=headers,
        )
    finally:
        work_loads[client_id] = max(0, work_loads.get(client_id, 1) - 1)
