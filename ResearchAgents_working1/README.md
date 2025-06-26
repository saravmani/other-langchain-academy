# Research Agent API

A simple LangGraph-based research agent exposed via FastAPI.

## Features

- **LangGraph Workflow**: Implements a research agent with tool calling and summarization
- **Dummy Research Tool**: Simulates research functionality for demonstration
- **LLM Summary Node**: Provides intelligent summarization of research results
- **FastAPI Integration**: RESTful API for easy integration
- **Memory Support**: Maintains conversation context across requests

## Architecture

The application consists of:

1. **Research Tool**: A dummy tool that simulates research operations
2. **Agent Node**: LLM that decides when to use tools
3. **Summary Node**: Dedicated LLM node for summarizing findings
4. **FastAPI Server**: Web API layer for external access

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
