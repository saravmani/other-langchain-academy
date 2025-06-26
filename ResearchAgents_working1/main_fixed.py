from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from graph import create_research_graph

app = FastAPI(title="Research Agent API", version="1.0.0")

# Pydantic models for request/response
class ResearchRequest(BaseModel):
    query: str
    thread_id: str = "default"

class ResearchResponse(BaseModel):
    result: str
    thread_id: str
    status: str

# Initialize the graph
research_graph = create_research_graph()

@app.get("/")
async def root():
    return {"message": "Research Agent API is running!"}

@app.post("/research", response_model=ResearchResponse)
async def research_query(request: ResearchRequest):
    """
    Process a research query using the LangGraph agent
    """
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Run the graph and get the final state
        final_result = None
        
        # Use stream_mode="values" to get the final state values
        for state in research_graph.stream(
            {"messages": [("user", request.query)]}, 
            config,
            stream_mode="values"
        ):
            print(f"DEBUG API: State keys: {list(state.keys())}")
            if "messages" in state:
                messages = state["messages"]
                print(f"DEBUG API: Found {len(messages)} total messages")
                
                # Get the last AI message
                for msg in reversed(messages):
                    if (hasattr(msg, 'content') and 
                        msg.content and 
                        hasattr(msg, 'type') and 
                        msg.type == 'ai'):
                        final_result = msg.content
                        print(f"DEBUG API: Found AI message: {msg.content[:100]}...")
                        break
        
        return ResearchResponse(
            result=final_result or "No result generated",
            thread_id=request.thread_id,
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/research-debug", response_model=dict)
async def research_query_debug(request: ResearchRequest):
    """
    Debug version that shows all events and messages
    """
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        
        events = []
        for event in research_graph.stream(
            {"messages": [("user", request.query)]}, 
            config
        ):
            # Convert event to serializable format
            event_info = {
                "event_keys": list(event.keys()),
                "messages_count": len(event.get("messages", [])) if "messages" in event else 0
            }
            
            if "messages" in event:
                messages_info = []
                for msg in event["messages"]:
                    msg_info = {
                        "type": getattr(msg, 'type', 'unknown'),
                        "content": getattr(msg, 'content', '')[:200] + "..." if len(getattr(msg, 'content', '')) > 200 else getattr(msg, 'content', ''),
                        "has_tool_calls": hasattr(msg, 'tool_calls') and bool(msg.tool_calls)
                    }
                    messages_info.append(msg_info)
                event_info["messages"] = messages_info
            
            events.append(event_info)
        
        return {"events": events}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
