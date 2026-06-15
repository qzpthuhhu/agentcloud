"""Assets router: file upload/download (basic, for v0.1).

For v0.1 we store files on local disk under settings.asset_storage_dir.
v1.1 will swap in S3-compatible storage.
"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import schemas, models
from ..config import settings
from ..database import get_db
from ..deps import get_current_key


router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/upload", response_model=schemas.AssetOut)
async def upload_asset(
    file: UploadFile = File(...),
    meta: str = Form("{}"),
    db: Session = Depends(get_db),
    current: models.Key = Depends(get_current_key),
):
    """Upload an asset. Stores on disk under asset_storage_dir."""
    import json
    try:
        meta_dict = json.loads(meta) if meta else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="meta must be valid JSON")

    # Read content (limit by content-length header if present)
    content = await file.read()
    if len(content) > settings.max_asset_size:
        raise HTTPException(
            status_code=413,
            detail=f"Asset too large (max {settings.max_asset_size} bytes)",
        )

    asset_id = uuid.uuid4().hex
    storage_dir = Path(settings.asset_storage_dir) / current.key_id
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / asset_id
    storage_path.write_bytes(content)

    asset = models.Asset(
        asset_id=asset_id,
        key_id=current.key_id,
        filename=file.filename or "unnamed",
        mime=file.content_type or "application/octet-stream",
        size=len(content),
        storage_path=str(storage_path),
        meta=meta_dict,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return schemas.AssetOut(
        asset_id=asset.asset_id,
        filename=asset.filename,
        mime=asset.mime,
        size=asset.size,
        created_at=asset.created_at,
        meta=asset.meta,
    )


@router.get("/{asset_id}", response_model=schemas.AssetOut)
def get_asset_info(
    asset_id: str,
    db: Session = Depends(get_db),
    current: models.Key = Depends(get_current_key),
):
    asset = db.query(models.Asset).filter(
        models.Asset.asset_id == asset_id,
        models.Asset.key_id == current.key_id,
    ).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return schemas.AssetOut(
        asset_id=asset.asset_id,
        filename=asset.filename,
        mime=asset.mime,
        size=asset.size,
        created_at=asset.created_at,
        meta=asset.meta,
    )


@router.get("/{asset_id}/download")
def download_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current: models.Key = Depends(get_current_key),
):
    asset = db.query(models.Asset).filter(
        models.Asset.asset_id == asset_id,
        models.Asset.key_id == current.key_id,
    ).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    if not os.path.exists(asset.storage_path):
        raise HTTPException(status_code=410, detail="Asset file missing on storage")
    return FileResponse(
        asset.storage_path,
        media_type=asset.mime,
        filename=asset.filename,
    )