-- FarmWise Database Setup Script
-- This script creates the PostgreSQL database and user with full permissions

-- Drop existing database if it exists (optional - uncomment if needed)
-- DROP DATABASE IF EXISTS farmwise_db;

-- Create database
CREATE DATABASE farmwise_db 
    ENCODING 'UTF8'
    OWNER postgres;

-- Connect to the new database
\c farmwise_db

-- Create PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Set role settings
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET default_transaction_deferrable TO on;
ALTER ROLE postgres SET timezone TO 'UTC';
ALTER ROLE postgres SET search_path TO public;

-- Grant all privileges on database
GRANT ALL PRIVILEGES ON DATABASE farmwise_db TO postgres;

-- Grant schema privileges
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
GRANT CREATE ON DATABASE farmwise_db TO postgres;

-- Grant table privileges (for future tables)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO postgres;

-- Grant geometry type privileges
GRANT ALL PRIVILEGES ON ALL TYPES IN SCHEMA public TO postgres;

-- Ensure postgres is owner of all objects
ALTER SCHEMA public OWNER TO postgres;

SELECT 'Database FarmWise setup complete!' as status;
