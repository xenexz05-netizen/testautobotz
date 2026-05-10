def get_readable_time(seconds: int) -> str:
    result = ""
    periods = [
        ("day", 86400),
        ("hour", 3600),
        ("minute", 60),
        ("second", 1),
    ]
    for name, count in periods:
        value = seconds // count
        if value:
            seconds -= value * count
            result += f"{int(value)} {name}{'s' if value != 1 else ''}, "
    return result.rstrip(", ") or "0 seconds"
