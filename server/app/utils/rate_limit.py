from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _rate_limit_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=["600/hour"],
    storage_uri=settings.REDIS_URL or "memory://",
    strategy="fixed-window",
    headers_enabled=True,
)
