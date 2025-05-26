from fastapi import FastAPI
from app.api import api_router
from app.db.session import engine
from app.db.base import Base

app = FastAPI(title="Bruteforce-API")
app.include_router(api_router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
