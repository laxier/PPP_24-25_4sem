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

@router.post("/sign-up/", response_model=UserResponse)
async def sign_up(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    new_user = await create_user(db, user)
    token = create_access_token({"sub": new_user.email})
    return UserResponse(id=new_user.id, email=new_user.email, token=token)

@router.post("/login/", response_model=UserResponse)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, user.email)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    # Проверка пароля (аналогичная логика, как в create_user)
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    if hashed_password != db_user.hashed_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    token = create_access_token({"sub": db_user.email})
    return UserResponse(id=db_user.id, email=db_user.email, token=token)

@router.get("/users/me/", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(lambda: None)):
    # Здесь должна быть логика извлечения текущего пользователя из токена
    # Для примера возвращаем заглушку (в реальном проекте используй OAuth2PasswordBearer и декодирование JWT)
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
