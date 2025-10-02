-- ETL Processor Database Initialization Script
-- This script sets up the initial database structure for the ETL Processor

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create sessions table to track NLQ sessions
CREATE TABLE IF NOT EXISTS nlq_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_id VARCHAR(255) UNIQUE NOT NULL,
    schema_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),
    status VARCHAR(50) DEFAULT 'created',
    provisioned_at TIMESTAMP WITH TIME ZONE,
    sql_content TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create index for efficient cleanup queries
CREATE INDEX IF NOT EXISTS idx_nlq_sessions_expires_at ON nlq_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_nlq_sessions_status ON nlq_sessions(status);
CREATE INDEX IF NOT EXISTS idx_nlq_sessions_schema_id ON nlq_sessions(schema_id);

-- Create cleanup log table to track automated cleanup operations
CREATE TABLE IF NOT EXISTS cleanup_log (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES nlq_sessions(id),
    schema_name VARCHAR(255),
    cleanup_type VARCHAR(50), -- 'automatic', 'manual'
    cleanup_status VARCHAR(50), -- 'success', 'failed', 'partial'
    cleanup_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create index for cleanup log queries
CREATE INDEX IF NOT EXISTS idx_cleanup_log_cleanup_at ON cleanup_log(cleanup_at);
CREATE INDEX IF NOT EXISTS idx_cleanup_log_session_id ON cleanup_log(session_id);

-- Function to automatically clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    session_record RECORD;
    cleanup_count INTEGER := 0;
    error_msg TEXT;
BEGIN
    -- Find expired sessions that haven't been cleaned up yet
    FOR session_record IN 
        SELECT id, schema_id, schema_name 
        FROM nlq_sessions 
        WHERE expires_at < CURRENT_TIMESTAMP 
        AND status != 'cleaned_up'
    LOOP
        BEGIN
            -- Drop the schema if it exists
            EXECUTE format('DROP SCHEMA IF EXISTS %I CASCADE', session_record.schema_name);
            
            -- Update session status
            UPDATE nlq_sessions 
            SET status = 'cleaned_up' 
            WHERE id = session_record.id;
            
            -- Log successful cleanup
            INSERT INTO cleanup_log (session_id, schema_name, cleanup_type, cleanup_status)
            VALUES (session_record.id, session_record.schema_name, 'automatic', 'success');
            
            cleanup_count := cleanup_count + 1;
            
        EXCEPTION WHEN OTHERS THEN
            error_msg := SQLERRM;
            
            -- Log failed cleanup
            INSERT INTO cleanup_log (session_id, schema_name, cleanup_type, cleanup_status, error_message)
            VALUES (session_record.id, session_record.schema_name, 'automatic', 'failed', error_msg);
            
            -- Update session status to indicate cleanup failure
            UPDATE nlq_sessions 
            SET status = 'cleanup_failed' 
            WHERE id = session_record.id;
        END;
    END LOOP;
    
    RETURN cleanup_count;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO etl_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO etl_user;
GRANT USAGE, CREATE ON SCHEMA public TO etl_user;

-- Insert initial data or configuration if needed
INSERT INTO nlq_sessions (schema_id, schema_name, status, metadata) 
VALUES ('example-session', 'example_schema', 'example', '{"description": "Example session for testing"}')
ON CONFLICT (schema_id) DO NOTHING;
