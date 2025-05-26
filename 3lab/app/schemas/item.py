from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
