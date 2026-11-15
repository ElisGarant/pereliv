"""Проверка Telegram Mini App initData по алгоритму из документации Telegram."""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


class InitDataError(ValueError):
    pass


def validate_init_data(init_data: str, bot_token: str, ttl: int = 86400, now: float | None = None) -> dict:
    if not init_data or not bot_token:
        raise InitDataError("нет initData или токена бота")
    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    received = pairs.pop("hash", None)
    if not received:
        raise InitDataError("нет подписи")
    check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise InitDataError("подпись не совпадает")
    auth_date = int(pairs.get("auth_date", "0") or 0)
    if ttl and (now or time.time()) - auth_date > ttl:
        raise InitDataError("initData устарели")
    try:
        user = json.loads(pairs.get("user", "{}"))
    except json.JSONDecodeError as e:
        raise InitDataError("некорректный user") from e
    if "id" not in user:
        raise InitDataError("нет пользователя")
    pairs["user"] = user
    return pairs


def sign_init_data(fields: dict, bot_token: str) -> str:
    """Собирает подписанную строку initData. Нужна для тестов и локальной отладки."""
    from urllib.parse import urlencode

    data = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else str(v)) for k, v in fields.items()}
    check_string = "\n".join(f"{k}={data[k]}" for k in sorted(data))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(data)
