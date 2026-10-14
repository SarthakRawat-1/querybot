import uuid
from fastapi import Depends, Request
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user_model import User

PUBLIC_USER_ID = uuid.UUID('a0000000-0000-0000-0000-000000000001')
PUBLIC_USER_EMAIL = 'public-workspace@querybot.local'


def ensure_public_user(db: Session) -> User:
    """Create the shared workspace owner used by anonymous application access."""
    user = User.find_by_id(db, PUBLIC_USER_ID)
    if user:
        return user

    user = User(
        id=PUBLIC_USER_ID,
        fullname='Public Workspace',
        email=PUBLIC_USER_EMAIL,
        password_hash='disabled-public-workspace-account',
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def get_current_user_id(
    request: Request,
    db: Session = Depends(get_db),
) -> str:
    """Return the shared workspace identity; application access is anonymous."""
    user = ensure_public_user(db)
    user_id = str(user.id)
    request.state.user_id = user_id
    return user_id
