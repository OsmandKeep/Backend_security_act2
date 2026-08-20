"""
Script de pruebas automatizadas para verificar los endpoints de la API.
"""
from fastapi.testclient import TestClient
from main import app, STATIC_API_KEY

client = TestClient(app)

def run_tests():
    print("--- 1. Probando GET /health ---")
    res = client.get("/health")
    assert res.status_code == 200, f"Error: esperó 200, obtuvo {res.status_code}"
    assert res.json() == {"status": "ok"}, f"Respuesta inesperada: {res.json()}"
    print("✅ GET /health OK:", res.json())

    print("\n--- 2. Probando GET /api/data sin API Key ---")
    res = client.get("/api/data")
    assert res.status_code == 401, f"Error: esperó 401, obtuvo {res.status_code}"
    print("✅ GET /api/data sin key rechazado con 401 Unauthorized:", res.json())

    print("\n--- 3. Probando GET /api/data con API Key incorrecta ---")
    res = client.get("/api/data", headers={"x-api-key": "clave-erronea"})
    assert res.status_code == 401, f"Error: esperó 401, obtuvo {res.status_code}"
    print("✅ GET /api/data con key incorrecta rechazado con 401 Unauthorized:", res.json())

    print("\n--- 4. Probando GET /api/data con API Key correcta ---")
    res = client.get("/api/data", headers={"x-api-key": STATIC_API_KEY})
    assert res.status_code == 200, f"Error: esperó 200, obtuvo {res.status_code}"
    expected_data = {
        "message": "Protected data",
        "course": "Security Exercise",
        "status": "success"
    }
    assert res.json() == expected_data, f"Respuesta inesperada: {res.json()}"
    print("✅ GET /api/data con key válida OK:", res.json())

    print("\n--- 5. Probando POST /api/data sin API Key ---")
    res = client.post("/api/data")
    assert res.status_code == 401, f"Error: esperó 401, obtuvo {res.status_code}"
    print("✅ POST /api/data sin key rechazado con 401 Unauthorized:", res.json())

    print("\n--- 6. Probando POST /api/data con API Key correcta ---")
    res = client.post("/api/data", headers={"x-api-key": STATIC_API_KEY})
    assert res.status_code == 200, f"Error: esperó 200, obtuvo {res.status_code}"
    assert res.json() == {"message": "POST received"}, f"Respuesta inesperada: {res.json()}"
    print("✅ POST /api/data con key válida OK:", res.json())

    print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
