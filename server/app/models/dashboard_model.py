import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import relationship, Session
from app.database import Base
from app.models.utils import to_uuid

TILE_SIZES = ('small', 'medium', 'large', 'full')
TILE_SIZE_COLUMNS = {'small': 3, 'medium': 4, 'large': 6, 'full': 12}


class Dashboard(Base):
    __tablename__ = 'dashboards'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    user_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    title = sa.Column(sa.String(200), nullable=False, default='Untitled dashboard')
    description = sa.Column(sa.Text, nullable=True)

    share_token = sa.Column(sa.String(64), unique=True, nullable=True, index=True)
    shared_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

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

    user = relationship('User', back_populates='dashboards')
    tiles = relationship(
        'DashboardTile',
        back_populates='dashboard',
        cascade='all, delete-orphan',
        passive_deletes=True,
        order_by='DashboardTile.position',
    )

    def __repr__(self) -> str:
        return f'<Dashboard {self.title}>'

    @property
    def is_shared(self) -> bool:
        return self.share_token is not None

    def enable_sharing(self) -> str:
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(32)
            self.shared_at = datetime.now(timezone.utc)
        return self.share_token

    def disable_sharing(self) -> None:
        self.share_token = None
        self.shared_at = None

    def to_dict(self, include_tiles: bool = False, public: bool = False) -> dict:
        payload = {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'tile_count': len(self.tiles),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if not public:
            payload['is_shared'] = self.is_shared
            payload['share_token'] = self.share_token
            payload['shared_at'] = self.shared_at.isoformat() if self.shared_at else None

        if include_tiles:
            payload['tiles'] = [tile.to_dict(public=public) for tile in self.tiles]

        return payload

    @classmethod
    def find_for_user(cls, db: Session, dashboard_id: str, user_id: str) -> Optional['Dashboard']:
        parsed_id = to_uuid(dashboard_id)
        parsed_user = to_uuid(user_id)
        if parsed_id is None or parsed_user is None:
            return None
        return db.query(cls).filter_by(id=parsed_id, user_id=parsed_user).first()

    @classmethod
    def find_by_share_token(cls, db: Session, token: str) -> Optional['Dashboard']:
        if not token or len(token) > 64:
            return None
        return db.query(cls).filter_by(share_token=token).first()

    @classmethod
    def list_for_user(cls, db: Session, user_id: str, limit: int = 50) -> list['Dashboard']:
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


class DashboardTile(Base):
    __tablename__ = 'dashboard_tiles'

    id = sa.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    dashboard_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('dashboards.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    message_id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('messages.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    title = sa.Column(sa.String(200), nullable=False, default='')
    view = sa.Column(sa.String(20), nullable=False, default='chart')
    size = sa.Column(sa.String(20), nullable=False, default='medium')
    position = sa.Column(sa.Integer, nullable=False, default=0)

    created_at = sa.Column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    dashboard = relationship('Dashboard', back_populates='tiles')
    message = relationship('Message')

    def __repr__(self) -> str:
        return f'<DashboardTile {self.title[:30]}>'

    def to_dict(self, public: bool = False) -> dict:
        payload = {
            'id': str(self.id),
            'title': self.title,
            'view': self.view,
            'size': self.size,
            'columns': TILE_SIZE_COLUMNS.get(self.size, 4),
            'position': self.position,
        }

        message = self.message
        if message:
            payload['answer'] = message.content
            payload['chart_image_base64'] = message.chart_image_base64
            payload['result_rows'] = message.result_rows
            payload['result_columns'] = message.result_columns
            payload['visualization'] = message.visualization
            payload['created_at'] = message.created_at.isoformat() if message.created_at else None

            if not public:
                payload['sql_query'] = message.sql_query
                payload['message_id'] = str(message.id)

        return payload
