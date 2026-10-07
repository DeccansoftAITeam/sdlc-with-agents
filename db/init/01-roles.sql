-- Local/CI only (docker compose). Cloud environments create the same roles via infra/.
-- owner: owns tables, runs migrations.   app: runtime role, NOT owner, NOBYPASSRLS.
CREATE ROLE ticketdesk_owner LOGIN PASSWORD 'owner' NOBYPASSRLS;
CREATE ROLE ticketdesk_app   LOGIN PASSWORD 'app'   NOBYPASSRLS;
CREATE DATABASE ticketdesk OWNER ticketdesk_owner;
\connect ticketdesk
ALTER SCHEMA public OWNER TO ticketdesk_owner;
GRANT USAGE ON SCHEMA public TO ticketdesk_app;
ALTER DEFAULT PRIVILEGES FOR ROLE ticketdesk_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ticketdesk_app;
ALTER DEFAULT PRIVILEGES FOR ROLE ticketdesk_owner IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO ticketdesk_app;
CREATE EXTENSION IF NOT EXISTS vector;
