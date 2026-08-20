import os
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Security Exercise API",
    description="API con anti-patrón de autenticación estática mediante x-api-key",
    version="1.0.0"
)

# Configuración de CORS obligatoria para peticiones entre orígenes/carpetas distintas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clave de API estática configurada (se puede modificar vía variable de entorno API_KEY)
STATIC_API_KEY = os.getenv("API_KEY", "mi-clave-secreta-123")


def require_api_key(x_api_key: Optional[str] = Header(None, alias="x-api-key")):
    """
    Verifica la presencia y validez del encabezado 'x-api-key'.
    Anti-patrón de seguridad: comparación de clave estática directa recibida del cliente.
    """
    # 1. ¿Contiene la petición el encabezado x-api-key?
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header 'x-api-key' no proporcionado"
        )

    # 2. ¿El valor es correcto?
    if x_api_key != STATIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida"
        )

    return x_api_key


# 1. Health endpoint (Público - Sin API Key)
@app.get("/health")
def get_health():
    return {
        "status": "ok"
    }


# 2. Protected GET endpoint (Requiere x-api-key)
@app.get("/api/data", dependencies=[Depends(require_api_key)])
def get_protected_data():
    return {
        "message": "Protected data",
        "course": "Security Exercise",
        "status": "success"
    }


# 3. Protected POST endpoint (Requiere x-api-key)
@app.post("/api/data", dependencies=[Depends(require_api_key)])
def post_protected_data():
    # El cuerpo (body) de la petición se ignora para este ejercicio
    return {
        "message": "POST received"
    }