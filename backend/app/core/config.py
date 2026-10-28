from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Shapater CRM"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/shapater"
    secret_key: str = "change-me"
    access_token_minutes: int = 60 * 12
    match_threshold: int = 70
    cors_origins: list[str] = ["http://localhost:3000"]
    default_phone_country_code: str = "92"


settings = Settings()
