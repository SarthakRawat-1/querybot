from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.conversation_model import Conversation, Message
from app.models.dashboard_model import TILE_SIZES, Dashboard, DashboardTile
from app.models.utils import to_uuid
from app.security import get_current_user_id
from app.utils.logging import get_logger
from app.utils.rate_limit import limiter
from app.utils.responses import error_response, success_response

logger = get_logger(__name__)

dashboard_bp = APIRouter(prefix='/api/dashboards', tags=['Dashboards'])
public_dashboard_bp = APIRouter(prefix='/api/public', tags=['Public Dashboards'])

TILE_VIEWS = ('chart', 'table', 'answer')
MAX_TILES = 30


class CreateDashboardRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class UpdateDashboardRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    shared: Optional[bool] = None


class AddTileRequest(BaseModel):
    messageId: str
    title: Optional[str] = None
    view: Optional[str] = 'chart'
    size: Optional[str] = 'medium'


class UpdateTileRequest(BaseModel):
    title: Optional[str] = None
    view: Optional[str] = None
    size: Optional[str] = None


class ReorderTilesRequest(BaseModel):
    tileIds: List[str]


def _title_for(message: Message) -> str:
    conversation = message.conversation
    if conversation and conversation.title:
        return conversation.title[:200]
    return (message.content or 'Result')[:200]


