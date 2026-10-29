from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Shapater CRM"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/shapater"
    migration_database_url: str | None = None  # owner/admin URL used only by Alembic
    auto_create_tables: bool = False  # dev/test only; prod uses Alembic
    # Fernet keys, comma separated. First encrypts; all can decrypt (key rotation). Generate with:
    # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_keys: str | None = None
    secret_key: str = "change-me"
    access_token_minutes: int = 60 * 12
    match_threshold: int = 70
    login_max_failures: int = 5
    login_window_seconds: int = 900
    cors_origins: list[str] = ["http://localhost:3000"]
    default_phone_country_code: str = "92"

    @field_validator("database_url", "migration_database_url", mode="before")
    @classmethod
    def _normalise_db_url(cls, v):
        """Hosts (Render, Neon, Supabase...) hand out postgres:// or postgresql:// URLs with libpq-style options.
        SQLAlchemy's async driver needs +asyncpg, and asyncpg wants ssl=... instead of sslmode=... (and rejects
        channel_binding), so translate them."""
        if not isinstance(v, str):
            return v
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                v = "postgresql+asyncpg://" + v[len(prefix):]
                break
        if v.startswith("postgresql+asyncpg://"):
            parts = urlsplit(v)
            q = dict(parse_qsl(parts.query, keep_blank_values=True))
            sslmode = q.pop("sslmode", None)
            q.pop("channel_binding", None)
            if sslmode and sslmode != "disable" and "ssl" not in q:
                q["ssl"] = "require"
            v = urlunsplit(parts._replace(query=urlencode(q)))
        return v


settings = Settings()
