from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from vector_store import get_research_vectorstore
from typing import TypedDict, Annotated
import re

# Enhanced state to track the workflow progress
class ResearchState(TypedDict):
    messages: Annotated[list, "The conversation messages"]
    company_code: str
    sector_code: str
    report_type: str
    research_context: str
    first_cut_report: str
    feedback: str
    final_report: str
    analyst_iterations: int

def initialize_research(state):
    """Initialize the research process by getting context from ChromaDB"""
    messages = state["messages"]
    company_code = state.get("company_code", "")
    sector_code = state.get("sector_code", "")
    report_type = state.get("report_type", "")
    
    print(f"DEBUG: initialize_research - Company: {company_code}, Sector: {sector_code}, Report: {report_type}")
    
    # Get relevant context from ChromaDB
    vectorstore = get_research_vectorstore()
    context = ""
    
    if company_code and company_code != "UNKNOWN":
        print(f"DEBUG: Retrieving context for company: {company_code}")
        context = vectorstore.get_context_for_company(company_code)
        print(f"DEBUG: Retrieved context length: {len(context)} characters")
    
    return {
        "messages": messages,
        "company_code": company_code,
        "sector_code": sector_code,
        "report_type": report_type,
        "research_context": context,
        "first_cut_report": "",
        "feedback": "",
        "final_report": "",
        "analyst_iterations": 0
    }

def equity_research_analyst(state):
    """Junior Equity Research Analyst - generates reports using RAG context"""
    messages = state["messages"]
    company_code = state.get("company_code", "")
    context = state.get("research_context", "")
    feedback = state.get("feedback", "")
    iterations = state.get("analyst_iterations", 0)
    
    print(f"DEBUG: Equity Research Analyst - Iteration {iterations + 1}")
    
    # Extract user message content (handle both tuple and message object formats)
    user_request = ""
    if messages and len(messages) > 0:
        if isinstance(messages[0], tuple):
            user_request = messages[0][1]  # For ("user", content) format
        else:
            user_request = messages[0].content  # For message object format
    
    # Determine if this is first cut or final report
    is_final_report = iterations > 0 and feedback
    
    if is_final_report:
        system_content = f"""You are a Junior Equity Research Analyst. You are revising your research report based on senior analyst feedback.

ORIGINAL USER REQUEST:
{user_request}

SENIOR ANALYST FEEDBACK:
{feedback}

RESEARCH CONTEXT:
=== RESEARCH CONTEXT ===
{context}
=== END CONTEXT ===

Please revise your report addressing all the feedback points. Generate a comprehensive, well-structured FINAL research report that incorporates the senior analyst's suggestions.

Use professional formatting with clear sections, bullet points, and actionable insights.
Make sure to address every concern raised in the feedback.
"""
    else:
        system_content = f"""You are a Junior Equity Research Analyst. Generate a comprehensive first-cut equity research report using the provided research context.

USER REQUEST:
{user_request}

RESEARCH CONTEXT:
=== RESEARCH CONTEXT ===
{context}
=== END CONTEXT ===

Generate a detailed first-cut research report with the following structure:
1. Executive Summary
2. Company Overview  
3. Financial Analysis
4. Investment Thesis
5. Risks and Considerations
6. Recommendation

Use professional formatting with clear sections, bullet points, and actionable insights.
Base your analysis on the research context provided above.
"""
    
    system_message = SystemMessage(content=system_content)
    model = init_chat_model("groq:llama3-8b-8192", temperature=0.7)
    
    # Create proper message for the model
    user_message = HumanMessage(content=user_request)
    response = model.invoke([system_message, user_message])
    report_content = response.content
    
    updated_state = {
        "messages": state["messages"],
        "company_code": company_code,
        "sector_code": state.get("sector_code", ""),
        "report_type": state.get("report_type", ""),
        "research_context": context,
        "analyst_iterations": iterations + 1
    }
    
    if is_final_report:
        print(f"DEBUG: Generated FINAL report")
        updated_state["final_report"] = report_content
        updated_state["first_cut_report"] = state.get("first_cut_report", "")
        updated_state["feedback"] = feedback
    else:
        print(f"DEBUG: Generated FIRST CUT report")
        updated_state["first_cut_report"] = report_content
        updated_state["feedback"] = ""
        updated_state["final_report"] = ""
    
    return updated_state

