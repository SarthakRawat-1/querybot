import hashlib
import json
from typing import Any, Callable, Optional
import redis
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_client: Optional[redis.Redis] = None
_unavailable = False


def init_cache() -> None:
    global _client, _unavailable

    url = settings.REDIS_URL
    if not url:
        logger.info('REDIS_URL is not set; caching is disabled')
        _unavailable = True
        return

    try:
        client = redis.Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            health_check_interval=30,
        )
        client.ping()
    except redis.RedisError as exc:
        logger.warning('Redis is unavailable, continuing without a cache: %s', exc)
        _unavailable = True
        return

    _client = client
    _unavailable = False
    logger.info('Cache connected')


def get_client() -> Optional[redis.Redis]:
    return None if _unavailable else _client


def build_key(*parts: Any) -> str:
    pieces = []
    for part in parts:
        text = str(part)
        if len(text) > 64:
            text = hashlib.sha256(text.encode('utf-8')).hexdigest()[:32]
        pieces.append(text)
    return 'querybot:' + ':'.join(pieces)


def get_json(key: str) -> Optional[Any]:
    client = get_client()
    if client is None:
        return None

    try:
        raw = client.get(key)
    except redis.RedisError as exc:
        logger.debug('Cache read failed for %s: %s', key, exc)
        return None

    if raw is None:
        return None

    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        logger.debug('Discarding malformed cache entry %s', key)
        return None


def set_json(key: str, value: Any, ttl: int = 3600) -> None:
    client = get_client()
    if client is None:
        return

    try:
        client.setex(key, ttl, json.dumps(value, default=str))
    except (redis.RedisError, TypeError, ValueError) as exc:
        logger.debug('Cache write failed for %s: %s', key, exc)


def delete(*keys: str) -> None:
    client = get_client()
    if client is None or not keys:
        return

    try:
        client.delete(*keys)
    except redis.RedisError as exc:
        logger.debug('Cache delete failed: %s', exc)


def delete_prefix(prefix: str) -> None:
    client = get_client()
    if client is None:
        return

    try:
        for key in client.scan_iter(match=f'{prefix}*', count=200):
            client.delete(key)
    except redis.RedisError as exc:
        logger.debug('Cache prefix delete failed for %s: %s', prefix, exc)


def cached_json(key: str, ttl: int, producer: Callable[[], Any]) -> Any:
    hit = get_json(key)
    if hit is not None:
        logger.debug('Cache hit: %s', key)
        return hit

    value = producer()
    set_json(key, value, ttl)
    return value
