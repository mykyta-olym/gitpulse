-- Least-privilege PostgreSQL init
-- Runs once on first container start (docker-entrypoint-initdb.d)

-- Revoke public schema CREATE from PUBLIC
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Grant only necessary privileges to the app user
GRANT USAGE ON SCHEMA public TO gitpulse;
GRANT CREATE ON SCHEMA public TO gitpulse;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO gitpulse;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO gitpulse;

-- Enable pg_stat_statements for query analysis (optional)
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
