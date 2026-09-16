import os
import sqlite3
import asyncio
import secrets
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, Header, HTTPException, Depends, status, Body
from fastapi.middleware.cors import CORSMiddleware
from cryptography.fernet import Fernet
from ldap3 import Server, Connection, ALL

# ---------------------------------------------------------------------------
# 1. Database & Encryption Configuration
# ---------------------------------------------------------------------------
DB_PATH = os.getenv("DB_PATH", "database.db")
DATABASE_ENCRYPTION_KEY = os.getenv(
    "DATABASE_ENCRYPTION_KEY",
    "xtUkK48nDUHiJ3vcLLZKTL6vXW_yOWsMy6EX4OkyXe4="
)

# ---------------------------------------------------------------------------
# LDAP Configuration
# ---------------------------------------------------------------------------
LDAP_HOST = os.getenv("LDAP_HOST", "openldap")
LDAP_PORT = int(os.getenv("LDAP_PORT", "389"))
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=example,dc=com")
LDAP_ADMIN_DN = os.getenv("LDAP_ADMIN_DN", f"cn=admin,{LDAP_BASE_DN}")
LDAP_ADMIN_PASSWORD = os.getenv("LDAP_ADMIN_PASSWORD", "adminpassword")

# Initialize Fernet cipher with the persistent database key
cipher = Fernet(DATABASE_ENCRYPTION_KEY.encode() if isinstance(DATABASE_ENCRYPTION_KEY, str) else DATABASE_ENCRYPTION_KEY)


def init_db():
    """Initializes the SQLite database and stores table if not exists."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ciphertext TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    # Seed an initial encrypted record if empty
    cursor.execute("SELECT COUNT(*) FROM records")
    count = cursor.fetchone()[0]
    if count == 0:
        initial_plain = "Initial Secure Record - Confidential Data"
        initial_cipher = cipher.encrypt(initial_plain.encode("utf-8")).decode("utf-8")
        cursor.execute(
            "INSERT INTO records (ciphertext, created_at) VALUES (?, ?)",
            (initial_cipher, datetime.utcnow().isoformat())
        )
        conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# 2. Dynamic Secret Authentication & Rotation (API_SECRET)
# ---------------------------------------------------------------------------
SHARED_SECRET_FILE = "/shared_secrets/current_secret.txt"
ROTATION_INTERVAL = int(os.getenv("ROTATION_INTERVAL_SECONDS", "60"))


async def auto_rotate_secrets():
    """Background task that automatically rotates API_SECRET every 1 minute."""
    os.makedirs("/shared_secrets", exist_ok=True)
    
    # Initialize with starting secret if not present
    current = os.getenv("API_SECRET", "initial_secret_abc123")
    if not os.path.exists(SHARED_SECRET_FILE):
        try:
            with open(SHARED_SECRET_FILE, "w") as f:
                f.write(current)
            print(f"[ROTATION] Initialized active API_SECRET: {current}", flush=True)
        except Exception as err:
            print(f"[ROTATION] Could not initialize file: {err}", flush=True)

    while True:
        try:
            await asyncio.sleep(ROTATION_INTERVAL)
            old_secret = get_expected_api_secret()
            new_secret = f"SEC-{secrets.token_hex(4).upper()}"
            
            with open(SHARED_SECRET_FILE, "w") as f:
                f.write(new_secret)
                
            print("\n" + "=" * 65, flush=True)
            print(f" [AUTOMATIC ROTATION - EVERY 1 MINUTE] {datetime.utcnow().isoformat()}", flush=True)
            print(f"  -> Old API_SECRET: {old_secret}", flush=True)
            print(f"  -> New API_SECRET: {new_secret}", flush=True)
            print(f"  -> DATABASE_ENCRYPTION_KEY: [UNCHANGED] {DATABASE_ENCRYPTION_KEY[:8]}...", flush=True)
            print("=" * 65 + "\n", flush=True)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[ROTATION ERROR] {e}", flush=True)


ENABLE_BACKGROUND_ROTATOR = os.getenv("ENABLE_BACKGROUND_ROTATOR", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    rotator_task = None
    if ENABLE_BACKGROUND_ROTATOR:
        rotator_task = asyncio.create_task(auto_rotate_secrets())
    yield
    if rotator_task:
        rotator_task.cancel()


class LoginRequest(BaseModel):
    username: str
    password: str


app = FastAPI(
    title="Security Exercise API",
    description="API with Dynamic Secret Authentication and Database Encryption",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ---------------------------------------------------------------------------
# 2. Dynamic Secret Authentication (API_SECRET)
# ---------------------------------------------------------------------------
SHARED_SECRET_FILE = "/shared_secrets/current_secret.txt"


def get_expected_api_secret() -> str:
    """
    Retrieves the active API secret dynamically.
    Checks shared volume first (for automatic rotation), falling back to env var.
    """
    if os.path.exists(SHARED_SECRET_FILE):
        try:
            with open(SHARED_SECRET_FILE, "r") as f:
                val = f.read().strip()
                if val:
                    return val
        except Exception:
            pass

    return os.getenv("API_SECRET", os.getenv("API_KEY", "my-secret-key"))


def require_api_key(x_api_key: Optional[str] = Header(None, alias="x-api-key")):
    """Validates the incoming x-api-key against the active rotated API_SECRET."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header 'x-api-key' not provided"
        )

    expected_secret = get_expected_api_secret()
    if x_api_key != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

    return x_api_key


