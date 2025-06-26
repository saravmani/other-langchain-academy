from langgraph.graph import StateGraph,MessagesState, START, END
from langgraph.types import Command, interrupt
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain.chat_models import init_chat_model 
from pydantic import BaseModel
import sqlite3
import os
from langgraph.checkpoint.sqlite import SqliteSaver

# Create the database file with absolute path
db_path = os.path.join(os.getcwd(), "checkpoints.db")
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.close()
    print(f"Created database file: {db_path}")

conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

@tool
def search(query: str):    
    """Call to surf the web."""
    print(f"Searching ...")
    # This is a placeholder for the actual implementation
    # Don't let the LLM know this though 😊
    return f"I looked up: {query}. Result: It's sunny in San Francisco, but you better look out if you're a Gemini 😈."

tools = [search]
tool_node = ToolNode(tools)
model = init_chat_model("openai:gpt-3.5-turbo", temperature=0.7, max_tokens=1000)

# We are going "bind" all tools to the model
# We have the ACTUAL tools from above, but we also need a mock tool to ask a human
# Since `bind_tools` takes in tools but also just tool definitions,
# We can define a tool definition for `ask_human`
class AskHuman(BaseModel):
    """Ask the human a question"""
    question: str

model = model.bind_tools(tools + [AskHuman])
# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1] # Get the last message in the conversation
    # If there is no function call, then we finish
    if not last_message.tool_calls: # here if not means technically checkes if the list is empty
        return END
    # If tool call is asking Human, we return that node
    # You could also add logic here to let some system know that there's something that requires Human input
    # For example, send a slack message, etc
    elif last_message.tool_calls[0]["name"] == "AskHuman":
        return "ask_human"
    else:
        return "toolcall"


def call_model(state):
    messages = state["messages"]
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}

def ask_human(state):
    print("Asking human for input...")
    tool_call_id = state["messages"][-1].tool_calls[0]["id"]
    ask = AskHuman.model_validate(state["messages"][-1].tool_calls[0]["args"])
    location = interrupt(ask.question)
    tool_message = [{"tool_call_id": tool_call_id, "type": "tool", "content": location}]
    return {"messages": tool_message}

workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("toolcall", tool_node)
workflow.add_node("ask_human", ask_human)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    path_map=["ask_human", "toolcall", END], # means should_continue will return one of these nodes
)
# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("toolcall", "agent")
workflow.add_edge("ask_human", "agent")

# memory = MemorySaver() 
app = workflow.compile(checkpointer=memory)
 
config = {"configurable": {"thread_id": "1"}}

for event in app.stream({"messages": [( "user", "Ask the user where they are, then look up the weather there")]}, config, stream_mode="values"):
    if "messages" in event:
        event["messages"][-1].pretty_print()

for event in app.stream(
    Command(resume="san francisco"),config, stream_mode="values"):
    if "messages" in event:
        event["messages"][-1].pretty_print()