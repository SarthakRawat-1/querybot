from typing import Any, Optional
from datetime import datetime, timezone
from fastapi.responses import JSONResponse


def success_response(
    message: str,
    data: Optional[Any] = None,
    status_code: int = 200,
    headers: Optional[dict[str, str]] = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        'success': True,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    if data is not None:
        payload['data'] = data
    return JSONResponse(status_code=status_code, content=payload, headers=headers)


def error_response(
    message: str,
    status_code: int = 400,
    errors: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
    data: Optional[Any] = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        'success': False,
        'message': message,
        'data': data,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    if errors is not None:
        payload['errors'] = errors
    return JSONResponse(status_code=status_code, content=payload, headers=headers)


def validation_error_response(errors: dict[str, Any]) -> JSONResponse:
    return error_response('Validation failed', 422, errors)


def unauthorized_response(message: str = 'Unauthorized access') -> JSONResponse:
    return error_response(message, 401)


def forbidden_response(message: str = 'Forbidden') -> JSONResponse:
    return error_response(message, 403)


def not_found_response(message: str = 'Resource not found') -> JSONResponse:
    return error_response(message, 404)


def conflict_response(message: str = 'Resource conflict') -> JSONResponse:
    return error_response(message, 409)


def internal_server_error_response(message: str = 'Internal server error') -> JSONResponse:
    return error_response(message, 500)