# ---------------------------------------------------------------------------
# 3. API Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def get_health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/data", dependencies=[Depends(require_api_key)])
def get_protected_data():
    """
    Retrieves the latest encrypted record from SQLite, decrypts it with Fernet,
    and returns both the decrypted plaintext and the raw database ciphertext.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, ciphertext, created_at FROM records ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="No records found in database")

    record_id, stored_cipher, created_at = row

    # Decrypt using the persistent database encryption key
    try:
        decrypted_plain = cipher.decrypt(stored_cipher.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(exc)}")

    return {
        "status": "success",
        "action": "Database Read & Decrypted",
        "decrypted_content": decrypted_plain,
        "database_raw_ciphertext": stored_cipher,
        "record_id": record_id,
        "timestamp": created_at
    }


@app.post("/api/data", dependencies=[Depends(require_api_key)])
def post_protected_data(payload: Dict[str, Any] = Body(default={"message": "Default secure message"})):
    """
    Receives data from client, encrypts it with Fernet, and saves ciphertext into SQLite.
    """
    message_to_encrypt = payload.get("message", "Confidential information")

    # Encrypt plaintext
    encrypted_bytes = cipher.encrypt(message_to_encrypt.encode("utf-8"))
    encrypted_str = encrypted_bytes.decode("utf-8")

    # Store in SQLite
    now_iso = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO records (ciphertext, created_at) VALUES (?, ?)",
        (encrypted_str, now_iso)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {
        "status": "success",
        "action": "Encrypted & Stored in Database",
        "plaintext_received": message_to_encrypt,
        "database_stored_ciphertext": encrypted_str,
        "record_id": new_id,
        "timestamp": now_iso
    }


# ---------------------------------------------------------------------------
# 4. LDAP Authentication & Diagnostics
# ---------------------------------------------------------------------------
@app.post("/api/login", dependencies=[Depends(require_api_key)])
def login_ldap(request: LoginRequest):
    """
    Authenticates user credentials against OpenLDAP directory.
    Requires valid x-api-key injected by Nginx proxy.
    """
    server = Server(LDAP_HOST, port=LDAP_PORT, get_info=ALL)
    user_dn = f"uid={request.username},ou=users,{LDAP_BASE_DN}"

    connection = Connection(
        server,
        user=user_dn,
        password=request.password,
        auto_bind=False,
    )

    try:
        if connection.bind():
            # Fetch attributes for display
            user_details = {
                "username": request.username,
                "dn": user_dn,
                "fullName": request.username.capitalize(),
                "email": f"{request.username}@example.com"
            }
            try:
                connection.search(
                    search_base=user_dn,
                    search_filter="(objectClass=*)",
                    attributes=["cn", "mail", "displayName"]
                )
                if connection.entries:
                    entry = connection.entries[0]
                    if hasattr(entry, "cn") and entry.cn:
                        user_details["fullName"] = str(entry.cn)
                    if hasattr(entry, "mail") and entry.mail:
                        user_details["email"] = str(entry.mail)
            except Exception:
                pass

            return {
                "status": "success",
                "authenticated": True,
                "username": request.username,
                "dn": user_dn,
                "user_info": user_details,
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Usuario '{request.username}' autenticado exitosamente con OpenLDAP"
            }

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales LDAP inválidas: Usuario o contraseña incorrectos"
        )
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en servidor LDAP ({LDAP_HOST}:{LDAP_PORT}): {str(err)}"
        )
    finally:
        try:
            connection.unbind()
        except Exception:
            pass


@app.get("/api/ldap/status")
def get_ldap_status():
    """Checks reachability of the OpenLDAP server."""
    try:
        server = Server(LDAP_HOST, port=LDAP_PORT, connect_timeout=3)
        conn = Connection(server, auto_bind=False)
        conn.open()
        conn.unbind()
        return {
            "status": "connected",
            "ldap_host": LDAP_HOST,
            "ldap_port": LDAP_PORT,
            "base_dn": LDAP_BASE_DN,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as exc:
        return {
            "status": "unreachable",
            "ldap_host": LDAP_HOST,
            "ldap_port": LDAP_PORT,
            "error": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/api/status")
def get_system_status():
    """Returns overall status of Backend, active API secret status, and database encryption status."""
    expected_secret = get_expected_api_secret()
    masked_secret = f"{expected_secret[:4]}...{expected_secret[-4:]}" if len(expected_secret) > 8 else "***"
    masked_db_key = f"{DATABASE_ENCRYPTION_KEY[:8]}...[PROTECTED]"

    return {
        "status": "healthy",
        "service": "Backend Security API",
        "active_api_secret_sample": masked_secret,
        "database_encryption_key_sample": masked_db_key,
        "database_key_unchanged": True,
        "ldap_host": LDAP_HOST,
        "timestamp": datetime.utcnow().isoformat()
    }