import os
from contextlib import contextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.config import settings
from app.database import SessionLocal
from app.routes.conversation_routes import conversation_bp
from app.routes.dashboard_routes import dashboard_bp, public_dashboard_bp
from app.routes.dataset_routes import dataset_bp
from app.routes.langgraph_routes import langgraph_bp
from app.utils.cache import init_cache
from app.utils.logging import configure_logging, get_logger
from app.utils.rate_limit import limiter
from app.utils.responses import error_response

logger = get_logger(__name__)


class AppConfig(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in dir(settings):
            if not key.startswith('_') and key.isupper():
                self[key] = getattr(settings, key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if hasattr(settings, key):
            setattr(settings, key, value)

    def __getitem__(self, key):
        if hasattr(settings, key):
            return getattr(settings, key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        if hasattr(settings, key):
            return getattr(settings, key)
        return super().get(key, default)


def create_app(config_name: str | None = None) -> FastAPI:
    if config_name:
        settings.TESTING = config_name == 'testing'

    configure_logging()
    init_cache()

    app_dir = str(Path(__file__).resolve().parent)
    app = FastAPI(
        title="QueryBot API",
        docs_url=None,
        redoc_url=None,
        root_path=app_dir,
    )

    app.config = AppConfig()
    app.state.limiter = limiter

    @contextmanager
    def _app_context():
        yield

    app.app_context = _app_context

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-CSRF-TOKEN"],
        expose_headers=["X-Conversation-Id"],
    )

    app.include_router(dataset_bp)
    app.include_router(conversation_bp)
    app.include_router(dashboard_bp)
    app.include_router(public_dashboard_bp)
    app.include_router(langgraph_bp)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return error_response('You are sending requests too quickly. Please slow down.', 429)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return error_response('Validation failed', 400, data={'errors': exc.errors()})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if exc.status_code == 404:
            return error_response('Resource not found', 404)
        if exc.status_code == 405:
            return error_response('Method not allowed', 405)
        if exc.status_code == 401:
            return error_response(exc.detail or 'Unauthorized access', 401)
        if exc.status_code == 403:
            return error_response(exc.detail or 'Forbidden', 403)
        return error_response(str(exc.detail), exc.status_code)

    @app.get('/')
    def index():
        return {'message': 'QueryBot API', 'status': 'running', 'version': '1.0.0'}

    @app.get('/health')
    def health():
        db = SessionLocal()
        try:
            db.execute(text('SELECT 1'))
            return {'status': 'healthy', 'database': 'ok'}
        except Exception as exc:
            logger.warning('Health check failed: %s', exc)
            return JSONResponse(status_code=503, content={'status': 'unhealthy', 'database': 'unavailable'})
        finally:
            db.close()

    return app


app = create_app()
