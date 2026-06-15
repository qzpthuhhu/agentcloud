"""Memory router: convenience view over the event log.

Memory items are derived from events of type 'memory.*' (add/update/delete).
This router provides:
- POST /v1/memory      -> emit a memory.add event (and return event_id)
- GET  /v1/memory      -> list memory items (joined from events)
"""
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .. import schemas, models
from ..database import get_db
from ..deps import get_current_key


router = APIRouter(prefix="/memory", tags=["memory"])


# event types considered "memory" items
MEMORY_EVENT_TYPES = ("memory.add", "memory.update")


@router.post("", response_model=schemas.MemoryAddResponse)
def add_memory(
    req: schemas.MemoryAddRequest,
    db: Session = Depends(get_db),
    current: models.Key = Depends(get_current_key),
):
    """Append a memory.add event to the log.

    Idempotent on client_event_id: if the same key+client_event_id pair was
    already accepted, the existing event_id is returned.
    """
    if req.client_event_id:
        existing = db.query(models.Event).filter(
            models.Event.key_id == current.key_id,
            models.Event.client_event_id == req.client_event_id,
        ).first()
        if existing is not None:
            return schemas.MemoryAddResponse(event_id=existing.event_id)

    payload = {
        "content": req.content,
        "type": req.type,
        "tags": req.tags,
        "meta": req.meta,
    }
    ev = models.Event(
        key_id=current.key_id,
        type="memory.add",
        payload=payload,
        client_ts=datetime.now(timezone.utc),
        client_event_id=req.client_event_id,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return schemas.MemoryAddResponse(event_id=ev.event_id)


@router.get("", response_model=schemas.MemoryList)
def list_memory(
    limit: int = Query(50, ge=1, le=500),
    type: Optional[str] = Query(None, description="Filter by memory.type (fact/preference/...)"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    db: Session = Depends(get_db),
    current: models.Key = Depends(get_current_key),
):
    """List memory items for the current key (newest first)."""
    q = db.query(models.Event).filter(
        models.Event.key_id == current.key_id,
        models.Event.type.in_(MEMORY_EVENT_TYPES),
    )
    events = q.order_by(desc(models.Event.event_id)).limit(limit).all()

    items: List[schemas.MemoryItem] = []
    for e in events:
        p = e.payload or {}
        if type and p.get("type") != type:
            continue
        tags = p.get("tags", [])
        if tag and tag not in tags:
            continue
        items.append(schemas.MemoryItem(
            event_id=e.event_id,
            type=e.type,
            memory_type=p.get("type", "fact"),
            content=p.get("content", ""),
            tags=tags,
            meta=p.get("meta", {}),
            created_at=e.server_ts,
        ))

    return schemas.MemoryList(items=items, total=len(items))