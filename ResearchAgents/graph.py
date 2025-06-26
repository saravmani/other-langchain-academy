from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver

# Simple equity research without tools - prompt comes from main_fixed.py
def call_model(state):
    """Generate equity research report directly using the provided prompt."""
    messages = state["messages"]
    
    print(f"DEBUG: call_model - input messages count: {len(messages)}")
    
    # The user message already contains the specific prompt from main_fixed.py
    # Just add a system message for professional formatting
    system_message = SystemMessage(content="""You are a professional equity research analyst. 
    Generate a comprehensive, well-structured research report based on the specific instructions provided. 
    Use professional formatting with clear sections, bullet points, and actionable insights.""")
    
    # Initialize the LLM
    model = init_chat_model("openai:gpt-3.5-turbo", temperature=0.7)
    
    # Combine system message with user messages
    full_messages = [system_message] + messages
    
    response = model.invoke(full_messages)
    print(f"DEBUG: call_model - response generated successfully")
    
    return {"messages": [response]}

def create_research_graph():
    """Create and return the simplified research graph."""
    
    # Create the state graph
    workflow = StateGraph(MessagesState)
    
    # Add single node - no tools needed
    workflow.add_node("agent", call_model)
    
    # Simple flow: START -> agent -> END
    workflow.add_edge(START, "agent")
    workflow.add_edge("agent", END)
    
    # Add memory
    memory = MemorySaver()
    
    # Compile the graph
    app = workflow.compile(checkpointer=memory)
    
    return app
