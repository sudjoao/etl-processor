"""
Database configuration and utilities for ETL Processor
Handles PostgreSQL connections and session management
"""

import os
import psycopg2
import asyncpg
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import json

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = int(os.getenv('POSTGRES_PORT', 5432))
        self.database = os.getenv('POSTGRES_DB', 'etl_processor')
        self.user = os.getenv('POSTGRES_USER', 'etl_user')
        self.password = os.getenv('POSTGRES_PASSWORD', 'etl_password')
    
    @property
    def connection_string(self) -> str:
        """Get synchronous connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_connection_string(self) -> str:
        """Get asynchronous connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self):
        self.config = DatabaseConfig()
    
    def get_connection(self):
        """Get synchronous database connection"""
        try:
            conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def get_async_connection(self):
        """Get asynchronous database connection"""
        try:
            conn = await asyncpg.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database (async): {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

class SessionManager:
    """Manages NLQ sessions and schema lifecycle"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def create_session(self, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new NLQ session"""
        try:
            session_id = str(uuid.uuid4())
            schema_name = f"nlq_session_{session_id.replace('-', '_')}"
            
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO nlq_sessions (schema_id, schema_name, metadata)
                        VALUES (%s, %s, %s)
                        RETURNING id, created_at, expires_at
                    """, (session_id, schema_name, json.dumps(metadata or {})))
                    
                    result = cursor.fetchone()
                    conn.commit()
                    
                    return {
                        'session_id': session_id,
                        'schema_name': schema_name,
                        'created_at': result[1].isoformat(),
                        'expires_at': result[2].isoformat(),
                        'status': 'created'
                    }
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def provision_session(self, schema_id: str, sql_content: str) -> Dict[str, Any]:
        """Provision a session with SQL schema"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get session info
                    cursor.execute("""
                        SELECT schema_name, status FROM nlq_sessions 
                        WHERE schema_id = %s
                    """, (schema_id,))
                    
                    session = cursor.fetchone()
                    if not session:
                        raise ValueError(f"Session {schema_id} not found")
                    
                    schema_name, status = session
                    
                    if status == 'provisioned':
                        raise ValueError(f"Session {schema_id} is already provisioned")
                    
                    # Create schema
                    cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                    
                    # Set search path and execute SQL
                    cursor.execute(f'SET search_path TO "{schema_name}", public')

                    # Fix SQL compatibility issues and execute the provided SQL content
                    fixed_sql_content = self._fix_sql_compatibility(sql_content)
                    self._execute_sql_statements(cursor, fixed_sql_content)
                    
                    # Update session status
                    cursor.execute("""
                        UPDATE nlq_sessions 
                        SET status = 'provisioned', 
                            provisioned_at = CURRENT_TIMESTAMP,
                            sql_content = %s
                        WHERE schema_id = %s
                    """, (sql_content, schema_id))
                    
                    conn.commit()
                    
                    return {
                        'session_id': schema_id,
                        'schema_name': schema_name,
                        'status': 'provisioned',
                        'message': 'Session provisioned successfully'
                    }
                    
        except Exception as e:
            logger.error(f"Failed to provision session {schema_id}: {e}")
            raise
    
    def get_session_info(self, schema_id: str) -> Dict[str, Any]:
        """Get session information"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT schema_name, created_at, expires_at, status, 
                               provisioned_at, metadata
                        FROM nlq_sessions 
                        WHERE schema_id = %s
                    """, (schema_id,))
                    
                    result = cursor.fetchone()
                    if not result:
                        raise ValueError(f"Session {schema_id} not found")
                    
                    schema_name, created_at, expires_at, status, provisioned_at, metadata = result
                    
                    # Calculate time remaining
                    now = datetime.now(expires_at.tzinfo)
                    time_remaining = max(0, (expires_at - now).total_seconds())
                    
                    return {
                        'session_id': schema_id,
                        'schema_name': schema_name,
                        'created_at': created_at.isoformat(),
                        'expires_at': expires_at.isoformat(),
                        'status': status,
                        'provisioned_at': provisioned_at.isoformat() if provisioned_at else None,
                        'time_remaining_seconds': int(time_remaining),
                        'metadata': metadata or {}
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get session info for {schema_id}: {e}")
            raise
    
    def cleanup_session(self, schema_id: str) -> Dict[str, Any]:
        """Manually cleanup a session"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get session info
                    cursor.execute("""
                        SELECT schema_name, status FROM nlq_sessions 
                        WHERE schema_id = %s
                    """, (schema_id,))
                    
                    result = cursor.fetchone()
                    if not result:
                        raise ValueError(f"Session {schema_id} not found")
                    
                    schema_name, status = result
                    
                    if status == 'cleaned_up':
                        return {
                            'session_id': schema_id,
                            'status': 'already_cleaned',
                            'message': 'Session was already cleaned up'
                        }
                    
                    # Drop schema
                    cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                    
                    # Update session status
                    cursor.execute("""
                        UPDATE nlq_sessions 
                        SET status = 'cleaned_up'
                        WHERE schema_id = %s
                    """, (schema_id,))
                    
                    # Log cleanup
                    cursor.execute("""
                        INSERT INTO cleanup_log (session_id, schema_name, cleanup_type, cleanup_status)
                        SELECT id, %s, 'manual', 'success'
                        FROM nlq_sessions WHERE schema_id = %s
                    """, (schema_name, schema_id))
                    
                    conn.commit()
                    
                    return {
                        'session_id': schema_id,
                        'status': 'cleaned_up',
                        'message': 'Session cleaned up successfully'
                    }
                    
        except Exception as e:
            logger.error(f"Failed to cleanup session {schema_id}: {e}")
            raise

    def _fix_sql_compatibility(self, sql_content: str) -> str:
        """Fix SQL compatibility issues for PostgreSQL"""
        import re

        logger.info("Applying SQL compatibility fixes...")

        # Fix table alias issues in CREATE VIEW statements
        # The problem is that aliases like "Genre.genre" are interpreted as schema.table
        # We need to replace them with quoted aliases to avoid schema conflicts

        # Pattern to find CREATE VIEW statements with problematic aliases
        view_pattern = r'(CREATE VIEW\s+\w+\s+AS\s+SELECT\s+)(.*?)(\s+FROM\s+.*?)(\s+GROUP BY\s+.*?)(;|\s*$)'

        def fix_view_aliases(match):
            create_part = match.group(1)
            select_part = match.group(2)
            from_part = match.group(3)
            group_by_part = match.group(4) if match.group(4) else ""
            end_part = match.group(5)

            # Extract table aliases from the FROM clause
            # Look for patterns like "LEFT JOIN dim_Genre Genre"
            alias_pattern = r'(?:LEFT\s+JOIN|JOIN)\s+(\w+)\s+(\w+)\s+ON'
            aliases = re.findall(alias_pattern, from_part, re.IGNORECASE)

            # Create a mapping of original aliases to quoted aliases
            alias_mapping = {}
            for table_name, alias in aliases:
                # Use quoted aliases to avoid schema conflicts
                alias_mapping[alias] = f'"{alias.lower()}"'

            # Fix the SELECT clause - replace problematic aliases
            fixed_select = select_part
            for original_alias, new_alias in alias_mapping.items():
                # Replace "OriginalAlias.column" with "quoted_alias".column
                pattern = rf'\b{re.escape(original_alias)}\.(\w+)'
                replacement = rf'{new_alias}.\1'
                fixed_select = re.sub(pattern, replacement, fixed_select)

            # Fix the GROUP BY clause if it exists
            fixed_group_by = group_by_part
            if group_by_part:
                for original_alias, new_alias in alias_mapping.items():
                    pattern = rf'\b{re.escape(original_alias)}\.(\w+)'
                    replacement = rf'{new_alias}.\1'
                    fixed_group_by = re.sub(pattern, replacement, fixed_group_by)

            # Fix the FROM clause to use quoted aliases
            fixed_from = from_part
            for table_name, alias in aliases:
                new_alias = f'"{alias.lower()}"'

                # Replace "LEFT JOIN table_name OriginalAlias ON" with "LEFT JOIN table_name "quoted_alias" ON"
                pattern = rf'(\s+{re.escape(table_name)}\s+){re.escape(alias)}(\s+ON)'
                replacement = rf'\1{new_alias}\2'
                fixed_from = re.sub(pattern, replacement, fixed_from, flags=re.IGNORECASE)

                # Fix the ON condition: replace "OriginalAlias.column" with "quoted_alias".column
                pattern = rf'\b{re.escape(alias)}\.(\w+)'
                replacement = rf'{new_alias}.\1'
                fixed_from = re.sub(pattern, replacement, fixed_from)

            return create_part + fixed_select + fixed_from + fixed_group_by + end_part

        # Apply the fix to all CREATE VIEW statements
        fixed_content = re.sub(view_pattern, fix_view_aliases, sql_content, flags=re.DOTALL | re.IGNORECASE)

        if fixed_content != sql_content:
            logger.info("SQL compatibility fixes applied successfully")
        else:
            logger.info("No SQL compatibility fixes needed")

        return fixed_content

    def _execute_sql_statements(self, cursor, sql_content: str):
        """Execute multiple SQL statements from a single string"""
        import re

        # Remove comments and normalize whitespace
        sql_content = re.sub(r'--.*?\n', '\n', sql_content)  # Remove line comments
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)  # Remove block comments

        # Split by semicolons, but be careful about semicolons in strings
        statements = []
        current_statement = ""
        in_string = False
        escape_next = False

        for char in sql_content:
            if escape_next:
                current_statement += char
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                current_statement += char
                continue

            if char == "'" and not escape_next:
                in_string = not in_string
                current_statement += char
                continue

            if char == ';' and not in_string:
                statement = current_statement.strip()
                if statement:  # Only add non-empty statements
                    statements.append(statement)
                current_statement = ""
                continue

            current_statement += char

        # Add the last statement if it doesn't end with semicolon
        statement = current_statement.strip()
        if statement:
            statements.append(statement)

        # Execute each statement
        for i, statement in enumerate(statements):
            if statement.strip():  # Skip empty statements
                try:
                    logger.info(f"Executing statement {i+1}: {statement[:100]}...")
                    cursor.execute(statement)
                    logger.info(f"Statement {i+1} executed successfully")
                except Exception as e:
                    logger.error(f"Error executing statement {i+1}: {statement[:200]}...")
                    logger.error(f"Full statement: {statement}")
                    logger.error(f"Error details: {e}")
                    raise

# Global database manager instance
db_manager = DatabaseManager()
session_manager = SessionManager()
