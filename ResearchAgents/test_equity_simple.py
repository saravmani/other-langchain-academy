import requests
import json

# Test the Simplified Equity Research Agent API

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("Health Check:", response.json())
    except Exception as e:
        print(f"Health check failed: {e}")

def test_equity_research(company_code, sector_code, report_type, thread_id="test_session"):
    """Test the equity research endpoint"""
    payload = {
        "company_code": company_code,
        "sector_code": sector_code,
        "report_type": report_type,
        "thread_id": thread_id
    }
    
    print(f"\n{'='*60}")
    print(f"Testing: {company_code} ({sector_code}) - {report_type}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(f"{BASE_URL}/research", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Company: {result['company_code']}")
            print(f"Sector: {result['sector_code']}")
            print(f"Report Type: {result['report_type']}")
            print(f"Thread ID: {result['thread_id']}")
            print(f"Status: {result['status']}")
            print("\n📊 RESEARCH REPORT:")
            print("-" * 40)
            print(result['result'])
            print("-" * 40)
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Equity Research Agent Tests")
    print("="*60)
    
    # Test health endpoint
    test_health()
    
    # Test different equity research scenarios
    test_scenarios = [
        # (company_code, sector_code, report_type)
        ("AAPL", "IT", "FirstCutReport"),
        ("AAPL", "IT", "BuyReport"),
        ("MSFT", "IT", "FirstCutReport"),
        ("TSLA", "AUTO", "BuyReport"),
        ("NVDA", "IT", "FirstCutReport"),
    ]
    
    for company_code, sector_code, report_type in test_scenarios:
        test_equity_research(company_code, sector_code, report_type)
    
    print(f"\n{'='*60}")
    print("✅ Testing completed!")
    print(f"{'='*60}")
