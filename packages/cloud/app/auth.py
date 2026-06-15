"""Authentication helpers: key generation, hashing, JWT, recovery codes.

Security model (v1):
- Master key: 32 random bytes, base58-encoded (44 chars). SHA-256 hashed for storage.
- Recovery code: 24 random bytes, base58-encoded (32 chars). Bcrypt hashed for storage.
- After key login, server issues a JWT bound to key_id, valid 30 days.
- v1: server can see plaintext data (not E2E encrypted). At-rest encryption is a v1.1+ item.
"""
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt, JWTError

from .config import settings
from .models import Key
from .database import Session


# ===== Key & recovery code generation =====

def _b58encode(data: bytes) -> str:
    """Base58 encode (Bitcoin alphabet)."""
    import base58
    return base58.b58encode(data).decode("ascii")


def _b58decode(s: str) -> bytes:
    import base58
    return base58.b58decode(s.encode("ascii"))


def generate_key() -> str:
    """Generate a new master key (44 chars, base58)."""
    return _b58encode(secrets.token_bytes(32))


def generate_recovery_code() -> str:
    """Generate a recovery code (32 chars, base58)."""
    return _b58encode(secrets.token_bytes(24))


def hash_key(key: str) -> bytes:
    """Hash master key with SHA-256 (fast lookup, since keys are high-entropy)."""
    return hashlib.sha256(key.encode("utf-8")).digest()


def hash_recovery_code(code: str) -> bytes:
    """Hash recovery code with bcrypt (slow, since codes may be lower-entropy in practice)."""
    return bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt())


def verify_recovery_code(code: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(code.encode("utf-8"), hashed)


# ===== JWT session tokens =====

def create_access_token(key_id: str, expires_minutes: Optional[int] = None) -> tuple[str, datetime]:
    """Create a JWT access token. Returns (token, expires_at)."""
    minutes = expires_minutes or settings.jwt_expire_minutes
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {
        "sub": key_id,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
        "typ": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_access_token(token: str) -> Optional[str]:
    """Decode JWT and return key_id, or None if invalid/expired."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload.get("sub")
    except JWTError:
        return None


# ===== DB lookups =====

def find_key_by_raw_key(db: Session, raw_key: str) -> Optional[Key]:
    """Look up a key by its raw value (after hashing)."""
    key_hash = hash_key(raw_key)
    return db.query(Key).filter(Key.key_hash == key_hash, Key.revoked_at.is_(None)).first()