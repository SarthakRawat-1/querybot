import json
import time
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal, get_db
from app.models.conversation_model import Conversation, Message
from app.models.utils import to_uuid
from app.security import get_current_user_id
from app.services import dataset_service, langgraph_service, sqlite_service
from app.services.sqlite_service import SqliteServiceError
from app.utils.logging import get_logger
from app.utils.rate_limit import limiter
from app.utils.responses import error_response, success_response

logger = get_logger(__name__)

langgraph_bp = APIRouter(prefix='/api/langgraph', tags=['LangGraph'])

HISTORY_TURN_LIMIT = 6
PREVIOUS_ANSWER_CHARS = 1200


class RunAgentRequest(BaseModel):
    question: Optional[str] = None
    databaseUuid: Optional[str] = None
    conversationId: Optional[str] = None


class QueryRequest(BaseModel):
    query: Optional[str] = None
    databaseUuid: Optional[str] = None


def _history_for(conversation: Conversation) -> list[dict]:
    turns = []
    for message in conversation.messages[-HISTORY_TURN_LIMIT:]:
        entry = {'role': message.role, 'content': message.content}
        if message.sql_query:
            entry['sql_query'] = message.sql_query
        turns.append(entry)
    return turns


def _previous_result(conversation: Conversation) -> dict | None:
    messages = list(conversation.messages)
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        if message.role != 'assistant' or not message.sql_query:
            continue

        question = next(
            (
                earlier.content
                for earlier in reversed(messages[:index])
                if earlier.role == 'user'
            ),
            None,
        )

        return {
            'question': question,
            'answer': (message.content or '')[:PREVIOUS_ANSWER_CHARS],
            'sql_query': message.sql_query,
            'visualization': message.visualization,
            'chart_spec': message.chart_spec or {},
            'insights': message.insights,
            'data_narrative': message.data_narrative,
        }

    return None


def _persist_assistant_message(conversation_id: str, result: dict, duration_ms: int) -> str | None:
    if not result:
        return None

    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter_by(id=to_uuid(conversation_id)).first()
        if not conversation:
            return None

        rows = result.get('results')
        message = Message(
            conversation_id=conversation.id,
            role='error' if result.get('error') and not result.get('answer') else 'assistant',
            content=result.get('answer') or result.get('error') or '',
            sql_query=result.get('sql_query'),
            visualization=result.get('visualization'),
            chart_spec=result.get('chart_spec') or None,
            insights=result.get('insights'),
            data_narrative=result.get('data_narrative'),
            formatted_table=result.get('formatted_table'),
            chart_image_base64=result.get('chart_image_base64'),
            result_rows=rows if isinstance(rows, list) else None,
            result_columns=result.get('result_columns'),
            error=result.get('error'),
            duration_ms=duration_ms,
        )
        conversation.updated_at = datetime.now(timezone.utc)
        db.add(message)
        db.commit()
        db.refresh(message)
        return str(message.id)
    finally:
        db.close()


@langgraph_bp.post('/run')
@limiter.limit(lambda: settings.RATELIMIT_ANALYSIS)
async def run_agent(
    request: Request,
    body: RunAgentRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    question = (body.question or '').strip()
    dataset_uuid = body.databaseUuid
    conversation_id = body.conversationId

    if not question:
        return error_response('A question is required', 400)
    if len(question) > 2000:
        return error_response('That question is too long (2000 character maximum)', 400)
    if not dataset_uuid:
        return error_response('Upload a dataset before asking a question', 400)

    dataset = dataset_service.get_owned_dataset(db, user_id, dataset_uuid)
    if not dataset:
        logger.warning('User %s attempted to query dataset %s they do not own', user_id, dataset_uuid)
        return error_response('Dataset not found', 404)

    if conversation_id:
        conversation = Conversation.find_for_user(db, conversation_id, user_id)
        if not conversation:
            return error_response('Conversation not found', 404)
        if str(conversation.dataset_id) != str(dataset.id):
            return error_response('That conversation belongs to a different dataset', 400)
    else:
        conversation = Conversation(
            user_id=dataset.user_id,
            dataset_id=dataset.id,
            title=Conversation.build_title(question),
        )
        db.add(conversation)
        db.flush()

    history = _history_for(conversation)
    previous = _previous_result(conversation)

    db.add(Message(conversation_id=conversation.id, role='user', content=question))
    dataset.touch()
    db.commit()

    conversation_uuid = str(conversation.id)
    dataset_ref = str(dataset.external_uuid)
    started = time.monotonic()

    async def event_generator():
        accumulated: dict = {}
        message_id: str | None = None

        try:
            for event, result in langgraph_service.stream_run(
                question, dataset_ref, history, previous
            ):
                accumulated = result
                yield event
        finally:
            try:
                duration_ms = int((time.monotonic() - started) * 1000)
                message_id = _persist_assistant_message(conversation_uuid, accumulated, duration_ms)
            except Exception:
                logger.exception('Could not persist assistant message')

        yield 'data: ' + json.dumps(
            {'done': True, 'conversationId': conversation_uuid, 'messageId': message_id}
        ) + '\n\n'

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache, no-transform',
            'X-Accel-Buffering': 'no',
            'X-Conversation-Id': conversation_uuid,
        },
    )


@langgraph_bp.post('/query')
@limiter.limit(lambda: settings.RATELIMIT_QUERY)
async def run_raw_query(
    request: Request,
    body: QueryRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    query = (body.query or '').strip()
    dataset_uuid = body.databaseUuid

    if not query:
        return error_response('A SQL query is required', 400)
    if not dataset_uuid:
        return error_response('A dataset is required', 400)

    dataset = dataset_service.get_owned_dataset(db, user_id, dataset_uuid)
    if not dataset:
        return error_response('Dataset not found', 404)

    try:
        result = await sqlite_service.execute_query(str(dataset.external_uuid), query)
    except SqliteServiceError as exc:
        return error_response(exc.message, exc.status_code)

    dataset_service.touch(db, dataset)
    return success_response('Query executed successfully', result)


@langgraph_bp.get('/health')
async def health_check():
    return success_response(
        'LangGraph integration status',
        {
            'api_url_set': bool(settings.LANGGRAPH_API_URL),
            'api_key_set': bool(settings.LANGSMITH_API_KEY),
            'assistant_id': settings.LANGGRAPH_ASSISTANT_ID,
        },
    )
