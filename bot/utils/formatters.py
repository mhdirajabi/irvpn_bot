from datetime import datetime


def format_data_limit(data_limit: int) -> str:
    if data_limit is None:
        return "♾️ نامحدود"
    return f"{data_limit / 1024**3:.2f} گیگابایت"


def format_expire_date(expire: int) -> str:
    if expire is None:
        return "♾️ لایف‌تایم"
    return datetime.fromtimestamp(expire).strftime("%Y-%m-%d")
