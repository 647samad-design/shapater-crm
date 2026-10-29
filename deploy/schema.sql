BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE agencies (
    id UUID NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    country VARCHAR(2) NOT NULL, 
    default_currency VARCHAR(3) NOT NULL, 
    plan VARCHAR(30) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE audit_logs (
    user_id UUID, 
    action VARCHAR(30) NOT NULL, 
    entity VARCHAR(30) NOT NULL, 
    entity_id UUID, 
    changes JSON NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    id UUID NOT NULL, 
    agency_id UUID NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id)
);

CREATE INDEX ix_audit_logs_agency_id ON audit_logs (agency_id);

CREATE TABLE users (
    id UUID NOT NULL, 
    agency_id UUID NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    full_name VARCHAR(200) NOT NULL, 
    hashed_password VARCHAR(255) NOT NULL, 
    role VARCHAR(20) NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id)
);

CREATE INDEX ix_users_agency_id ON users (agency_id);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE clients (
    name VARCHAR(200) NOT NULL, 
    phone VARCHAR(40) NOT NULL, 
    phone_normalized VARCHAR(40) NOT NULL, 
    email VARCHAR(255), 
    source VARCHAR(50), 
    notes TEXT, 
    assigned_to UUID, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    agency_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id), 
    FOREIGN KEY(assigned_to) REFERENCES users (id), 
    CONSTRAINT uq_client_phone_per_agency UNIQUE (agency_id, phone_normalized)
);

CREATE INDEX ix_clients_agency_id ON clients (agency_id);

CREATE INDEX ix_clients_phone_normalized ON clients (phone_normalized);

CREATE TABLE properties (
    created_by UUID, 
    title VARCHAR(300) NOT NULL, 
    description TEXT, 
    purpose VARCHAR(10) NOT NULL, 
    property_type VARCHAR(30) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    price NUMERIC(16, 2) NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    area_value FLOAT, 
    area_unit VARCHAR(10), 
    area_sqft FLOAT, 
    bedrooms INTEGER, 
    bathrooms INTEGER, 
    country VARCHAR(2) NOT NULL, 
    city VARCHAR(100), 
    area_name VARCHAR(150), 
    address VARCHAR(300), 
    latitude FLOAT, 
    longitude FLOAT, 
    features JSON NOT NULL, 
    owner_name VARCHAR(200), 
    owner_phone VARCHAR(30), 
    permit_number VARCHAR(100), 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    agency_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id), 
    FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_properties_agency_id ON properties (agency_id);

CREATE INDEX ix_properties_area_name ON properties (area_name);

CREATE INDEX ix_properties_city ON properties (city);

CREATE INDEX ix_properties_property_type ON properties (property_type);

CREATE INDEX ix_properties_purpose ON properties (purpose);

CREATE INDEX ix_properties_status ON properties (status);

CREATE TABLE requirements (
    client_id UUID NOT NULL, 
    purpose VARCHAR(10) NOT NULL, 
    property_types JSON NOT NULL, 
    budget_min NUMERIC(16, 2), 
    budget_max NUMERIC(16, 2), 
    currency VARCHAR(3) NOT NULL, 
    city VARCHAR(100), 
    preferred_areas JSON NOT NULL, 
    bedrooms_min INTEGER, 
    bedrooms_max INTEGER, 
    required_features JSON NOT NULL, 
    urgency VARCHAR(10) NOT NULL, 
    notes TEXT, 
    is_active BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    agency_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id), 
    FOREIGN KEY(client_id) REFERENCES clients (id)
);

CREATE INDEX ix_requirements_agency_id ON requirements (agency_id);

CREATE INDEX ix_requirements_client_id ON requirements (client_id);

CREATE INDEX ix_requirements_is_active ON requirements (is_active);

CREATE INDEX ix_requirements_purpose ON requirements (purpose);

CREATE TABLE leads (
    client_id UUID NOT NULL, 
    requirement_id UUID, 
    property_id UUID, 
    stage VARCHAR(20) NOT NULL, 
    source VARCHAR(50), 
    assigned_to UUID, 
    value NUMERIC(16, 2), 
    currency VARCHAR(3), 
    id UUID NOT NULL, 
    agency_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id), 
    FOREIGN KEY(assigned_to) REFERENCES users (id), 
    FOREIGN KEY(client_id) REFERENCES clients (id), 
    FOREIGN KEY(property_id) REFERENCES properties (id), 
    FOREIGN KEY(requirement_id) REFERENCES requirements (id)
);

