from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.item import Item
from app.schemas.item import ItemCreate


async def create_item(db: AsyncSession, owner_id: int, data: ItemCreate) -> Item:
    item = Item(**data.model_dump(), owner_id=owner_id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def list_items(db: AsyncSession, owner_id: int) -> list[Item]:
    res = await db.execute(select(Item).where(Item.owner_id == owner_id))
    return list(res.scalars())
