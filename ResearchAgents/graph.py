from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from vector_store import get_research_vectorstore
import re

# Simple equity research with ChromaDB context - prompt comes from main_fixed.py
def call_model(state):
    """Generate equity research report using the provided prompt and ChromaDB context."""
    messages = state["messages"]
    
    print(f"DEBUG: call_model - input messages count: {len(messages)}")
    
    # Extract company code from the user message/prompt
    user_message = messages[0].content if messages else ""
    company_code = extract_company_code_from_prompt(user_message)
    
    # Get relevant context from ChromaDB
    vectorstore = get_research_vectorstore()
    context = ""
    
    if company_code:
        print(f"DEBUG: Retrieving context for company: {company_code}")
        context = vectorstore.get_context_for_company(company_code)
        print(f"DEBUG: Retrieved context length: {len(context)} characters")
    
    # Enhanced system message with context
    system_content = f"""You are a professional equity research analyst. 
    Generate a comprehensive, well-structured research report based on the specific instructions provided.
    Use professional formatting with clear sections, bullet points, and actionable insights.
    
    {"IMPORTANT: Use the following research context to enhance your analysis with factual data and insights:" if context else ""}
    
    {"=== RESEARCH CONTEXT ===" if context else ""}
    {context if context else ""}
    {"=== END CONTEXT ===" if context else ""}
    
    Based on the research context above and your knowledge, provide a detailed and accurate analysis.
    Ensure your recommendations are well-supported by the available data.
    """
    
    system_message = SystemMessage(content=system_content)
    
    # Initialize the LLM with Groq and Llama3-8b-8192
    model = init_chat_model("groq:llama3-8b-8192", temperature=0.7)
    
    # Combine system message with user messages
    full_messages = [system_message] + messages
    
    response = model.invoke(full_messages)
    print(f"DEBUG: call_model - response generated successfully")
    
    return {"messages": [response]}

def extract_company_code_from_prompt(prompt: str) -> str:
    """Extract company code from the prompt text"""
    # Common patterns to look for company codes
    patterns = [
        r'\b(AAPL|MSFT|GOOGL|AMZN|TSLA|NVDA|META)\b',  # Specific codes
        r'Apple Inc\.|Apple',  # Apple variations
        r'Microsoft Corporation|Microsoft',  # Microsoft variations
        r'Alphabet Inc\.|Google|Alphabet',  # Google/Alphabet variations
    ]
    
    # Company code mapping
    company_mapping = {
        'Apple': 'AAPL',
        'Microsoft': 'MSFT', 
        'Google': 'GOOGL',
        'Alphabet': 'GOOGL',
        'Amazon': 'AMZN',
        'Tesla': 'TSLA',
        'NVIDIA': 'NVDA',
        'Meta': 'META'
    }
    
    prompt_upper = prompt.upper()
    
    # First try direct ticker matches
    for pattern in patterns:
        matches = re.findall(pattern, prompt_upper)
        if matches:
            match = matches[0]
            return company_mapping.get(match, match)
    
    # If no direct match, try company name mapping
    for company_name, ticker in company_mapping.items():
        if company_name.upper() in prompt_upper:
            return ticker
    
    return None

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
