from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    id: int
    email: str
    token: Optional[str] = None
