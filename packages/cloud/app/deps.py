"""Auth dependencies."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import models
from .auth import decode_access_token
from .database import get_db


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_key(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.Key:
    """Resolve the authenticated Key from the JWT bearer token."""
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    key_id = decode_access_token(creds.credentials)
    if key_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    key = db.query(models.Key).filter(
        models.Key.key_id == key_id,
        models.Key.revoked_at.is_(None),
    ).first()
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Key not found or revoked",
        )
    return key