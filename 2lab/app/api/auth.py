from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.cruds.user import get_user_by_email, create_user
from app.core.security import create_access_token
from app.db.session import AsyncSessionLocal
import hashlib

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Функция для сохранения токена
from app.cruds.token import create_token
from app.models.token import Token

async def create_token(db: AsyncSession, user_id: int, access_token: str, token_type: str):
    new_token = Token(user_id=user_id, access_token=access_token, token_type=token_type)
    db.add(new_token)
    await db.commit()
    await db.refresh(new_token)
    return new_token


# В sign_up и login добавьте сохранение токена:
@router.post("/sign-up/", response_model=UserResponse)
async def sign_up(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    new_user = await create_user(db, user)
    token = create_access_token({"sub": new_user.email})

    # Сохраняем токен
    await create_token(db, new_user.id, token, "bearer")

    return UserResponse(id=new_user.id, email=new_user.email, token=token)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


@router.post("/login/", response_model=UserResponse)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    token = create_access_token({"sub": db_user.email})

    # Сохраняем токен
    await create_token(db, db_user.id, token, "bearer")

    return UserResponse(id=db_user.id, email=db_user.email, token=token)


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserResponse
from app.db.session import AsyncSessionLocal
from app.cruds.user import get_user_by_token

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
bearer_scheme = HTTPBearer()

@router.get("/users/me/", response_model=UserResponse)
async def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
):
    if not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing")

    token = credentials.credentials  # Получаем сам токен
    user = await get_user_by_token(token, db)
    return UserResponse(id=user.id, email=user.email, token=token)


