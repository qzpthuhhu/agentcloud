"""Auth router: register, login, recover, revoke."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas, models
from ..auth import (
    generate_key, generate_recovery_code,
    hash_key, hash_recovery_code, verify_recovery_code,
    create_access_token, find_key_by_raw_key,
)
from ..database import get_db
from ..deps import get_current_key


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.RegisterResponse)
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Create a new agent identity. Returns master key + recovery code.

    The key is shown ONCE - server only stores hash.
    """
    raw_key = generate_key()
    recovery = generate_recovery_code()

    key = models.Key(
        key_hash=hash_key(raw_key),
        recovery_hash=hash_recovery_code(recovery),
        label=req.label,
    )
    db.add(key)
    db.commit()
    db.refresh(key)

    return schemas.RegisterResponse(
        key=raw_key,
        key_id=key.key_id,
        recovery_code=recovery,
        created_at=key.created_at,
    )


@router.post("/login", response_model=schemas.LoginResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Exchange a master key for a JWT access token."""
    key = find_key_by_raw_key(db, req.key)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid key",
        )
    token, expires_at = create_access_token(key.key_id)
    return schemas.LoginResponse(
        access_token=token,
        expires_at=expires_at,
        key_id=key.key_id,
    )


@router.post("/recover", response_model=schemas.RecoverResponse)
def recover(req: schemas.RecoverRequest, db: Session = Depends(get_db)):
    """Use a recovery code to regenerate a master key.

    This revokes the old key and issues a new one.
    """
    # Find key by trying recovery code against all non-revoked keys.
    # Note: this is O(n) over keys; for large scale we'd add a recovery_hash index
    # keyed by partial code, but recovery is rare so OK for v1.
    candidates = db.query(models.Key).filter(
        models.Key.revoked_at.is_(None)
    ).all()

    matched: models.Key = None  # type: ignore
    for cand in candidates:
        try:
            if verify_recovery_code(req.recovery_code, bytes(cand.recovery_hash)):
                matched = cand
                break
        except Exception:
            continue

    if matched is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid recovery code",
        )

    # Generate new key material
    new_raw = req.new_key or generate_key()
    new_recovery = generate_recovery_code()

    # Update the existing key in place: new key_hash + new recovery_hash.
    # key_id is preserved -> identity continuity.
    matched.key_hash = hash_key(new_raw)
    matched.recovery_hash = hash_recovery_code(new_recovery)
    # Note: we keep revoked_at as-is to preserve history; if a key was previously
    # revoked, recovery on it would have failed (we filter revoked_at IS NULL).
    db.commit()
    db.refresh(matched)

    return schemas.RecoverResponse(
        key=new_raw,
        key_id=matched.key_id,
        created_at=matched.created_at,
    )


@router.get("/me")
def me(current: models.Key = Depends(get_current_key)):
    """Get info about the currently authenticated key."""
    return {
        "key_id": current.key_id,
        "label": current.label,
        "created_at": current.created_at,
    }