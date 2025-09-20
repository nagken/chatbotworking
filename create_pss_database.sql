-- Create the PSS Knowledge Assist database and user
-- Run these commands in your psql session

-- Create the database
CREATE DATABASE pss_knowledge_assist_dev;

-- Create a user for the application (if not exists)
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'pss_user') THEN
      CREATE USER pss_user WITH PASSWORD 'pss_password_123';
   END IF;
END
$do$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pss_knowledge_assist_dev TO pss_user;

-- Connect to the new database
\c pss_knowledge_assist_dev;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO pss_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pss_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pss_user;

-- List databases to confirm
\l

-- Show current database
SELECT current_database();
