# Natural Language Query (NLQ) Feature Documentation

## Overview

The NLQ feature enables users to interact with their provisioned database schemas using natural language questions powered by AI. Users can ask questions about their data, and the AI will generate and execute SQL queries, returning formatted results.

## Architecture

### Components

1. **Backend Service** (`backend/nlq_service.py`)
   - Handles AI-powered natural language to SQL conversion
   - Manages database connections and query execution
   - Provides schema context to the AI for accurate query generation

2. **API Endpoint** (`backend/app.py`)
   - `/api/nlq/session/<schema_id>/query` - POST endpoint for processing NLQ queries

3. **Frontend Component** (`components/nlq-chat.tsx`)
   - Chat interface for user interaction
   - Message history display
   - SQL query and result visualization

4. **Integration** (`components/tabs/configuracao-exploracao-tab.tsx`)
   - Integrated into the "Configuração de Exploração" tab
   - Only visible when a session is provisioned

## Features

### AI Capabilities

The AI assistant can:

1. **Schema Exploration**
   - Count tables in the schema
   - List all tables and their types
   - Describe table structures and columns
   - Show primary and foreign key relationships

2. **Data Queries**
   - Retrieve records from tables
   - Filter and sort data
   - Aggregate data (COUNT, SUM, AVG, etc.)
   - Join tables based on relationships

3. **Data Analysis**
   - Calculate statistics
   - Identify patterns
   - Compare data across tables
   - Generate insights

### Example Questions

```
- "How many tables does my schema have?"
- "Show me the first 5 records from dim_movie"
- "What columns does the fact_dados_importados table have?"
- "How many rows are in each table?"
- "What are the foreign keys in my schema?"
- "Show me all movies with rating 'PG'"
- "What is the average budget in the fact table?"
- "List all unique genres from dim_movie"
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# NLQ Configuration
NLQ_MODEL=anthropic/claude-3.5-sonnet
NLQ_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
```

### Supported Models

The system uses OpenRouter for AI services. Recommended models:

- `anthropic/claude-3.5-sonnet` (Best performance, recommended)
- `anthropic/claude-3-haiku` (Faster, lower cost)
- `openai/gpt-4o` (Alternative)
- `openai/gpt-3.5-turbo` (Budget option)

### API Key Setup

