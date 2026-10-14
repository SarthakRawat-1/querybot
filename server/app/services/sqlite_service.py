from typing import Any, Optional
import httpx
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SqliteServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _base_url() -> str:
    return settings.SQLITE_SERVICE_URL.rstrip('/')


def _headers() -> dict[str, str]:
    token = settings.SERVICE_TOKEN
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
        headers['X-Service-Token'] = token
    return headers


def _timeout() -> float:
    return float(settings.SQLITE_SERVICE_TIMEOUT)


def _unwrap(response: httpx.Response) -> Any:
    try:
        body = response.json()
    except ValueError:
        raise SqliteServiceError('The dataset service returned a malformed response.')

    if response.is_error or body.get('success') is False:
        message = body.get('message') or 'The dataset service rejected the request.'
        raise SqliteServiceError(message, status_code=response.status_code)

    return body.get('data', body)


async def _request(method: str, path: str, **kwargs: Any) -> Any:
    url = f'{_base_url()}{path}'
    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            response = await client.request(
                method,
                url,
                headers=_headers(),
                **kwargs,
            )
    except httpx.TimeoutException:
        logger.error('Dataset service timed out: %s %s', method, path)
        raise SqliteServiceError('The dataset service timed out.', status_code=504)
    except httpx.RequestError as exc:
        logger.error('Dataset service unreachable: %s', exc)
        raise SqliteServiceError('The dataset service is unavailable.', status_code=503)

    return _unwrap(response)


async def upload_file(filename: str, content: bytes, content_type: str = 'application/octet-stream') -> dict:
    files = {'file': (filename, content, content_type)}
    return await _request('POST', '/upload-file', files=files)


async def add_file(dataset_uuid: str, filename: str, content: bytes, content_type: str = 'application/octet-stream') -> dict:
    files = {'file': (filename, content, content_type)}
    return await _request('POST', f'/databases/{dataset_uuid}/files', files=files)


async def get_schema(dataset_uuid: str) -> dict:
    return await _request('GET', f'/get-schema/{dataset_uuid}')


async def execute_query(dataset_uuid: str, query: str, max_rows: Optional[int] = None) -> dict:
    payload: dict[str, Any] = {'uuid': dataset_uuid, 'query': query}
    if max_rows is not None:
        payload['maxRows'] = max_rows
    return await _request('POST', '/execute-query', json=payload)


async def preview_table(dataset_uuid: str, table: str) -> dict:
    return await _request('GET', f'/databases/{dataset_uuid}/preview/{table}')


async def profile_dataset(dataset_uuid: str) -> dict:
    return await _request('GET', f'/databases/{dataset_uuid}/profile')


async def delete_database(dataset_uuid: str) -> None:
    try:
        await _request('DELETE', f'/databases/{dataset_uuid}')
    except SqliteServiceError as exc:
        if exc.status_code != 404:
            raise
        logger.info('Dataset %s was already absent from the dataset service', dataset_uuid)


async def database_exists(dataset_uuid: str) -> bool:
    try:
        await _request('GET', f'/databases/{dataset_uuid}')
        return True
    except SqliteServiceError:
        return False