@dashboard_bp.get('')
async def list_dashboards(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dashboards = Dashboard.list_for_user(db, user_id)
    return success_response(
        'Dashboards retrieved successfully',
        {'dashboards': [dashboard.to_dict() for dashboard in dashboards]},
    )


@dashboard_bp.post('')
async def create_dashboard(
    request: Request,
    body: CreateDashboardRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    title = (body.title or '').strip() or 'Untitled dashboard'
    description = (body.description or '').strip()[:2000] or None

    dashboard = Dashboard(
        user_id=to_uuid(user_id),
        title=title[:200],
        description=description,
    )
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)

    logger.info('Dashboard created: %s', dashboard.id)
    return success_response('Dashboard created successfully', {'dashboard': dashboard.to_dict()}, 201)


@dashboard_bp.get('/{dashboard_id}')
async def get_dashboard(
    request: Request,
    dashboard_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dashboard = Dashboard.find_for_user(db, dashboard_id, user_id)
    if not dashboard:
        return error_response('Dashboard not found', 404)

    return success_response(
        'Dashboard retrieved successfully',
        {'dashboard': dashboard.to_dict(include_tiles=True)},
    )


@dashboard_bp.patch('/{dashboard_id}')
async def update_dashboard(
    request: Request,
    dashboard_id: str,
    body: UpdateDashboardRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dashboard = Dashboard.find_for_user(db, dashboard_id, user_id)
    if not dashboard:
        return error_response('Dashboard not found', 404)

    if body.title is not None:
        title = body.title.strip()
        if not title:
            return error_response('A title is required', 400)
        dashboard.title = title[:200]

    if body.description is not None:
        dashboard.description = body.description.strip()[:2000] or None

    if body.shared is not None:
        if body.shared:
            dashboard.enable_sharing()
            logger.info('Dashboard sharing enabled: %s', dashboard.id)
        else:
            dashboard.disable_sharing()
            logger.info('Dashboard sharing revoked: %s', dashboard.id)

    db.commit()
    db.refresh(dashboard)
    return success_response('Dashboard updated successfully', {'dashboard': dashboard.to_dict()})


@dashboard_bp.delete('/{dashboard_id}')
async def delete_dashboard(
    request: Request,
    dashboard_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dashboard = Dashboard.find_for_user(db, dashboard_id, user_id)
    if not dashboard:
        return error_response('Dashboard not found', 404)

    db.delete(dashboard)
    db.commit()
    return success_response('Dashboard deleted successfully')


@dashboard_bp.post('/{dashboard_id}/tiles')
async def add_tile(
    request: Request,
    dashboard_id: str,
    body: AddTileRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dashboard = Dashboard.find_for_user(db, dashboard_id, user_id)
    if not dashboard:
        return error_response('Dashboard not found', 404)

    if len(dashboard.tiles) >= MAX_TILES:
        return error_response(f'A dashboard holds at most {MAX_TILES} tiles', 400)

    message_id = to_uuid(body.messageId)
    if message_id is None:
        return error_response('A valid message identifier is required', 400)

    message = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Message.id == message_id, Conversation.user_id == to_uuid(user_id))
        .first()
    )
    if not message:
        return error_response('Result not found', 404)

    view = body.view if body.view in TILE_VIEWS else 'chart'
    size = body.size if body.size in TILE_SIZES else 'medium'

    if view == 'chart' and not message.chart_image_base64:
        view = 'table' if message.result_rows else 'answer'

    tile = DashboardTile(
        dashboard_id=dashboard.id,
        message_id=message.id,
        title=(body.title or '').strip()[:200] or _title_for(message),
        view=view,
        size=size,
        position=len(dashboard.tiles),
    )

    db.add(tile)
    db.commit()
    db.refresh(tile)

    return success_response('Pinned to the dashboard', {'tile': tile.to_dict()}, 201)


@dashboard_bp.patch('/{dashboard_id}/tiles/order')
async def reorder_tiles(
    request: Request,
    dashboard_id: str,
    body: ReorderTilesRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dashboard = Dashboard.find_for_user(db, dashboard_id, user_id)
    if not dashboard:
        return error_response('Dashboard not found', 404)

    order = body.tileIds
    by_id = {str(tile.id): tile for tile in dashboard.tiles}
    position = 0

    for tile_id in order:
        tile = by_id.pop(str(tile_id), None)
        if tile is not None:
            tile.position = position
            position += 1

    for tile in by_id.values():
        tile.position = position
        position += 1

    db.commit()
    db.refresh(dashboard)
    return success_response(
        'Tiles reordered successfully',
        {'dashboard': dashboard.to_dict(include_tiles=True)},
    )


@dashboard_bp.patch('/{dashboard_id}/tiles/{tile_id}')
async def update_tile(
    request: Request,
    dashboard_id: str,
    tile_id: str,
    body: UpdateTileRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dashboard = Dashboard.find_for_user(db, dashboard_id, user_id)
    if not dashboard:
        return error_response('Dashboard not found', 404)

    tile = next((t for t in dashboard.tiles if str(t.id) == str(tile_id)), None)
    if not tile:
        return error_response('Tile not found', 404)

    if body.title is not None:
        tile.title = body.title.strip()[:200] or tile.title
    if body.view in TILE_VIEWS:
        tile.view = body.view
    if body.size in TILE_SIZES:
        tile.size = body.size

    db.commit()
    db.refresh(tile)
    return success_response('Tile updated successfully', {'tile': tile.to_dict()})


@dashboard_bp.delete('/{dashboard_id}/tiles/{tile_id}')
async def remove_tile(
    request: Request,
    dashboard_id: str,
    tile_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    dashboard = Dashboard.find_for_user(db, dashboard_id, user_id)
    if not dashboard:
        return error_response('Dashboard not found', 404)

    tile = next((t for t in dashboard.tiles if str(t.id) == str(tile_id)), None)
    if not tile:
        return error_response('Tile not found', 404)

    survivors = sorted(
        (candidate for candidate in dashboard.tiles if candidate.id != tile.id),
        key=lambda candidate: candidate.position,
    )

    db.delete(tile)

    for index, remaining in enumerate(survivors):
        remaining.position = index

    db.commit()
    return success_response('Tile removed successfully')


@public_dashboard_bp.get('/dashboards/{token}')
@limiter.limit('60/hour')
async def get_shared_dashboard(request: Request, token: str, db: Session = Depends(get_db)):
    dashboard = Dashboard.find_by_share_token(db, token)
    if not dashboard:
        return error_response('This dashboard is not available', 404)

    return success_response(
        'Dashboard retrieved successfully',
        {'dashboard': dashboard.to_dict(include_tiles=True, public=True)},
    )
