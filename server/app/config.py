import os
from datetime import timedelta
from typing import List
from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, ''))
    except ValueError:
        return default


class Settings:
    DEBUG: bool = os.environ.get('DEBUG', 'true').lower() not in ('false', '0', 'no', 'off')
    TESTING: bool = os.environ.get('TESTING', '').lower() == 'true'

    DATABASE_URL: str = os.environ.get('DATABASE_URL') or 'sqlite:///querybot.db'

    CORS_ORIGINS: List[str] = _split_csv(os.environ.get('CORS_ORIGINS')) or [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:8080',
    ]

    LANGSMITH_API_KEY: str | None = os.environ.get('LANGSMITH_API_KEY')
    LANGGRAPH_API_URL: str = os.environ.get('LANGGRAPH_API_URL', 'http://localhost:8000')
    LANGGRAPH_ASSISTANT_ID: str = os.environ.get('LANGGRAPH_ASSISTANT_ID', 'agent')

    SQLITE_SERVICE_URL: str = os.environ.get('SQLITE_SERVICE_URL', 'http://localhost:3001')
    SERVICE_TOKEN: str = os.environ.get('SERVICE_TOKEN', '')
    SQLITE_SERVICE_TIMEOUT: int = _int_env('SQLITE_SERVICE_TIMEOUT', 120)

    MAX_UPLOAD_BYTES: int = _int_env('MAX_UPLOAD_BYTES', 100 * 1024 * 1024)
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    REDIS_URL: str | None = os.environ.get('REDIS_URL')

    SCHEMA_CACHE_TTL: int = _int_env('SCHEMA_CACHE_TTL', 4 * 60 * 60)
    PREVIEW_CACHE_TTL: int = _int_env('PREVIEW_CACHE_TTL', 30 * 60)

    RATELIMIT_ANALYSIS: str = os.environ.get('RATELIMIT_ANALYSIS', '20 per hour;5 per minute')
    RATELIMIT_QUERY: str = os.environ.get('RATELIMIT_QUERY', '120 per hour')
    RATELIMIT_UPLOAD: str = os.environ.get('RATELIMIT_UPLOAD', '30 per hour')


settings = Settings()
