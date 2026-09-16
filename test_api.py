"""
Automated test script to verify API endpoints, dynamic secret authentication, and database encryption.
"""
import os
from fastapi.testclient import TestClient
from main import app, get_expected_api_secret

client = TestClient(app)

def run_tests():
    api_secret = get_expected_api_secret()

    print("--- 1. Testing GET /health ---")
    res = client.get("/health")
    assert res.status_code == 200, f"Error: expected 200, got {res.status_code}"
    print("[OK] GET /health OK:", res.json())

    print("\n--- 2. Testing GET /api/data without API Key ---")
    res = client.get("/api/data")
    assert res.status_code == 401, f"Error: expected 401, got {res.status_code}"
    print("[OK] GET /api/data without key rejected with 401 Unauthorized:", res.json())

    print("\n--- 3. Testing GET /api/data with invalid API Key ---")
    res = client.get("/api/data", headers={"x-api-key": "invalid-wrong-secret"})
    assert res.status_code == 401, f"Error: expected 401, got {res.status_code}"
    print("[OK] GET /api/data with invalid key rejected with 401 Unauthorized:", res.json())

    print("\n--- 4. Testing GET /api/data with valid dynamic API Key ---")
    res = client.get("/api/data", headers={"x-api-key": api_secret})
    assert res.status_code == 200, f"Error: expected 200, got {res.status_code}"
    data = res.json()
    assert "decrypted_content" in data
    assert "database_raw_ciphertext" in data
    print("[OK] GET /api/data with valid key returned decrypted record:", data["decrypted_content"])

    print("\n--- 5. Testing POST /api/data with valid dynamic API Key ---")
    res = client.post(
        "/api/data",
        headers={"x-api-key": api_secret},
        json={"message": "Test confidential message"}
    )
    assert res.status_code == 200, f"Error: expected 200, got {res.status_code}"
    assert res.json()["status"] == "success"
    print("[OK] POST /api/data encrypted & stored record successfully")

    print("\n--- 6. Testing GET /api/status ---")
    res = client.get("/api/status")
    assert res.status_code == 200, f"Error: expected 200, got {res.status_code}"
    print("[OK] GET /api/status:", res.json())

    print("\n[SUCCESS] All basic backend integration tests passed successfully!")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"[ERROR] Test error: {e}")

