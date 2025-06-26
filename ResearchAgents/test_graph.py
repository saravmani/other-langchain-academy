import os
os.environ["OPENAI_API_KEY"] = "your_key_here"  # Replace with actual key

from graph import create_research_graph

def test_graph_directly():
    """Test the graph directly without FastAPI"""
    print("Creating research graph...")
    graph = create_research_graph()
    
    print("Running graph with test query...")
    config = {"configurable": {"thread_id": "test"}}
    
    query = "What is the weather like?"
    print(f"Query: {query}")
    
    try:
        for event in graph.stream({"messages": [("user", query)]}, config):
            print(f"Event: {event}")
            if "messages" in event:
                for msg in event["messages"]:
                    print(f"  Message type: {type(msg)}")
                    print(f"  Message content: {getattr(msg, 'content', 'No content')}")
                    if hasattr(msg, 'tool_calls'):
                        print(f"  Tool calls: {msg.tool_calls}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_graph_directly()
