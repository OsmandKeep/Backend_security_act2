import os
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Security Exercise API",
    description="API demonstrating static x-api-key authentication anti-pattern",
    version="1.0.0"
)

# Mandatory CORS configuration for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configured static API Key (can be overridden via API_KEY environment variable)
STATIC_API_KEY = os.getenv("API_KEY", "my-secret-key")


def require_api_key(x_api_key: Optional[str] = Header(None, alias="x-api-key")):
    """
    Validates the presence and authenticity of the 'x-api-key' header.
    Security anti-pattern: direct comparison with static key received from the client.
    """
    # 1. Does the request contain the x-api-key header?
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header 'x-api-key' not provided"
        )

    # 2. Is the value correct?
    if x_api_key != STATIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

    return x_api_key


# 1. Health endpoint (Public - No API Key)
@app.get("/health")
def get_health():
    return {
        "status": "ok"
    }


# 2. Protected GET endpoint (Requires x-api-key)
@app.get("/api/data", dependencies=[Depends(require_api_key)])
def get_protected_data():
    return {
        "message": "Protected data",
        "course": "Security Exercise",
        "status": "success"
    }


# 3. Protected POST endpoint (Requires x-api-key)
@app.post("/api/data", dependencies=[Depends(require_api_key)])
def post_protected_data():
    # The request body is ignored for this exercise
    return {
        "message": "POST received"
    }