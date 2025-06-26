import requests
import json

# Test the Research Agent API

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())

def test_research(query, thread_id="test_session"):
    """Test the research endpoint"""
    payload = {
        "query": query,
        "thread_id": thread_id
    }
    
    print(f"\nTesting query: {query}")
    
    # Test regular endpoint
    response = requests.post(f"{BASE_URL}/research", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("Success!")
        print(f"Result: {result['result']}")
        print(f"Thread ID: {result['thread_id']}")
        print(f"Status: {result['status']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
    # Test debug endpoint
    print("\n--- DEBUG INFO ---")
    debug_response = requests.post(f"{BASE_URL}/research-debug", json=payload)
    if debug_response.status_code == 200:
        debug_result = debug_response.json()
        print(f"Debug events: {len(debug_result['events'])}")
        for i, event in enumerate(debug_result['events']):
            print(f"Event {i}: {event}")
    else:
        print(f"Debug error: {debug_response.status_code}")
        print(debug_response.text)

if __name__ == "__main__":
    # Test health endpoint
    test_health()
    
    # Test research queries
    test_queries = [
        "What is the weather like today?",
        "Tell me about recent technology trends",
        "Research the benefits of artificial intelligence",
        "What are the latest scientific discoveries?"
    ]
    
    for query in test_queries:
        test_research(query)
        print("-" * 50)
