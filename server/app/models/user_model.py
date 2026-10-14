import uuid
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import relationship, Session
from app.database import Base


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    fullname = sa.Column(sa.String(100), nullable=False)
    email = sa.Column(sa.String(255), unique=True, nullable=False, index=True)
    password_hash = sa.Column(sa.String(255), nullable=False)

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

    is_active = sa.Column(sa.Boolean, default=True, nullable=False)

    datasets = relationship('Dataset', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)
    conversations = relationship('Conversation', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)
    dashboards = relationship('Dashboard', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)

    def __init__(self, fullname: str, email: str, password_hash: str, **kwargs):
        super().__init__(**kwargs)
        self.fullname = fullname
        self.email = email.lower().strip()
        self.password_hash = password_hash

    def __repr__(self) -> str:
        return f'<User {self.email}>'

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'fullname': self.fullname,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
        }

    @classmethod
    def find_by_email(cls, db: Session, email: str) -> Optional['User']:
        return db.query(cls).filter_by(email=email.lower().strip()).first()

    @classmethod
    def find_by_id(cls, db: Session, user_id: str) -> Optional['User']:
        try:
            parsed = uuid.UUID(str(user_id))
        except (ValueError, AttributeError, TypeError):
            return None
        return db.query(cls).filter_by(id=parsed).first()