import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (register tables)
from app.api.v1 import api_router
from app.core.config import settings
from app.core.db import Base, engine


log = logging.getLogger("shapater")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.secret_key == "change-me" or not settings.encryption_keys:
        log.warning("SECRET_KEY / ENCRYPTION_KEYS not set: using insecure dev defaults. Set both before going live.")
    if settings.auto_create_tables:  # dev convenience only; production uses `alembic upgrade head`
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}
