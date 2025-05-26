from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=4)


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True
