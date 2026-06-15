"""Pydantic schemas for API."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ===== Auth =====

class RegisterRequest(BaseModel):
    label: Optional[str] = None


class RegisterResponse(BaseModel):
    key: str = Field(..., description="The agent's master key - keep this secret!")
    key_id: str
    recovery_code: str = Field(..., description="Use this to recover if key is lost")
    created_at: datetime


class LoginRequest(BaseModel):
    key: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    key_id: str


class RecoverRequest(BaseModel):
    recovery_code: str
    new_key: Optional[str] = None  # if None, generate one


class RecoverResponse(BaseModel):
    key: str
    key_id: str
    created_at: datetime


# ===== Events =====

class EventIn(BaseModel):
    type: str = Field(..., description="Event type, e.g. 'memory.add', 'memory.update', 'memory.delete'")
    payload: Dict[str, Any] = Field(default_factory=dict)
    client_ts: Optional[datetime] = None
    client_event_id: Optional[str] = Field(None, description="Client-side dedup key")


class EventBatch(BaseModel):
    events: List[EventIn]


class EventOut(BaseModel):
    event_id: int
    key_id: str
    type: str
    payload: Dict[str, Any]
    client_ts: Optional[datetime]
    server_ts: datetime
    client_event_id: Optional[str]


class EventBatchResponse(BaseModel):
    accepted: List[int] = Field(..., description="event_ids in the same order as input")
    duplicates: List[int] = Field(default_factory=list, description="indices of events that were duplicates (skipped)")


class EventList(BaseModel):
    events: List[EventOut]
    has_more: bool
    next_since: Optional[int] = None


# ===== Memory (view over events) =====

class MemoryItem(BaseModel):
    """Memory item - derived view of an event of type memory.add."""
    event_id: int
    type: str  # 'memory.add' / 'memory.update' etc.
    memory_type: str = "fact"  # semantic type from payload
    content: str
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class MemoryAddRequest(BaseModel):
    content: str
    type: str = "fact"  # fact | preference | conversation | note | skill
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    client_event_id: Optional[str] = None


class MemoryAddResponse(BaseModel):
    event_id: int


class MemoryList(BaseModel):
    items: List[MemoryItem]
    total: int


# ===== Assets =====

class AssetOut(BaseModel):
    asset_id: str
    filename: str
    mime: str
    size: int
    created_at: datetime
    meta: Dict[str, Any] = Field(default_factory=dict)


# ===== Errors =====

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None