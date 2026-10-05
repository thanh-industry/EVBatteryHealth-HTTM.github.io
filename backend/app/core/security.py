"""Demo auth: password hashing and a signed, stateless bearer token.

Not JWT (no extra dependency needed) but the same idea: base64 payload +
HMAC-SHA256 signature, verified on every request. Good enough for a demo app
that must still enforce real 401/403 behaviour.
"""
import base64
import hashlib
import hmac
import json
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

_bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or hashlib.sha256(password.encode("utf-8")).digest()[:16]
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, settings.PBKDF2_ITERATIONS
    )
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, _digest_hex = stored_hash.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    candidate = hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, stored_hash)


def _sign(payload_b64: str) -> str:
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")


def create_token(user_id: int) -> str:
    payload = {"uid": user_id, "exp": int(time.time()) + settings.TOKEN_TTL_SECONDS}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    return f"{payload_b64}.{_sign(payload_b64)}"


def decode_token(token: str) -> int:
    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError:
        raise ValueError("Malformed token")
    if not hmac.compare_digest(signature, _sign(payload_b64)):
        raise ValueError("Invalid token signature")
    padding = "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("Token expired")
    return int(payload["uid"])


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        user_id = decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def require_role(*roles: str):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not permitted to perform this action.",
            )
        return current_user

    return dependency