CREATE INDEX ix_leads_agency_id ON leads (agency_id);

CREATE INDEX ix_leads_client_id ON leads (client_id);

CREATE INDEX ix_leads_stage ON leads (stage);

CREATE TABLE matches (
    requirement_id UUID NOT NULL, 
    property_id UUID NOT NULL, 
    score INTEGER NOT NULL, 
    breakdown JSON NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    id UUID NOT NULL, 
    agency_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id), 
    FOREIGN KEY(property_id) REFERENCES properties (id), 
    FOREIGN KEY(requirement_id) REFERENCES requirements (id), 
    CONSTRAINT uq_match_pair UNIQUE (requirement_id, property_id)
);

CREATE INDEX ix_matches_agency_id ON matches (agency_id);

CREATE INDEX ix_matches_property_id ON matches (property_id);

CREATE INDEX ix_matches_requirement_id ON matches (requirement_id);

CREATE INDEX ix_matches_score ON matches (score);

CREATE TABLE activities (
    lead_id UUID, 
    client_id UUID, 
    user_id UUID NOT NULL, 
    type VARCHAR(20) NOT NULL, 
    note TEXT, 
    due_at TIMESTAMP WITH TIME ZONE, 
    done BOOLEAN NOT NULL, 
    id UUID NOT NULL, 
    agency_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id), 
    FOREIGN KEY(client_id) REFERENCES clients (id), 
    FOREIGN KEY(lead_id) REFERENCES leads (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_activities_agency_id ON activities (agency_id);

CREATE INDEX ix_activities_client_id ON activities (client_id);

CREATE INDEX ix_activities_due_at ON activities (due_at);

CREATE INDEX ix_activities_lead_id ON activities (lead_id);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

-- Running upgrade 0001 -> 0002

ALTER TABLE properties ENABLE ROW LEVEL SECURITY;

ALTER TABLE properties FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON properties USING (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid) WITH CHECK (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid);

ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

ALTER TABLE clients FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON clients USING (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid) WITH CHECK (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid);

ALTER TABLE requirements ENABLE ROW LEVEL SECURITY;

ALTER TABLE requirements FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON requirements USING (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid) WITH CHECK (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid);

ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

ALTER TABLE matches FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON matches USING (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid) WITH CHECK (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid);

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

ALTER TABLE leads FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON leads USING (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid) WITH CHECK (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid);

ALTER TABLE activities ENABLE ROW LEVEL SECURITY;

ALTER TABLE activities FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON activities USING (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid) WITH CHECK (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid);

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON audit_logs USING (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid) WITH CHECK (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid);

DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'shapater_app') THEN
            GRANT USAGE ON SCHEMA public TO shapater_app;
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO shapater_app;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public
              GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO shapater_app;
            REVOKE ALL ON alembic_version FROM shapater_app;
          END IF;
        END $$;;

UPDATE alembic_version SET version_num='0002' WHERE alembic_version.version_num = '0001';

-- Running upgrade 0002 -> 0003

CREATE TABLE api_keys (
    provider VARCHAR(40) NOT NULL, 
    label VARCHAR(100) NOT NULL, 
    encrypted_value TEXT NOT NULL, 
    last4 VARCHAR(8) NOT NULL, 
    notes TEXT, 
    created_by UUID, 
    id UUID NOT NULL, 
    agency_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    CONSTRAINT uq_apikey_label UNIQUE (agency_id, provider, label)
);

CREATE INDEX ix_api_keys_agency_id ON api_keys (agency_id);

CREATE INDEX ix_api_keys_provider ON api_keys (provider);

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

ALTER TABLE api_keys FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON api_keys USING (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid) WITH CHECK (agency_id = NULLIF(current_setting('app.current_agency', true), '')::uuid);

DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'shapater_app') THEN
            GRANT SELECT, INSERT, UPDATE, DELETE ON api_keys TO shapater_app;
          END IF;
        END $$;;

UPDATE alembic_version SET version_num='0003' WHERE alembic_version.version_num = '0002';

COMMIT;

