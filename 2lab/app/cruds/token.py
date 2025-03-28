from app.models.token import Token  # Импорт модели Token
from sqlalchemy.ext.asyncio import AsyncSession

async def create_token(db: AsyncSession, user_id: int, access_token: str, token_type: str):
    new_token = Token(user_id=user_id, access_token=access_token, token_type=token_type)
    db.add(new_token)
    await db.commit()
    await db.refresh(new_token)
    return new_token
