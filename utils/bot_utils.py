from vars import Var
from utils.file_properties import get_media, get_fname, get_fsize


async def gen_links(stored_msg) -> dict:
    media = get_media(stored_msg)
    unique_id = getattr(media, "file_unique_id", "")
    secure_hash = unique_id[:6]
    msg_id = stored_msg.id

    stream_link = f"{Var.URL}watch/{secure_hash}{msg_id}"
    online_link = f"{Var.URL}{secure_hash}{msg_id}"

    return {
        "stream_link": stream_link,
        "online_link": online_link,
        "media_name": get_fname(stored_msg),
        "media_size": get_fsize(stored_msg),
    }


async def is_admin(client, user_id: int) -> bool:
    return user_id == Var.OWNER_ID
