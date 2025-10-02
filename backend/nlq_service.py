"""
Natural Language Query (NLQ) Service
Enables AI-powered database queries using OpenRouter and PostgreSQL MCP Server
"""
import os
import json
import logging
import asyncio
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class NLQService:
    """Natural Language Query service using OpenRouter AI and PostgreSQL MCP"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.model = os.getenv('AI_MODEL', 'anthropic/claude-3.5-sonnet')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # PostgreSQL connection details
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'etl_processor'),
            'user': os.getenv('POSTGRES_USER', 'etl_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'etl_password')
        }
        
        logger.info(f"NLQ Service initialized with model: {self.model}")
        logger.info(f"Database: {self.db_config['database']}@{self.db_config['host']}:{self.db_config['port']}")
    
    def get_schema_context(self, schema_name: str) -> Dict[str, Any]:
        """Get comprehensive schema context for AI"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Set search path to the session schema
            cursor.execute(f'SET search_path TO "{schema_name}", public')
            
            # Get all tables in the schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                ORDER BY table_name
            """, (schema_name,))
            tables = [row['table_name'] for row in cursor.fetchall()]
            
            # Get detailed information for each table
            schema_info = {
                'schema_name': schema_name,
                'tables': []
            }
            
            for table_name in tables:
                # Get columns
                cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema_name, table_name))
                columns = cursor.fetchall()
                
                # Get row count
                cursor.execute(f'SELECT COUNT(*) as count FROM "{schema_name}"."{table_name}"')
                row_count = cursor.fetchone()['count']
                
                # Get primary keys
                cursor.execute("""
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = %s::regclass AND i.indisprimary
                """, (f'"{schema_name}"."{table_name}"',))
                primary_keys = [row['attname'] for row in cursor.fetchall()]
                
                # Get foreign keys
                cursor.execute("""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = %s
                        AND tc.table_name = %s
                """, (schema_name, table_name))
                foreign_keys = cursor.fetchall()
                
                schema_info['tables'].append({
                    'name': table_name,
                    'row_count': row_count,
                    'columns': [dict(col) for col in columns],
                    'primary_keys': primary_keys,
                    'foreign_keys': [dict(fk) for fk in foreign_keys]
                })
            
            cursor.close()
            conn.close()
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error getting schema context: {e}")
            raise
    
    def execute_sql_query(self, schema_name: str, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query in the specified schema"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Set search path to the session schema
            cursor.execute(f'SET search_path TO "{schema_name}", public')
            
            # Execute the query
            cursor.execute(sql_query)
            
            # Check if it's a SELECT query
            if sql_query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                return {
                    'success': True,
                    'type': 'select',
                    'columns': columns,
                    'rows': [dict(row) for row in results],
                    'row_count': len(results)
                }
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                conn.commit()
                return {
                    'success': True,
                    'type': 'modification',
                    'rows_affected': cursor.rowcount
                }
            
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def query_with_ai(self, schema_name: str, user_question: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process natural language query using AI"""
        try:
            # Get schema context
            logger.info(f"Getting schema context for: {schema_name}")
            schema_context = self.get_schema_context(schema_name)
            
            # Build the system prompt
            system_prompt = self._build_system_prompt(schema_context)
            
            # Build conversation messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user question
            messages.append({"role": "user", "content": user_question})
            
            # Call OpenRouter API
            logger.info(f"Calling OpenRouter API with model: {self.model}")
            response = self._call_openrouter_api(messages)
            
            # Extract AI response
            ai_message = response['choices'][0]['message']['content']
            
            # Check if AI generated SQL query
            sql_query = self._extract_sql_from_response(ai_message)
            
            result = {
                'success': True,
                'ai_response': ai_message,
                'timestamp': datetime.now().isoformat()
            }
            
            # If SQL was generated, execute it
            if sql_query:
                logger.info(f"Executing SQL query: {sql_query[:100]}...")
                query_result = self.execute_sql_query(schema_name, sql_query)
                result['sql_query'] = sql_query
                result['query_result'] = query_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error in query_with_ai: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _build_system_prompt(self, schema_context: Dict[str, Any]) -> str:
        """Build system prompt with schema context"""
        schema_name = schema_context['schema_name']
        tables_info = []
        
        for table in schema_context['tables']:
            columns_desc = []
            for col in table['columns']:
                pk_marker = " (PRIMARY KEY)" if col['column_name'] in table['primary_keys'] else ""
                columns_desc.append(f"  - {col['column_name']}: {col['data_type']}{pk_marker}")
            
            fk_desc = []
            for fk in table['foreign_keys']:
                fk_desc.append(f"  - {fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
            
            table_desc = f"""
Table: {table['name']} ({table['row_count']} rows)
Columns:
{chr(10).join(columns_desc)}"""
            
            if fk_desc:
                table_desc += f"\nForeign Keys:\n{chr(10).join(fk_desc)}"
            
            tables_info.append(table_desc)
        
        prompt = f"""You are a helpful database assistant with access to a PostgreSQL database schema.

Schema: {schema_name}

Available Tables:
{chr(10).join(tables_info)}

Your role:
1. Answer questions about the database schema and data
2. Generate SQL queries when needed to answer questions
3. Execute queries and present results in a user-friendly format
4. Explain your reasoning and the data you find

Guidelines:
- Always use the schema name "{schema_name}" when referencing tables
- When generating SQL, wrap it in ```sql code blocks
- For SELECT queries, limit results to 100 rows unless specifically asked for more
- Present data in clear, formatted tables or lists
- If a question is ambiguous, ask for clarification
- Be concise but informative

Remember: You have direct access to execute queries, so you can provide real-time data insights."""
        
        return prompt
    
    def _call_openrouter_api(self, messages: List[Dict]) -> Dict[str, Any]:
        """Call OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5001",
            "X-Title": "ETL Processor NLQ"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()
    
    def _extract_sql_from_response(self, ai_response: str) -> Optional[str]:
        """Extract SQL query from AI response"""
        import re
        
        # Look for SQL code blocks
        sql_pattern = r'```sql\s*(.*?)\s*```'
        matches = re.findall(sql_pattern, ai_response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return matches[0].strip()
        
        return None

# Global NLQ service instance
nlq_service = NLQService()

