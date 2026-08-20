# Security Exercise - Backend API (Part 1)

API built with **Python** and **FastAPI** to demonstrate the security anti-pattern of static API key authentication passed via HTTP headers.

## 🚀 Prerequisites

- Python 3.10+
- Activated virtual environment

## 📦 Dependency Installation

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

By default, the expected static API key is `my-secret-key-123`.
You can change it by setting the `API_KEY` environment variable:

```bash
# On Windows (PowerShell)
$env:API_KEY="your_custom_key"

# On Linux/Mac
export API_KEY="your_custom_key"
```

## ▶️ Running the Local Server

Run the development server with auto-reload:

```bash
uvicorn main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`.
Interactive documentation is available at `http://localhost:8000/docs`.

---

## 📌 Endpoints

| Method | Endpoint | Requires API Key | Required Header | Expected Response |
|---|---|---|---|---|
| `GET` | `/health` | ❌ No | None | `{"status": "ok"}` |
| `GET` | `/api/data` | ✅ Yes | `x-api-key: my-secret-key-123` | JSON with protected data |
| `POST` | `/api/data` | ✅ Yes | `x-api-key: my-secret-key-123` | `{"message": "POST received"}` |

---

## 🧪 Testing the Endpoints

### Automated Test Suite
Run the test script directly:
```bash
python test_api.py
```

### Manual Testing

#### 1. Health Check (GET `/health`)
**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
```
**cURL:**
```bash
curl -X GET "http://localhost:8000/health"
```

---

#### 2. Protected GET (GET `/api/data`)

**With valid API Key:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/data" -Method Get -Headers @{"x-api-key"="my-secret-key-123"}
```
```bash
curl -X GET "http://localhost:8000/api/data" -H "x-api-key: my-secret-key-123"
```

**Without API Key or with invalid key (Returns 401 Unauthorized):**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/data" -Method Get
```
```bash
curl -X GET "http://localhost:8000/api/data"
```

---

#### 3. Protected POST (POST `/api/data`)

**With valid API Key:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/data" -Method Post -Headers @{"x-api-key"="my-secret-key-123"}
```
```bash
curl -X POST "http://localhost:8000/api/data" -H "x-api-key: my-secret-key-123"
```

---

## 🛡️ Security Anti-Pattern

This exercise demonstrates the following validation flow:
1. The client sends `x-api-key: SECRET` in the header.
2. The server directly compares the value against a hardcoded/static key.
3. If missing or mismatched -> `401 Unauthorized`.
4. If matched -> Returns the protected data.

