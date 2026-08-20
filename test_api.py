"""
Automated test script to verify the API endpoints.
"""
from fastapi.testclient import TestClient
from main import app, STATIC_API_KEY

client = TestClient(app)

def run_tests():
    print("--- 1. Testing GET /health ---")
    res = client.get("/health")
    assert res.status_code == 200, f"Error: expected 200, got {res.status_code}"
    assert res.json() == {"status": "ok"}, f"Unexpected response: {res.json()}"
    print("[OK] GET /health OK:", res.json())

    print("\n--- 2. Testing GET /api/data without API Key ---")
    res = client.get("/api/data")
    assert res.status_code == 401, f"Error: expected 401, got {res.status_code}"
    print("[OK] GET /api/data without key rejected with 401 Unauthorized:", res.json())

    print("\n--- 3. Testing GET /api/data with invalid API Key ---")
    res = client.get("/api/data", headers={"x-api-key": "invalid-key"})
    assert res.status_code == 401, f"Error: expected 401, got {res.status_code}"
    print("[OK] GET /api/data with invalid key rejected with 401 Unauthorized:", res.json())

    print("\n--- 4. Testing GET /api/data with valid API Key ---")
    res = client.get("/api/data", headers={"x-api-key": STATIC_API_KEY})
    assert res.status_code == 200, f"Error: expected 200, got {res.status_code}"
    expected_data = {
        "message": "Protected data",
        "course": "Security Exercise",
        "status": "success"
    }
    assert res.json() == expected_data, f"Unexpected response: {res.json()}"
    print("[OK] GET /api/data with valid key OK:", res.json())

    print("\n--- 5. Testing POST /api/data without API Key ---")
    res = client.post("/api/data")
    assert res.status_code == 401, f"Error: expected 401, got {res.status_code}"
    print("[OK] POST /api/data without key rejected with 401 Unauthorized:", res.json())

    print("\n--- 6. Testing POST /api/data with valid API Key ---")
    res = client.post("/api/data", headers={"x-api-key": STATIC_API_KEY})
    assert res.status_code == 200, f"Error: expected 200, got {res.status_code}"
    assert res.json() == {"message": "POST received"}, f"Unexpected response: {res.json()}"
    print("[OK] POST /api/data with valid key OK:", res.json())

    print("\n[SUCCESS] All tests passed successfully!")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"[ERROR] Test error: {e}")
