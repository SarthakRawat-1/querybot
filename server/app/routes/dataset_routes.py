import os
from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.security import get_current_user_id
from app.services import dataset_service, sqlite_service
from app.services.sqlite_service import SqliteServiceError
from app.utils import cache
from app.utils.logging import get_logger
from app.utils.rate_limit import limiter
from app.utils.responses import error_response, success_response

logger = get_logger(__name__)

dataset_bp = APIRouter(prefix='/api/datasets', tags=['Datasets'])

ALLOWED_EXTENSIONS = {'.csv', '.sqlite', '.db', '.sql'}


def _dataset_cache_prefix(dataset_uuid: str) -> str:
    return cache.build_key('dataset', dataset_uuid)


@dataset_bp.get('')
async def list_datasets(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    datasets = dataset_service.list_datasets(db, user_id)
    return success_response(
        'Datasets retrieved successfully',
        {'datasets': [dataset.to_dict() for dataset in datasets]},
    )


@dataset_bp.post('')
@limiter.limit(lambda: settings.RATELIMIT_UPLOAD)
async def upload_dataset(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not file or not file.filename:
        return error_response('No file was uploaded', 400)

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return error_response(
            f'Unsupported file type. Accepted formats: {", ".join(sorted(ALLOWED_EXTENSIONS))}',
            400,
        )

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_BYTES:
        return error_response('The uploaded file is too large', 413)

    try:
        dataset = await dataset_service.register_upload(
            db,
            user_id,
            filename=filename,
            content=content,
            content_type=file.content_type or 'application/octet-stream',
        )
    except SqliteServiceError as exc:
        logger.warning('Upload rejected by dataset service: %s', exc.message)
        return error_response(exc.message, exc.status_code)

    return success_response('File uploaded successfully', {'dataset': dataset.to_dict()}, 201)


@dataset_bp.get('/{dataset_uuid}/schema')
async def get_schema(
    request: Request,
    dataset_uuid: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dataset = dataset_service.get_owned_dataset(db, user_id, dataset_uuid)
    if not dataset:
        return error_response('Dataset not found', 404)

    key = cache.build_key('dataset', str(dataset.external_uuid), 'schema')

    try:
        payload = cache.get_json(key)
        if payload is None:
            payload = await sqlite_service.get_schema(str(dataset.external_uuid))
            cache.set_json(key, payload, settings.SCHEMA_CACHE_TTL)
    except SqliteServiceError as exc:
        return error_response(exc.message, exc.status_code)

    return success_response(
        'Schema retrieved successfully',
        {'tables': payload.get('tables', []), 'dataset': dataset.to_dict()},
    )


@dataset_bp.post('/{dataset_uuid}/files')
@limiter.limit('30/hour')
async def add_file(
    request: Request,
    dataset_uuid: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dataset = dataset_service.get_owned_dataset(db, user_id, dataset_uuid)
    if not dataset:
        return error_response('Dataset not found', 404)

    if not file or not file.filename:
        return error_response('No file was uploaded', 400)

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return error_response(
            f'Unsupported file type. Accepted formats: {", ".join(sorted(ALLOWED_EXTENSIONS))}',
            400,
        )

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_BYTES:
        return error_response('The uploaded file is too large', 413)

    try:
        payload = await dataset_service.add_file(
            db,
            dataset,
            filename=filename,
            content=content,
            content_type=file.content_type or 'application/octet-stream',
        )
    except SqliteServiceError as exc:
        logger.warning('Could not add the file: %s', exc.message)
        return error_response(exc.message, exc.status_code)

    cache.delete_prefix(_dataset_cache_prefix(str(dataset.external_uuid)))

    return success_response(
        f'Added {len(payload.get("addedTables") or [])} table(s)',
        {'dataset': dataset.to_dict(), 'addedTables': payload.get('addedTables') or []},
        201,
    )


@dataset_bp.get('/{dataset_uuid}/profile')
async def profile_dataset(
    request: Request,
    dataset_uuid: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dataset = dataset_service.get_owned_dataset(db, user_id, dataset_uuid)
    if not dataset:
        return error_response('Dataset not found', 404)

    key = cache.build_key('dataset', str(dataset.external_uuid), 'profile')

    try:
        payload = cache.get_json(key)
        if payload is None:
            payload = await sqlite_service.profile_dataset(str(dataset.external_uuid))
            cache.set_json(key, payload, settings.SCHEMA_CACHE_TTL)
    except SqliteServiceError as exc:
        return error_response(exc.message, exc.status_code)

    return success_response('Profile retrieved successfully', payload)


@dataset_bp.get('/{dataset_uuid}/preview/{table}')
async def preview_table(
    request: Request,
    dataset_uuid: str,
    table: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dataset = dataset_service.get_owned_dataset(db, user_id, dataset_uuid)
    if not dataset:
        return error_response('Dataset not found', 404)

    key = cache.build_key('dataset', str(dataset.external_uuid), 'preview', table)

    try:
        payload = cache.get_json(key)
        if payload is None:
            payload = await sqlite_service.preview_table(str(dataset.external_uuid), table)
            cache.set_json(key, payload, settings.PREVIEW_CACHE_TTL)
    except SqliteServiceError as exc:
        return error_response(exc.message, exc.status_code)

    return success_response('Preview retrieved successfully', payload)


@dataset_bp.delete('/{dataset_uuid}')
async def delete_dataset(
    request: Request,
    dataset_uuid: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dataset = dataset_service.get_owned_dataset(db, user_id, dataset_uuid)
    if not dataset:
        return error_response('Dataset not found', 404)

    external_uuid = str(dataset.external_uuid)

    try:
        await dataset_service.delete_dataset(db, dataset)
    except SqliteServiceError as exc:
        return error_response(exc.message, exc.status_code)

    cache.delete_prefix(_dataset_cache_prefix(external_uuid))
    return success_response('Dataset deleted successfully')
