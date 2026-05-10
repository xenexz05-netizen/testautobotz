from pyrogram.types import Message
from utils.human_readable import humanbytes


def get_media(message: Message):
    media_types = (
        "document", "video", "photo", "audio",
        "voice", "animation", "video_note", "sticker"
    )
    for attr in media_types:
        media = getattr(message, attr, None)
        if media:
            return media
    return None


def get_fname(message: Message) -> str:
    media = get_media(message)
    if not media:
        return "Unknown"
    name = getattr(media, "file_name", None)
    if name:
        return name
    media_type = type(media).__name__.lower()
    ext_map = {
        "photo": "jpg", "audio": "mp3", "voice": "ogg",
        "video": "mp4", "animation": "mp4", "videonote": "mp4",
        "sticker": "webp"
    }
    ext = ext_map.get(media_type, "bin")
    return f"File2Link_{message.id}.{ext}"


def get_fsize(message: Message) -> str:
    media = get_media(message)
    if not media:
        return "0 B"
    size = getattr(media, "file_size", 0) or 0
    return humanbytes(size)


def get_fsize_bytes(message: Message) -> int:
    media = get_media(message)
    if not media:
        return 0
    return getattr(media, "file_size", 0) or 0


def get_mime(message: Message) -> str:
    media = get_media(message)
    if not media:
        return "application/octet-stream"
    mime = getattr(media, "mime_type", None)
    if mime:
        return mime
    media_type = type(media).__name__.lower()
    mime_map = {
        "photo": "image/jpeg",
        "voice": "audio/ogg",
        "videonote": "video/mp4",
        "sticker": "image/webp",
    }
    return mime_map.get(media_type, "application/octet-stream")
