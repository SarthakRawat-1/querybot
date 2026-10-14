import json
from typing import Any, Iterator, Optional
from langgraph_sdk import get_sync_client
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

RESULT_KEYS = (
    'answer',
    'sql_query',
    'visualization',
    'visualization_reason',
    'chart_image_base64',
    'chart_generation_error',
    'insights',
    'insights_error',
    'formatted_table',
    'data_narrative',
    'results',
    'result_columns',
    'chart_spec',
    'error',
)


class LangGraphError(Exception):
    pass


def _client():
    api_url = settings.LANGGRAPH_API_URL
    if not api_url:
        raise LangGraphError('LANGGRAPH_API_URL is not configured.')
    return get_sync_client(api_key=settings.LANGSMITH_API_KEY, url=api_url)


def _to_dict(chunk: Any) -> Optional[dict]:
    data = getattr(chunk, 'data', None)
    if data is None:
        data = chunk

    if hasattr(data, '__dict__') and not isinstance(data, dict):
        data = vars(data)

    return data if isinstance(data, dict) and data else None


def _sse(payload: dict) -> str:
    return f'data: {json.dumps(payload, default=str)}\n\n'


def stream_run(
    question: str,
    dataset_uuid: str,
    history: Optional[list[dict]] = None,
    previous: Optional[dict] = None,
) -> Iterator[tuple[str, dict]]:
    accumulated: dict[str, Any] = {}
    assistant_id = settings.LANGGRAPH_ASSISTANT_ID or 'agent'

    payload: dict[str, Any] = {'question': question, 'uuid': dataset_uuid}
    if history:
        payload['history'] = history
    if previous:
        payload['previous'] = previous

    try:
        client = _client()
        thread = client.threads.create()
        thread_id = thread['thread_id']

        logger.info('Starting agent run on thread %s', thread_id)

        stream = client.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            input=payload,
            stream_mode='updates',
        )

        for chunk in stream:
            node_update = _to_dict(chunk)
            if not node_update:
                continue

            for value in node_update.values():
                if isinstance(value, dict):
                    for key in RESULT_KEYS:
                        if value.get(key) is not None:
                            accumulated[key] = value[key]

            yield _sse(node_update), accumulated

    except Exception as exc:
        logger.exception('Agent run failed')
        accumulated['error'] = str(exc)
        yield _sse({'error': f'The analysis failed: {exc}'}), accumulated
