-- PSS Knowledge Assist Database Setup
-- Run this in your PostgreSQL console

-- Create the PSS Knowledge Assist database
CREATE DATABASE pss_knowledge_assist_dev;

-- Create a user for the application (optional, for better security)
CREATE USER pss_user WITH PASSWORD 'pss_password_123';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pss_knowledge_assist_dev TO pss_user;

-- Switch to the new database
\c pss_knowledge_assist_dev;

-- Show current database
SELECT current_database();

-- Show that we're ready
\l
