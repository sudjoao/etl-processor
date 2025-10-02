# NLQ Feature - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Configure API Key

Edit your `.env` file:

```bash
# Required: OpenRouter API Key
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here

# Optional: Choose AI Model (default: claude-3.5-sonnet)
NLQ_MODEL=anthropic/claude-3.5-sonnet

# Or use a FREE model for testing:
# NLQ_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

**Get an API Key:**
1. Visit https://openrouter.ai/
2. Sign up for an account
3. Add credits (or use free models)
4. Copy your API key

### Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Start the Application

```bash
# Terminal 1: Start PostgreSQL
docker-compose up postgres -d

# Terminal 2: Start Backend
cd backend
python app.py

# Terminal 3: Start Frontend
pnpm dev
```

### Step 4: Create a Session

1. Open http://localhost:3000
2. Go to "Configuração de Exploração" tab
3. Upload a SQL file (try `data/DataWarehouse_complete-14.sql`)
4. Click "Configurar Ambiente de Exploração"
5. Wait for provisioning to complete

### Step 5: Start Chatting!

The chat interface appears automatically. Try these questions:

```
"How many tables does my schema have?"
"Show me the first 5 records from dim_movie"
"What columns does the fact_dados_importados table have?"
```

## 💡 Example Questions

### Schema Exploration

```
"How many tables does my schema have?"
"List all tables in my schema"
"What is the structure of dim_movie?"
"Show me all foreign keys"
"What are the primary keys in fact_dados_importados?"
```

### Data Retrieval

```
"Show me 5 records from dim_movie"
"Get all records from dim_person where director is 'Hayao Miyazaki'"
"Show me the first 10 movies"
"Display all unique genres"
"List all directors"
```

### Data Analysis

```
"How many rows are in each table?"
"What is the average budget?"
"Count movies by genre"
"Show me the total budget by rating"
"Which genre has the most movies?"
```

### Aggregations

```
"What is the sum of all budgets?"
"Calculate the average box office revenue"
"Count distinct directors"
"Show me min and max budgets"
"Group movies by rating and count them"
```

## 🎯 Tips for Best Results

### 1. Be Specific

❌ Bad: "Show me data"
✅ Good: "Show me the first 10 records from dim_movie"

### 2. Use Table Names

❌ Bad: "How many movies?"
✅ Good: "How many rows in dim_movie?"

### 3. Ask for Structure First

```
"What columns does dim_movie have?"
```

Then ask data questions based on the structure.

### 4. Use Natural Language

You don't need to know SQL! Ask naturally:

```
"How many different genres are there?"
"Show me all PG-rated movies"
"What's the most expensive movie?"
```

## 🔧 Troubleshooting

### Problem: "Payment Required" Error

**Cause:** OpenRouter API key has no credits

**Solution:**
1. Add credits at https://openrouter.ai/
2. Or use a free model:
   ```bash
   NLQ_MODEL=meta-llama/llama-3.1-8b-instruct:free
   ```

### Problem: "Session must be provisioned"

**Cause:** Trying to chat before provisioning

**Solution:**
1. Upload SQL file first
2. Click "Configurar Ambiente"
3. Wait for green "Sessão Ativa" card
4. Chat will appear automatically

### Problem: No Response

**Cause:** Backend not running or API error

**Solution:**
1. Check backend terminal for errors
2. Verify API key is set correctly
3. Check internet connection
4. Try restarting backend

### Problem: Wrong SQL Generated

**Cause:** Question is ambiguous

**Solution:**
1. Be more specific
2. Use exact table/column names
3. Ask for table structure first
4. Rephrase the question

## 📊 Understanding Responses

### Response Format

Each AI response may include:

1. **Natural Language Answer**: Human-readable explanation
2. **SQL Query**: The generated SQL (in code block)
3. **Query Results**: Formatted table with data
4. **Insights**: Additional context or observations

### Example Response

```
Question: "How many tables does my schema have?"

AI Response:
"Your schema has 6 tables:
- dim_movie
- dim_person
- dim_location
- dim_language
- dim_date
- fact_dados_importados"

SQL Query:
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'nlq_session_...'

