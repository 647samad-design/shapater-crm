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
    def _asyncpg_scheme(cls, v):
        """Hosts (Render, Railway, Neon) give postgres:// or postgresql://; SQLAlchemy async needs +asyncpg."""
        if isinstance(v, str):
            for prefix in ("postgres://", "postgresql://"):
                if v.startswith(prefix):
                    return "postgresql+asyncpg://" + v[len(prefix):]
        return v


settings = Settings()
