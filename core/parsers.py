import re

def is_yandex_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@(yandex\.ru|ya\.ru)$'
    return bool(re.match(pattern, email, re.IGNORECASE))