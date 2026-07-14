import bcrypt
import jwt
from datetime import UTC, datetime, timedelta

from backend.config import Config


def hash_password(password):
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Invalid hashes should behave like incorrect passwords.
        return False


def create_access_token(user_id, role):
    expires_at = datetime.now(UTC) + timedelta(
        minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expires_at,
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
