from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver

# Define the dummy tool
@tool
def research_tool(query: str) -> str:
    """
    A dummy research tool that simulates doing research on a topic.
    
    Args:
        query: The research query to investigate
        
    Returns:
        A simulated research result
    """
    print(f"🔍 Researching: {query}")
    
    # Simulate different types of research results
    dummy_results = {
        "weather": "Based on current data, the weather is generally pleasant with mild temperatures.",
        "technology": "Recent technological advances show promising developments in AI and automation.",
        "science": "Scientific research indicates significant progress in various fields including medicine and physics.",
        "default": f"Research completed on '{query}'. Found relevant information and key insights."
    }
    
    # Simple keyword matching for demo purposes
    for keyword, result in dummy_results.items():
        if keyword.lower() in query.lower():
            return result
    
    return dummy_results["default"]

# Initialize tools and model
tools = [research_tool]
tool_node = ToolNode(tools)

# Initialize the LLM
model = init_chat_model("openai:gpt-3.5-turbo", temperature=0.7)
model_with_tools = model.bind_tools(tools)

def should_continue(state):
    """Determine whether to continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    print(f"DEBUG: Last message type: {type(last_message)}")
    print(f"DEBUG: Has tool calls: {hasattr(last_message, 'tool_calls')}")
    if hasattr(last_message, 'tool_calls'):
        print(f"DEBUG: Tool calls: {last_message.tool_calls}")
    
    # If there are tool calls, continue to tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print("DEBUG: Going to tools")
        return "tools"
    # Otherwise, go to summary
    print("DEBUG: Going to summary")
    return "summary"

def call_model(state):
    """Call the model with tools."""
    messages = state["messages"]
    
    print(f"DEBUG: call_model - input messages count: {len(messages)}")
    
    # Add system message for research agent behavior
    system_message = SystemMessage(content="""You are a helpful research assistant. 
    When users ask questions, use the research_tool to gather information, then provide a comprehensive summary.
    Always use the research tool for any query that requires information gathering.""")
    
    # Combine system message with user messages
    full_messages = [system_message] + messages
    
    response = model_with_tools.invoke(full_messages)
    print(f"DEBUG: call_model - response type: {type(response)}")
    print(f"DEBUG: call_model - response has tool_calls: {hasattr(response, 'tool_calls')}")
    if hasattr(response, 'tool_calls'):
        print(f"DEBUG: call_model - tool_calls: {response.tool_calls}")
    
    return {"messages": [response]}

def summarize_results(state):
    """Summarize the research results."""
    messages = state["messages"]
    
    print(f"DEBUG: summarize_results - input messages count: {len(messages)}")
    
    # Create a summary prompt
    summary_prompt = """Based on the research conducted above, please provide a clear and concise summary of the findings. 
    Focus on the key insights and present them in a well-structured format."""
    
    # Get the conversation history for context
    conversation_context = "\n".join([
        f"{msg.type}: {msg.content}" for msg in messages[-5:] 
        if hasattr(msg, 'content') and msg.content
    ])
    
    summary_message = f"{conversation_context}\n\n{summary_prompt}"
    
    response = model.invoke([SystemMessage(content="You are a helpful assistant that summarizes research findings clearly and concisely."), 
                           ("user", summary_message)])
    
    print(f"DEBUG: summarize_results - response content: {response.content[:100]}...")
    
    return {"messages": [response]}

def create_research_graph():
    """Create and return the research graph."""
    
    # Create the state graph
    workflow = StateGraph(MessagesState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_node("summary", summarize_results)
    
    # Set up the graph flow
    workflow.add_edge(START, "agent")
    
    # Add conditional edges from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "summary": "summary"
        }
    )
    
    # After tools, go back to agent for processing
    workflow.add_edge("tools", "agent")
    
    # Summary ends the workflow
    workflow.add_edge("summary", END)
    
    # Add memory
    memory = MemorySaver()
    
    # Compile the graph
    app = workflow.compile(checkpointer=memory)
    
    return app
