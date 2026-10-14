import uuid
from datetime import datetime, timezone
from typing import Any, Optional
import sqlalchemy as sa
from sqlalchemy.orm import relationship, Session
from app.database import Base
from app.models.utils import to_uuid


class Conversation(Base):
    __tablename__ = 'conversations'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    user_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    dataset_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('datasets.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    title = sa.Column(sa.String(200), nullable=False, default='New conversation')

    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship('User', back_populates='conversations')
    dataset = relationship('Dataset', back_populates='conversations')
    messages = relationship(
        'Message',
        back_populates='conversation',
        cascade='all, delete-orphan',
        passive_deletes=True,
        order_by='Message.created_at',
    )

    def __repr__(self) -> str:
        return f'<Conversation {self.title}>'

    def to_dict(self, include_messages: bool = False) -> dict:
        payload = {
            'id': str(self.id),
            'title': self.title,
            'dataset_id': str(self.dataset_id),
            'dataset_uuid': str(self.dataset.external_uuid) if self.dataset else None,
            'dataset_name': self.dataset.file_name if self.dataset else None,
            'message_count': len(self.messages),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_messages:
            payload['messages'] = [message.to_dict() for message in self.messages]
        return payload

    @staticmethod
    def build_title(question: str) -> str:
        cleaned = ' '.join((question or '').split())
        if not cleaned:
            return 'New conversation'
        return cleaned if len(cleaned) <= 80 else f'{cleaned[:77]}...'

    @classmethod
    def find_for_user(cls, db: Session, conversation_id: str, user_id: str) -> Optional['Conversation']:
        parsed_id = to_uuid(conversation_id)
        parsed_user = to_uuid(user_id)
        if parsed_id is None or parsed_user is None:
            return None
        return db.query(cls).filter_by(id=parsed_id, user_id=parsed_user).first()

    @classmethod
    def list_for_user(cls, db: Session, user_id: str, limit: int = 50) -> list['Conversation']:
        parsed_user = to_uuid(user_id)
        if parsed_user is None:
            return []

        return (
            db.query(cls)
            .filter_by(user_id=parsed_user)
            .order_by(cls.updated_at.desc())
            .limit(limit)
            .all()
        )


class Message(Base):
    __tablename__ = 'messages'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    conversation_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('conversations.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    role = sa.Column(sa.String(20), nullable=False)
    content = sa.Column(sa.Text, nullable=False, default='')

    sql_query = sa.Column(sa.Text, nullable=True)
    visualization = sa.Column(sa.String(50), nullable=True)
    chart_spec = sa.Column(sa.JSON, nullable=True)
    insights = sa.Column(sa.Text, nullable=True)
    data_narrative = sa.Column(sa.Text, nullable=True)
    formatted_table = sa.Column(sa.Text, nullable=True)
    chart_image_base64 = sa.Column(sa.Text, nullable=True)
    result_rows = sa.Column(sa.JSON, nullable=True)
    result_columns = sa.Column(sa.JSON, nullable=True)
    error = sa.Column(sa.Text, nullable=True)
    duration_ms = sa.Column(sa.Integer, nullable=True)

    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    conversation = relationship('Conversation', back_populates='messages')

    def __repr__(self) -> str:
        return f'<Message {self.role}>'

    def to_dict(self) -> dict:
        payload: dict[str, Any] = {
            'id': str(self.id),
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        optional = {
            'sql_query': self.sql_query,
            'visualization': self.visualization,
            'chart_spec': self.chart_spec,
            'insights': self.insights,
            'data_narrative': self.data_narrative,
            'formatted_table': self.formatted_table,
            'chart_image_base64': self.chart_image_base64,
            'result_rows': self.result_rows,
            'result_columns': self.result_columns,
            'error': self.error,
            'duration_ms': self.duration_ms,
        }
        payload.update({key: value for key, value in optional.items() if value is not None})
        return payload
