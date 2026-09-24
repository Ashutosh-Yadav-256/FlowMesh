"""
FlowMesh Authentication & Session Management Service

Handles password hashing, OIDC assertion mapping, and JWT session tokens.
"""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt

from app.config import settings


def hash_secret(secret: str) -> str:
    """Deterministic salted SHA-256 hash for API keys and secrets."""
    salt = settings.api_secret_key.encode("utf-8")
    return hmac.HMAC(salt, secret.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_secret(secret: str, hashed: str) -> bool:
    """Verifies a secret against its stored hash."""
    expected = hash_secret(secret)
    return hmac.compare_digest(expected, hashed)


def create_access_token(
    user_id: str,
    tenant_id: str,
    role: str,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates a signed JWT session token encoding user, active tenant, and RBAC role."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode: Dict[str, Any] = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(to_encode, settings.api_secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and cryptographically verifies a JWT session token."""
    return jwt.decode(token, settings.api_secret_key, algorithms=[settings.algorithm])
