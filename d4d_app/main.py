from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from d4d_app.database import Base, engine
from d4d_app.routers.web import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="D4D Leon CRM", lifespan=lifespan)
app.include_router(router)
