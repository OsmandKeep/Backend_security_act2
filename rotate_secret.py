import os
import secrets

SHARED_SECRET_FILE = os.getenv("SHARED_SECRET_FILE", "/shared_secrets/current_secret.txt")


def rotate():
    new_secret = f"SEC-{secrets.token_hex(4).upper()}"
    old_secret = "None"

    if os.path.exists(SHARED_SECRET_FILE):
        try:
            with open(SHARED_SECRET_FILE, "r") as f:
                old_secret = f.read().strip()
        except Exception:
            pass

    os.makedirs(os.path.dirname(os.path.abspath(SHARED_SECRET_FILE)), exist_ok=True)
    with open(SHARED_SECRET_FILE, "w") as f:
        f.write(new_secret)

    print("=" * 50)
    print(" [MANUAL/TRIGGERED SECRET ROTATION]")
    print(f"  Old Secret: {old_secret}")
    print(f"  New Secret: {new_secret}")
    print("=" * 50)


if __name__ == "__main__":
    rotate()
