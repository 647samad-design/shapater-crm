-- Restricted role the API connects with. Row-Level Security applies to it.
-- CHANGE THE PASSWORD in production (and use secrets management).
CREATE ROLE shapater_app LOGIN PASSWORD 'shapater_app_pw' NOSUPERUSER NOBYPASSRLS;
GRANT CONNECT ON DATABASE shapater TO shapater_app;
