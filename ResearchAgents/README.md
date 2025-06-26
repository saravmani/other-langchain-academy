# Equity Research Agent API

A LangGraph-based equity research report generator exposed via FastAPI.

## Features

- **Equity Research Reports**: Generate professional research reports for stocks
- **Multi-Parameter Input**: Company code, sector code, and report type parameters
- **Dynamic Prompts**: Fetches relevant data from `Prompts.json` configuration
- **Professional Structure**: Tailored reports based on report type (BUY/HOLD/SELL/RESEARCH)
- **FastAPI Integration**: RESTful API for easy integration
- **Memory Support**: Maintains conversation context across requests

## Architecture

The application consists of:

1. **Equity Research Tool**: Fetches company, sector, and report type data from JSON
2. **Agent Node**: Professional equity analyst that generates structured reports
3. **Summary Node**: Dedicated LLM node for final report summarization
4. **FastAPI Server**: Web API layer for external access
5. **Prompts.json**: Configuration file with company, sector, and report type data

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key:
```bash
set OPENAI_API_KEY=your_api_key_here
```

3. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /research
Research a topic and get summarized results.

**Request Body:**
```json
{
    "query": "What are the latest developments in AI?",
    "thread_id": "user123"
}
```

**Response:**
```json
{
    "result": "Summary of research findings...",
    "thread_id": "user123",
    "status": "success"
}
```

### GET /
Health check endpoint.

### GET /health
Service health status.

## Usage Examples

### Using cURL:
```bash
curl -X POST "http://localhost:8000/research" \
     -H "Content-Type: application/json" \
     -d '{"query": "Research the latest trends in machine learning", "thread_id": "session1"}'
```

### Using Python requests:
```python
import requests

response = requests.post(
    "http://localhost:8000/research",
    json={
        "query": "What are the benefits of renewable energy?",
        "thread_id": "user456"
    }
)

print(response.json())
```

## Graph Flow

1. User sends query → Agent Node
2. Agent decides to use research tool → Tools Node
3. Tool executes and returns results → Agent Node
4. Agent processes results → Summary Node
5. Summary Node creates final response → End

## Customization

- Modify `research_tool` in `graph.py` to integrate with real research APIs
- Adjust the summary prompt in `summarize_results` function
- Add more tools by extending the `tools` list
- Customize the LLM model and parameters in `init_chat_model`