1. Get an API key from [OpenRouter](https://openrouter.ai/)
2. Add credits to your OpenRouter account
3. Set the `OPENROUTER_API_KEY` in your `.env` file

**Note:** The Claude 3.5 Sonnet model requires payment. Make sure your OpenRouter account has sufficient credits.

## Installation

### Backend Dependencies

The required Python packages are already added to `backend/requirements.txt`:

```bash
anthropic==0.39.0
```

Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### Frontend Dependencies

No additional frontend dependencies are required. The chat component uses existing UI components from shadcn/ui.

## Usage

### 1. Provision a Session

First, upload a SQL file and provision a session:

1. Go to the "Configuração de Exploração" tab
2. Upload a SQL file (e.g., `data/DataWarehouse_complete-14.sql`)
3. Click "Configurar Ambiente de Exploração"
4. Wait for the session to be provisioned

### 2. Use the Chat Interface

Once the session is provisioned, the chat interface will appear:

1. Type your question in natural language
2. Press Enter or click the Send button
3. The AI will process your question and respond
4. If SQL is generated, it will be displayed along with the results

### 3. View Results

Results are displayed in different formats:

- **Table Data**: Shown in a formatted table with columns and rows
- **Counts/Aggregates**: Displayed as text with the numeric result
- **Errors**: Shown in red alert boxes with error details

## API Reference

### POST `/api/nlq/session/<schema_id>/query`

Process a natural language query for a session.

**Request Body:**
```json
{
  "question": "How many tables does my schema have?",
  "conversation_history": [
    {
      "role": "user",
      "content": "Previous question"
    },
    {
      "role": "assistant",
      "content": "Previous response"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "response": "Your schema has 6 tables...",
  "sql_query": "SELECT COUNT(*) FROM information_schema.tables...",
  "query_result": {
    "success": true,
    "type": "select",
    "columns": ["count"],
    "rows": [{"count": 6}],
    "row_count": 1
  },
  "timestamp": "2025-10-02T12:30:00.000000"
}
```

## How It Works

### 1. Schema Context Extraction

When a query is received, the system:

1. Retrieves the session's schema name
2. Queries PostgreSQL's `information_schema` to get:
   - All tables in the schema
   - Column definitions (name, type, nullable, default)
   - Primary keys
   - Foreign keys
   - Row counts

### 2. AI Processing

The system:

1. Builds a comprehensive system prompt with schema context
2. Sends the user's question to OpenRouter AI
3. The AI analyzes the question and schema
4. Generates appropriate SQL query if needed

### 3. Query Execution

If SQL is generated:

1. The system sets the search path to the session schema
2. Executes the SQL query
3. Fetches results (limited to 100 rows for display)
4. Formats results for the frontend

### 4. Response Formatting

The AI:

1. Provides a natural language explanation
2. Shows the SQL query used (in code blocks)
3. Presents results in a user-friendly format
4. Offers insights or additional context

## Security

### Schema Isolation

- Each session has its own dedicated PostgreSQL schema
- The AI can only access the user's specific session schema
- No cross-session data access is possible

### SQL Injection Prevention

- All queries are executed within the session schema context
- PostgreSQL's parameterized queries are used where applicable
- The AI is instructed to generate safe, read-only queries

### Access Control

- Sessions must be provisioned before querying
- Session IDs are UUIDs (hard to guess)
- Sessions expire after 24 hours

## Troubleshooting

### "Payment Required" Error

**Problem:** OpenRouter returns 402 error

**Solution:**
1. Check your OpenRouter account balance
2. Add credits to your account
3. Verify your API key is correct
4. Try a free model like `meta-llama/llama-3.1-8b-instruct:free`

### "Session must be provisioned" Error

**Problem:** Trying to query before provisioning

**Solution:**
1. Upload a SQL file first
2. Click "Configurar Ambiente de Exploração"
3. Wait for provisioning to complete
4. The chat interface will appear automatically

### No Response from AI

**Problem:** AI doesn't respond or times out

**Solution:**
1. Check backend logs for errors
2. Verify OpenRouter API key is set
3. Check internet connection
4. Try a simpler question first

### Incorrect SQL Generated

**Problem:** AI generates wrong SQL

**Solution:**
1. Rephrase your question more clearly
2. Be specific about table and column names
3. Ask the AI to "show me the table structure first"
4. Provide more context in your question

## Performance Considerations

### Query Limits

- SELECT queries are limited to 100 rows for display
- Full result sets are still returned to the AI for analysis
- Use LIMIT in your questions for large tables

### Response Time

- Simple questions: 2-5 seconds
- Complex queries: 5-15 seconds
- Depends on:
  - AI model speed
  - Database query complexity
  - Network latency

### Cost Optimization

- Use cheaper models for simple questions
- Claude Haiku is faster and cheaper than Sonnet
- Free models available for testing
- Conversation history adds to token usage

## Future Enhancements

Potential improvements:

1. **Query History**: Save and replay previous queries
2. **Export Results**: Download query results as CSV/Excel
3. **Visualizations**: Generate charts from query results
4. **Query Suggestions**: AI-powered query recommendations
5. **Multi-turn Conversations**: Better context retention
6. **Custom Prompts**: User-defined AI behavior
7. **Query Optimization**: AI suggests index improvements

## Testing

### Manual Testing

Test the feature with these questions:

```bash
# Schema exploration
"How many tables does my schema have?"
"List all tables in my schema"
"What columns does dim_movie have?"

# Data retrieval
"Show me 5 records from dim_movie"
"What are all the unique genres?"
"How many rows in fact_dados_importados?"

# Analysis
"What is the average budget?"
"Show me movies grouped by rating"
"Which director has the most movies?"
```

### Automated Testing

Create a test script:

```python
import requests

session_id = "your-session-id"
questions = [
    "How many tables?",
    "Show me dim_movie structure",
    "Count rows in each table"
]

for q in questions:
    response = requests.post(
        f"http://localhost:5001/api/nlq/session/{session_id}/query",
        json={"question": q}
    )
    print(f"Q: {q}")
    print(f"A: {response.json()['response'][:100]}...")
```

## Support

For issues or questions:

1. Check the backend logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure PostgreSQL is running and accessible
4. Test with simple questions first
5. Check OpenRouter API status and credits

## License

This feature is part of the ETL Processor project and follows the same license.

