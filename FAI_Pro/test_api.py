"""
Test script for the Irish Housing AI Assistant API.
Tests all endpoints: health, meta, and chat (SSE streaming).
"""
import requests
import json
import sseclient

base = "http://localhost:8000"

# 1. Health check
print("=== /health ===")
r = requests.get(f"{base}/health")
print(json.dumps(r.json(), indent=2))

# 2. Counties
print("\n=== /api/meta/counties ===")
r = requests.get(f"{base}/api/meta/counties")
data = r.json()
print(f"Total counties: {len(data['counties'])}")
print("Sample:", data["counties"][:5])

# 3. Years
print("\n=== /api/meta/years ===")
r = requests.get(f"{base}/api/meta/years")
data = r.json()
print("Years:", data["years"])

# 4. Chat endpoint — General greeting
print("\n=== /api/chat (general greeting) ===")
payload = {"query": "Hello! What can you help me with?", "session_id": "test-session-1"}
with requests.post(f"{base}/api/chat", json=payload, stream=True) as resp:
    for line in resp.iter_lines():
        if line and line.startswith(b"data: "):
            event = json.loads(line[6:])
            if event.get("type") == "status":
                print(f"  [STATUS] {event['message']}")
            elif event.get("type") == "data":
                print(f"  [ANSWER] {event['answer'][:300]}...")
                print(f"  [INTENT] {event.get('intent')}")
            elif event.get("type") == "error":
                print(f"  [ERROR] {event['message']}")

# 5. Chat endpoint — Rent query
print("\n=== /api/chat (rent query - Dublin) ===")
payload = {"query": "What is the average rent in Dublin?", "session_id": "test-session-2"}
with requests.post(f"{base}/api/chat", json=payload, stream=True) as resp:
    for line in resp.iter_lines():
        if line and line.startswith(b"data: "):
            event = json.loads(line[6:])
            if event.get("type") == "status":
                print(f"  [STATUS] {event['message']}")
            elif event.get("type") == "data":
                print(f"  [ANSWER] {event['answer'][:400]}...")
                print(f"  [INTENT] {event.get('intent')}")
                print(f"  [CHART]  {event.get('chart_data')}")
                print(f"  [SOURCES count] {len(event.get('sources', []))}")
            elif event.get("type") == "error":
                print(f"  [ERROR] {event['message']}")

# 6. Chat endpoint — County comparison
print("\n=== /api/chat (comparison query) ===")
payload = {"query": "Compare rent in Cork vs Galway", "session_id": "test-session-3"}
with requests.post(f"{base}/api/chat", json=payload, stream=True) as resp:
    for line in resp.iter_lines():
        if line and line.startswith(b"data: "):
            event = json.loads(line[6:])
            if event.get("type") == "status":
                print(f"  [STATUS] {event['message']}")
            elif event.get("type") == "data":
                print(f"  [ANSWER] {event['answer'][:400]}...")
                print(f"  [INTENT] {event.get('intent')}")
                print(f"  [CHART]  {event.get('chart_data')}")
            elif event.get("type") == "error":
                print(f"  [ERROR] {event['message']}")

# 7. Chat endpoint — Trend analysis
print("\n=== /api/chat (trend analysis) ===")
payload = {"query": "Show me the rent trend in Limerick over the years", "session_id": "test-session-4"}
with requests.post(f"{base}/api/chat", json=payload, stream=True) as resp:
    for line in resp.iter_lines():
        if line and line.startswith(b"data: "):
            event = json.loads(line[6:])
            if event.get("type") == "status":
                print(f"  [STATUS] {event['message']}")
            elif event.get("type") == "data":
                print(f"  [ANSWER] {event['answer'][:400]}...")
                print(f"  [INTENT] {event.get('intent')}")
                print(f"  [CHART]  {event.get('chart_data')}")
            elif event.get("type") == "error":
                print(f"  [ERROR] {event['message']}")

print("\n=== ALL TESTS COMPLETE ===")
