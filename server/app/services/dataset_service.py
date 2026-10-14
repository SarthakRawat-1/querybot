import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.dataset_model import Dataset
from app.services import sqlite_service
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _parse_expiry(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


async def register_upload(
    db: Session,
    user_id: str,
    filename: str,
    content: bytes,
    content_type: str = 'application/octet-stream',
) -> Dataset:
    payload = await sqlite_service.upload_file(filename, content, content_type)

    tables = payload.get('tables') or []
    dataset = Dataset(
        external_uuid=uuid.UUID(payload['uuid']),
        user_id=uuid.UUID(str(user_id)),
        file_name=payload.get('fileName') or filename or 'dataset',
        size_bytes=int(payload.get('sizeBytes') or len(content)),
        table_count=len(tables),
        row_count=sum(int(table.get('rowCount') or 0) for table in tables),
        expires_at=_parse_expiry(payload.get('expiresAt')),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    logger.info(
        'Registered dataset %s for user %s (%d tables)',
        dataset.external_uuid,
        user_id,
        dataset.table_count,
    )
    return dataset


async def add_file(
    db: Session,
    dataset: Dataset,
    filename: str,
    content: bytes,
    content_type: str = 'application/octet-stream',
) -> dict:
    payload = await sqlite_service.add_file(str(dataset.external_uuid), filename, content, content_type)

    tables = payload.get('tables') or []
    dataset.table_count = len(tables)
    dataset.row_count = sum(int(table.get('rowCount') or 0) for table in tables)
    dataset.size_bytes = int(payload.get('sizeBytes') or dataset.size_bytes)
    dataset.touch()
    db.commit()
    db.refresh(dataset)

    logger.info(
        'Added %s to dataset %s (now %d tables)',
        payload.get('fileName'),
        dataset.external_uuid,
        dataset.table_count,
    )
    return payload


def get_owned_dataset(db: Session, user_id: str, dataset_uuid: str) -> Optional[Dataset]:
    return Dataset.find_for_user(db, dataset_uuid, user_id)


def list_datasets(db: Session, user_id: str) -> list[Dataset]:
    return Dataset.list_for_user(db, user_id)


def touch(db: Session, dataset: Dataset) -> None:
    dataset.touch()
    if dataset.expires_at:
        dataset.expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
    db.commit()


async def delete_dataset(db: Session, dataset: Dataset) -> None:
    await sqlite_service.delete_database(str(dataset.external_uuid))
    db.delete(dataset)
    db.commit()
