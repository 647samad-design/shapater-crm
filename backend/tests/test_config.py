from app.core.config import Settings


def test_host_style_database_urls_are_converted():
    assert Settings(database_url="postgres://u:p@h/db").database_url == "postgresql+asyncpg://u:p@h/db"
    assert Settings(database_url="postgresql://u:p@h/db").database_url == "postgresql+asyncpg://u:p@h/db"
    assert Settings(database_url="postgresql+asyncpg://u:p@h/db").database_url == "postgresql+asyncpg://u:p@h/db"
    assert Settings(database_url="sqlite+aiosqlite:///x.db").database_url == "sqlite+aiosqlite:///x.db"


def test_neon_style_url_is_made_asyncpg_compatible():
    url = "postgresql://neondb_owner:pw@ep-cool-123.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    out = Settings(database_url=url).database_url
    assert out == "postgresql+asyncpg://neondb_owner:pw@ep-cool-123.ap-southeast-1.aws.neon.tech/neondb?ssl=require"
    assert "sslmode" not in out and "channel_binding" not in out
    # unix-socket / local URLs keep their other options and drop sslmode=disable
    local = Settings(database_url="postgresql://u:p@/db?host=/tmp/pg&sslmode=disable").database_url
    assert local == "postgresql+asyncpg://u:p@/db?host=%2Ftmp%2Fpg"
