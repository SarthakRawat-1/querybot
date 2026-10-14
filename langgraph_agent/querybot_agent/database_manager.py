"""
Client for the SQLite dataset service.
"""
import logging
import os
from typing import Any, Optional

import requests

from querybot_agent.config import settings

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Raised when the dataset service cannot serve a request."""


class DatabaseManager:
    """Reads schema and executes queries against the dataset service."""

    def __init__(self, base_url: Optional[str] = None):
        target = (base_url or settings.sqlite_service_url).rstrip('/')
        if ('localhost:3001' in target or '127.0.0.1:3001' in target) and (
            os.path.exists('/.dockerenv') or os.environ.get('IN_DOCKER')
        ):
            target = 'http://sqlite-service:3001'
        self.base_url = target
        self._session = requests.Session()
        self._session.headers.update(settings.auth_headers)
        # Cache schema with a short TTL (10 seconds) so multiple nodes within a single
        # run share the fetched schema without roundtrips, but new table uploads across
        # runs are recognized immediately.
        self._schema_cache: dict[str, tuple[float, str]] = {}

    def _unwrap(self, response: requests.Response) -> Any:
        """Extract the payload from the service's response envelope."""
        try:
            body = response.json()
        except ValueError:
            raise DatabaseError('The dataset service returned a malformed response.')

        if not response.ok or body.get('success') is False:
            raise DatabaseError(body.get('message') or f'Request failed with status {response.status_code}')

        # The service wraps payloads in `data`; fall back to the body for
        # compatibility with any deployment still returning a bare object.
        return body.get('data', body)

    def get_schema(self, uuid: str, refresh: bool = False) -> str:
        """Return the prompt-facing schema description for a dataset."""
        import time

        now = time.time()
        if not refresh and uuid in self._schema_cache:
            cached_at, cached_schema = self._schema_cache[uuid]
            if now - cached_at < 10.0:
                return cached_schema

        try:
            response = self._session.get(
                f'{self.base_url}/get-schema/{uuid}',
                timeout=settings.request_timeout,
            )
            payload = self._unwrap(response)
        except requests.RequestException as exc:
            raise DatabaseError(f'Could not reach the dataset service: {exc}') from exc

        schema = payload.get('schema', '')
        if not schema:
            raise DatabaseError('The dataset service returned an empty schema.')

        self._schema_cache[uuid] = (now, schema)
        return schema

    def get_tables(self, uuid: str) -> list[dict]:
        """Return structured table metadata."""
        try:
            response = self._session.get(
                f'{self.base_url}/get-schema/{uuid}',
                timeout=settings.request_timeout,
            )
            return self._unwrap(response).get('tables', [])
        except requests.RequestException as exc:
            raise DatabaseError(f'Could not reach the dataset service: {exc}') from exc

    def execute_query(self, uuid: str, query: str) -> list[Any]:
        """
        Execute a read-only query and return rows as positional lists.

        The dataset service rejects anything that is not a single read-only
        statement, so a hallucinated UPDATE never reaches the database.
        """
        try:
            response = self._session.post(
                f'{self.base_url}/execute-query',
                json={'uuid': uuid, 'query': query, 'maxRows': settings.max_result_rows},
                timeout=settings.request_timeout,
            )
            payload = self._unwrap(response)
        except requests.RequestException as exc:
            raise DatabaseError(f'Could not reach the dataset service: {exc}') from exc

        if payload.get('truncated'):
            logger.warning(
                'Result truncated at %s rows for dataset %s', settings.max_result_rows, uuid
            )

        return payload.get('results', [])

    def execute_query_detailed(self, uuid: str, query: str) -> dict:
        """Execute a query and return the full payload, including column names."""
        try:
            response = self._session.post(
                f'{self.base_url}/execute-query',
                json={'uuid': uuid, 'query': query, 'maxRows': settings.max_result_rows},
                timeout=settings.request_timeout,
            )
            return self._unwrap(response)
        except requests.RequestException as exc:
            raise DatabaseError(f'Could not reach the dataset service: {exc}') from exc
