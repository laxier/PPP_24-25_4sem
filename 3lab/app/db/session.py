from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.core.settings import get_settings

settings = get_settings()

engine = create_async_engine(settings.db_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False, autocommit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