Results:
┌───────┐
│ count │
├───────┤
│   6   │
└───────┘
```

## 🎨 UI Features

### Message Types

- **User Messages**: Blue, right-aligned
- **AI Messages**: Gray, left-aligned
- **SQL Queries**: Code blocks with syntax highlighting
- **Results**: Formatted tables
- **Errors**: Red alert boxes

### Interactive Elements

- **Send Button**: Submit your question
- **Input Field**: Type your question
- **Scroll Area**: Auto-scrolls to latest message
- **Schema Indicator**: Shows current schema name

## 🔐 Security Notes

### What the AI Can Access

✅ Your session's schema only
✅ Tables you created
✅ Data you uploaded

### What the AI Cannot Access

❌ Other users' sessions
❌ Other schemas
❌ System tables
❌ PostgreSQL configuration

### Safe Queries

The AI is instructed to generate:
- Read-only queries (SELECT)
- Safe aggregations
- Proper WHERE clauses
- Limited result sets

## 📈 Performance Tips

### For Faster Responses

1. Use simpler questions
2. Choose faster AI models (claude-haiku)
3. Limit result sets ("first 10 records")
4. Avoid complex joins initially

### For Better Accuracy

1. Use exact table/column names
2. Provide context in questions
3. Ask follow-up questions
4. Use the conversation history

## 🆓 Free Models

If you want to test without paying:

```bash
# In .env file:

# Llama 3.1 (Free)
NLQ_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Mistral (Free)
NLQ_MODEL=mistralai/mistral-7b-instruct:free

# Gemma (Free)
NLQ_MODEL=google/gemma-2-9b-it:free
```

**Note:** Free models may be slower and less accurate than paid models.

## 📚 Advanced Usage

### Multi-Turn Conversations

The AI remembers previous questions:

```
You: "How many tables?"
AI: "You have 6 tables..."

You: "Show me the first one"
AI: "Here are records from dim_movie..."
```

### Complex Queries

```
"Show me the top 5 directors by number of movies"
"Calculate average budget per genre"
"Find movies with budget > 100000000"
"Join dim_movie and fact_dados_importados"
```

### Data Exploration

```
"What's the data distribution in dim_movie?"
"Are there any null values in fact_dados_importados?"
"Show me a sample of each table"
"What are the unique values in the rating column?"
```

## 🎓 Learning SQL

The NLQ feature is great for learning SQL:

1. Ask a question in natural language
2. See the generated SQL
3. Understand how it works
4. Try variations

Example learning path:

```
1. "Count rows in dim_movie" → Learn COUNT(*)
2. "Show movies where rating is PG" → Learn WHERE
3. "Count movies by genre" → Learn GROUP BY
4. "Show top 5 movies by budget" → Learn ORDER BY LIMIT
```

## 🔄 Session Management

### Session Lifecycle

1. **Created**: Session exists but no schema
2. **Provisioned**: Schema created, SQL executed, ready for queries
3. **Active**: Can chat and query data
4. **Expired**: After 24 hours, schema is cleaned up

### Refresh Session

Click "Atualizar Info" to check:
- Time remaining
- Session status
- Schema name

### Cleanup Session

Click "Finalizar Sessão" to:
- Drop the schema
- Delete all data
- Free up resources

## 📞 Getting Help

### Check Logs

Backend logs show:
- API calls
- SQL queries executed
- Errors and warnings

### Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "Payment Required" | No API credits | Add credits or use free model |
| "Session not found" | Invalid session ID | Create new session |
| "Must be provisioned" | Session not ready | Wait for provisioning |
| "Connection refused" | Database down | Start PostgreSQL |

### Debug Mode

Check backend terminal for detailed logs:
```
INFO:nlq_service:Getting schema context...
INFO:nlq_service:Calling OpenRouter API...
INFO:nlq_service:Executing SQL query...
```

## 🎉 Success Checklist

- [ ] API key configured in `.env`
- [ ] Dependencies installed
- [ ] PostgreSQL running
- [ ] Backend running on port 5001
- [ ] Frontend running on port 3000
- [ ] SQL file uploaded
- [ ] Session provisioned
- [ ] Chat interface visible
- [ ] First question answered successfully

## 🚀 You're Ready!

Start exploring your data with natural language queries. The AI is ready to help you discover insights, analyze patterns, and understand your data better.

Happy querying! 🎊

