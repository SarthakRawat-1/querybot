import uuid
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import relationship, Session
from app.database import Base
from app.models.utils import to_uuid


class Dataset(Base):
    __tablename__ = 'datasets'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    external_uuid = sa.Column(sa.Uuid(as_uuid=True), unique=True, nullable=False, index=True)

    user_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    file_name = sa.Column(sa.String(255), nullable=False)
    size_bytes = sa.Column(sa.BigInteger, nullable=False, default=0)
    table_count = sa.Column(sa.Integer, nullable=False, default=0)
    row_count = sa.Column(sa.BigInteger, nullable=False, default=0)

    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_used_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

    user = relationship('User', back_populates='datasets')
    conversations = relationship(
        'Conversation',
        back_populates='dataset',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f'<Dataset {self.file_name} ({self.external_uuid})>'

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'uuid': str(self.external_uuid),
            'file_name': self.file_name,
            'size_bytes': self.size_bytes,
            'table_count': self.table_count,
            'row_count': self.row_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }

    def touch(self) -> None:
        self.last_used_at = datetime.now(timezone.utc)

    @classmethod
    def find_for_user(cls, db: Session, external_uuid: str, user_id: str) -> Optional['Dataset']:
        parsed_uuid = to_uuid(external_uuid)
        parsed_user = to_uuid(user_id)
        if parsed_uuid is None or parsed_user is None:
            return None

        return db.query(cls).filter_by(external_uuid=parsed_uuid, user_id=parsed_user).first()

    @classmethod
    def list_for_user(cls, db: Session, user_id: str, limit: int = 50) -> list['Dataset']:
        parsed_user = to_uuid(user_id)
        if parsed_user is None:
            return []

        return (
            db.query(cls)
            .filter_by(user_id=parsed_user)
            .order_by(cls.last_used_at.desc())
            .limit(limit)
            .all()
        )
