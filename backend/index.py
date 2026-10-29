"""Vercel entrypoint. Vercel looks for a FastAPI instance named `app` in index.py/app.py/server.py."""
from app.main import app  # noqa: F401
