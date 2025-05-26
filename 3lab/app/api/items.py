from fastapi import APIRouter
from app.api.deps import DBSession, CurrentUser

from app.schemas.item import ItemCreate, ItemRead
from app.cruds.item import create_item, list_items

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=ItemRead, status_code=201)
async def add_item(data: ItemCreate, db: DBSession, user: CurrentUser):
    return await create_item(db, owner_id=user.id, data=data)


@router.get("", response_model=list[ItemRead])
async def my_items(db: DBSession, user: CurrentUser):
    return await list_items(db, owner_id=user.id)
