from fastapi import APIRouter

from app.api.v1 import auth, clients, dashboard, leads, matches, properties, requirements

api_router = APIRouter(prefix="/api/v1")
for module in (auth, properties, clients, requirements, matches, leads, dashboard):
    api_router.include_router(module.router)
