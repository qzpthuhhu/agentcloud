"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import auth, events, memory, assets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup."""
    init_db()
    yield


app = FastAPI(
    title="Agent Cloud Drive API",
    version="0.1.0",
    description="Key-based cloud memory layer for AI agents.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": settings.service_name,
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# Mount v1 routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(events.router, prefix=settings.api_prefix)
app.include_router(memory.router, prefix=settings.api_prefix)
app.include_router(assets.router, prefix=settings.api_prefix)