def senior_equity_research_analyst(state):
    """Senior Equity Research Analyst - reviews and provides feedback"""
    first_cut_report = state.get("first_cut_report", "")
    company_code = state.get("company_code", "")
    context = state.get("research_context", "")
    messages = state["messages"]
    
    print(f"DEBUG: Senior Equity Research Analyst - Reviewing first cut report")
    
    # Extract user message content (handle both tuple and message object formats)
    user_request = ""
    if messages and len(messages) > 0:
        if isinstance(messages[0], tuple):
            user_request = messages[0][1]  # For ("user", content) format
        else:
            user_request = messages[0].content  # For message object format
    
    system_content = f"""You are a Senior Equity Research Analyst with 15+ years of experience. 
Your role is to review the junior analyst's first-cut report and provide constructive feedback.

ORIGINAL USER REQUEST:
{user_request}

COMPANY: {company_code}

RESEARCH CONTEXT:
=== RESEARCH CONTEXT ===
{context}
=== END CONTEXT ===

JUNIOR ANALYST'S FIRST CUT REPORT:
=== REPORT TO REVIEW ===
{first_cut_report}
=== END REPORT ===

Please provide detailed, constructive feedback focusing on:
1. Accuracy of financial analysis
2. Completeness of risk assessment
3. Quality of investment thesis
4. Use of research context and data
5. Report structure and presentation
6. Missing critical information
7. Specific improvements needed

Be specific about what needs to be corrected, enhanced, or added. 
Provide actionable suggestions for improvement.
"""
    
    system_message = SystemMessage(content=system_content)
    model = init_chat_model("groq:llama3-8b-8192", temperature=0.3)  # Lower temperature for more consistent feedback
    
    response = model.invoke([system_message])
    feedback_content = response.content
    
    print(f"DEBUG: Generated feedback for first cut report")
    
    return {
        "messages": state["messages"],
        "company_code": company_code,
        "sector_code": state.get("sector_code", ""),
        "report_type": state.get("report_type", ""),
        "research_context": context,
        "first_cut_report": first_cut_report,
        "feedback": feedback_content,
        "final_report": "",
        "analyst_iterations": state.get("analyst_iterations", 0)
    }

def should_continue_to_senior(state):
    """Determine if we should go to senior analyst (after first cut)"""
    iterations = state.get("analyst_iterations", 0)
    return "senior_analyst" if iterations == 1 else "finalize"

def should_continue_to_final(state):
    """Determine if we should go to final report (after feedback)"""
    iterations = state.get("analyst_iterations", 0)
    return "junior_analyst" if iterations == 1 else "finalize"

def finalize_research(state):
    """Finalize the research process and return the appropriate report"""
    final_report = state.get("final_report", "")
    first_cut_report = state.get("first_cut_report", "")
    
    # Return the final report if available, otherwise the first cut
    report_to_return = final_report if final_report else first_cut_report
    
    print(f"DEBUG: Finalizing research - returning {'final' if final_report else 'first cut'} report")
    
    return {
        "messages": [AIMessage(content=report_to_return)]
    }

def create_research_graph():
    """Create and return the multi-agent research graph."""
    
    # Create the state graph with custom ResearchState
    workflow = StateGraph(ResearchState)
    
    # Add nodes for the workflow
    workflow.add_node("initialize", initialize_research)
    workflow.add_node("junior_analyst", equity_research_analyst)
    workflow.add_node("senior_analyst", senior_equity_research_analyst)
    workflow.add_node("finalize", finalize_research)
    
    # Define the workflow edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "junior_analyst")
    
    # Conditional routing after junior analyst
    workflow.add_conditional_edges(
        "junior_analyst",
        should_continue_to_senior,
        {
            "senior_analyst": "senior_analyst",
            "finalize": "finalize"
        }
    )
    
    # After senior analyst feedback, go back to junior analyst for final report
    workflow.add_edge("senior_analyst", "junior_analyst")
    
    # End the workflow after finalization
    workflow.add_edge("finalize", END)
    
    # Add memory
    memory = MemorySaver()
    
    # Compile the graph
    app = workflow.compile(checkpointer=memory)
    
    return app
