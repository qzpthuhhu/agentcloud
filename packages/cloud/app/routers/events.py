"""Events router: append-only event log for sync."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .. import schemas, models
from ..database import get_db
from ..deps import get_current_key


router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=schemas.EventBatchResponse)
def append_events(
    batch: schemas.EventBatch,
    db: Session = Depends(get_db),
    current: models.Key = Depends(get_current_key),
):
    """Append events to the log.

    Idempotent on client_event_id: if the same key+client_event_id pair was
    already accepted, the existing event_id is returned instead of inserting
    a duplicate.
    """
    accepted_ids: list[int] = []
    duplicate_indices: list[int] = []

    for idx, ev_in in enumerate(batch.events):
        # Dedup: same (key_id, client_event_id) already exists?
        existing = None
        if ev_in.client_event_id:
            existing = db.query(models.Event).filter(
                models.Event.key_id == current.key_id,
                models.Event.client_event_id == ev_in.client_event_id,
            ).first()
        if existing is not None:
            accepted_ids.append(existing.event_id)
            duplicate_indices.append(idx)
            continue

        ev = models.Event(
            key_id=current.key_id,
            type=ev_in.type,
            payload=ev_in.payload or {},
            client_ts=ev_in.client_ts,
            client_event_id=ev_in.client_event_id,
        )
        db.add(ev)
        db.flush()  # get event_id without commit
        accepted_ids.append(ev.event_id)

    db.commit()
    return schemas.EventBatchResponse(
        accepted=accepted_ids,
        duplicates=duplicate_indices,
    )


@router.get("", response_model=schemas.EventList)
def list_events(
    since: Optional[int] = Query(None, description="Return events with event_id > since"),
    limit: int = Query(200, ge=1, le=1000),
    type: Optional[str] = Query(None, description="Filter by event type"),
    db: Session = Depends(get_db),
    current: models.Key = Depends(get_current_key),
):
    """Pull events from the log.

    Used for sync: client passes last known event_id as `since`, server
    returns newer events in ascending order.
    """
    q = db.query(models.Event).filter(models.Event.key_id == current.key_id)
    if since is not None:
        q = q.filter(models.Event.event_id > since)
    if type is not None:
        q = q.filter(models.Event.type == type)

    # Fetch limit+1 to know if there's more
    events = q.order_by(models.Event.event_id.asc()).limit(limit + 1).all()
    has_more = len(events) > limit
    events = events[:limit]

    next_since = events[-1].event_id if events else since

    return schemas.EventList(
        events=[
            schemas.EventOut(
                event_id=e.event_id,
                key_id=e.key_id,
                type=e.type,
                payload=e.payload or {},
                client_ts=e.client_ts,
                server_ts=e.server_ts,
                client_event_id=e.client_event_id,
            )
            for e in events
        ],
        has_more=has_more,
        next_since=next_since,
    )


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current: models.Key = Depends(get_current_key),
):
    ev = db.query(models.Event).filter(
        models.Event.event_id == event_id,
        models.Event.key_id == current.key_id,
    ).first()
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return schemas.EventOut(
        event_id=ev.event_id,
        key_id=ev.key_id,
        type=ev.type,
        payload=ev.payload or {},
        client_ts=ev.client_ts,
        server_ts=ev.server_ts,
        client_event_id=ev.client_event_id,
    )