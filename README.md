# Security Exercise - Backend API (Part 1)

API construida con **Python** y **FastAPI** para demostrar el anti-patrón de seguridad basado en API Keys estáticas enviadas en encabezados HTTP.

## 🚀 Requisitos previos

- Python 3.10+
- Entorno virtual activado

## 📦 Instalación de dependencias

```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

Por defecto, la clave API estática esperada es `mi-clave-secreta-123`.
Puedes cambiarla configurando la variable de entorno `API_KEY`:

```bash
# En Windows (PowerShell)
$env:API_KEY="tu_clave_personalizada"

# En Linux/Mac
export API_KEY="tu_clave_personalizada"
```

## ▶️ Ejecución del Servidor Local

Ejecuta el servidor en modo desarrollo con recarga automática:

```bash
uvicorn main:app --reload --port 8000
```

El servidor estará disponible en `http://localhost:8000`.
Documentación interactiva disponible en `http://localhost:8000/docs`.

---

## 📌 Endpoints

| Método | Endpoint | Requiere API Key | Header requerido | Respuesta esperada |
|---|---|---|---|---|
| `GET` | `/health` | ❌ No | Ninguno | `{"status": "ok"}` |
| `GET` | `/api/data` | ✅ Sí | `x-api-key: mi-clave-secreta-123` | JSON con datos protegidos |
| `POST` | `/api/data` | ✅ Sí | `x-api-key: mi-clave-secreta-123` | `{"message": "POST received"}` |

---

## 🧪 Pruebas de los Endpoints

### 1. Health Check (GET `/health`)
**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
```
**cURL:**
```bash
curl -X GET "http://localhost:8000/health"
```

---

### 2. Protected GET (GET `/api/data`)

**Con API Key válida:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/data" -Method Get -Headers @{"x-api-key"="mi-clave-secreta-123"}
```
```bash
curl -X GET "http://localhost:8000/api/data" -H "x-api-key: mi-clave-secreta-123"
```

**Sin API Key o clave inválida (Retorna 401 Unauthorized):**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/data" -Method Get
```
```bash
curl -X GET "http://localhost:8000/api/data"
```

---

### 3. Protected POST (POST `/api/data`)

**Con API Key válida:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/data" -Method Post -Headers @{"x-api-key"="mi-clave-secreta-123"}
```
```bash
curl -X POST "http://localhost:8000/api/data" -H "x-api-key: mi-clave-secreta-123"
```

---

## 🛡️ Anti-patrón de Seguridad

Este ejercicio reproduce el siguiente flujo de validación:
1. El cliente envía `x-api-key: SECRET` en la cabecera.
2. El servidor compara directamente el valor contra una clave fija.
3. Si no existe o no coincide -> `401 Unauthorized`.
4. Si coincide -> Retorna los datos protegidos.
