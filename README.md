# Security Backend API - Dynamic Secret Authentication, LDAP & Database Encryption

FastAPI service integrated with **OpenLDAP**, dynamic **API_SECRET** rotation, and persistent **Fernet** database encryption.

## 🚀 Key Features

1. **LDAP Authentication (`/api/login`)**: Validates user credentials against OpenLDAP directory (`osixia/openldap:1.5.0`) using `ldap3`.
2. **Dynamic `API_SECRET` Authentication**: Validates `x-api-key` injected securely by the Nginx reverse proxy. The active secret is dynamically read from the shared volume (`/shared_secrets/current_secret.txt`).
3. **Persistent Database Encryption**: Encrypts and decrypts confidential data in SQLite using Python's `cryptography.fernet` with `DATABASE_ENCRYPTION_KEY`. This key is persistent and NOT rotated during secret rotation.
4. **Zero-Trust Reverse Proxy**: Browsers interact with Frontend Nginx; Frontend injects the secret server-side to Backend.

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `API_SECRET` | `initial_secret_abc123` | Shared secret for Nginx <-> Backend communication |
| `DATABASE_ENCRYPTION_KEY` | *(Fernet 32-byte key)* | Persistent database encryption key (DO NOT ROTATE) |
| `DB_PATH` | `/app/data/app.db` | SQLite database file path |
| `LDAP_HOST` | `openldap` | OpenLDAP hostname or IP |
| `LDAP_PORT` | `389` | OpenLDAP port |
| `LDAP_BASE_DN` | `dc=example,dc=com` | LDAP Base DN |
| `LDAP_ADMIN_PASSWORD` | `adminpassword` | OpenLDAP administrator password |

## 📌 Endpoints

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/health` | ❌ No | Health check |
| `GET` | `/api/status` | ❌ No | Diagnostic status and masked secret verification |
| `GET` | `/api/ldap/status` | ❌ No | OpenLDAP connection health |
| `POST` | `/api/login` | ✅ `x-api-key` | Authenticates user against OpenLDAP (`alice`, `bob`) |
| `GET` | `/api/data` | ✅ `x-api-key` | Retrieves latest record, decrypts with Fernet |
| `POST` | `/api/data` | ✅ `x-api-key` | Encrypts payload with Fernet and stores in SQLite |

## 🧪 Testing

Run automated tests:
```bash
python test_api.py
```

