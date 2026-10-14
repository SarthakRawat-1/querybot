import json
import logging
import sys
from datetime import datetime, timezone
from app.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    use_json = not settings.DEBUG

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter()
        if use_json
        else logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    )

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)

    root.addHandler(handler)
    root.setLevel(level)

    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
