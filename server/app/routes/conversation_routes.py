from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.conversation_model import Conversation
from app.security import get_current_user_id
from app.utils.responses import error_response, success_response

conversation_bp = APIRouter(prefix='/api/conversations', tags=['Conversations'])


class RenameConversationRequest(BaseModel):
    title: str


@conversation_bp.get('')
async def list_conversations(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    conversations = Conversation.list_for_user(db, user_id)
    return success_response(
        'Conversations retrieved successfully',
        {'conversations': [conversation.to_dict() for conversation in conversations]},
    )


@conversation_bp.get('/{conversation_id}')
async def get_conversation(
    request: Request,
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    conversation = Conversation.find_for_user(db, conversation_id, user_id)
    if not conversation:
        return error_response('Conversation not found', 404)

    return success_response(
        'Conversation retrieved successfully',
        {'conversation': conversation.to_dict(include_messages=True)},
    )


@conversation_bp.patch('/{conversation_id}')
async def rename_conversation(
    request: Request,
    conversation_id: str,
    body: RenameConversationRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    conversation = Conversation.find_for_user(db, conversation_id, user_id)
    if not conversation:
        return error_response('Conversation not found', 404)

    title = body.title.strip()
    if not title:
        return error_response('A title is required', 400)

    conversation.title = title[:200]
    db.commit()
    db.refresh(conversation)

    return success_response('Conversation renamed successfully', {'conversation': conversation.to_dict()})


@conversation_bp.delete('/{conversation_id}')
async def delete_conversation(
    request: Request,
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    conversation = Conversation.find_for_user(db, conversation_id, user_id)
    if not conversation:
        return error_response('Conversation not found', 404)

    db.delete(conversation)
    db.commit()

    return success_response('Conversation deleted successfully')
