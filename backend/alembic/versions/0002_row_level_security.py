"""Row-Level Security: database-enforced tenant isolation

Every tenant table is filtered by app.current_agency (set per transaction by the API).
If the setting is missing, NULLIF(...) yields NULL and NO rows are visible (fail-closed).
The API must connect as a non-superuser role (see docker/initdb) - superusers bypass RLS.

Revision ID: 0002
Revises: 0001
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TENANT_TABLES = ["properties", "clients", "requirements", "matches", "leads", "activities", "audit_logs"]
APP_ROLE = "shapater_app"
EXPR = "agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid"


def upgrade() -> None:
    for t in TENANT_TABLES:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant_isolation ON {t} USING ({EXPR}) WITH CHECK ({EXPR})")
    # Grant the restricted app role access (role is created by docker/initdb or your DBA).
    op.execute(f"""
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
            GRANT USAGE ON SCHEMA public TO {APP_ROLE};
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE};
            ALTER DEFAULT PRIVILEGES IN SCHEMA public
              GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_ROLE};
            REVOKE ALL ON alembic_version FROM {APP_ROLE};
          END IF;
        END $$;
    """)


def downgrade() -> None:
    for t in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {t}")
        op.execute(f"ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY")
