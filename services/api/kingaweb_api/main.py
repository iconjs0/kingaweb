from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from .assets import router as assets_router
from .config import get_settings
from .database import get_db

settings = get_settings()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Control-plane API for KingaWeb's authorized security monitoring platform.",
    docs_url="/docs" if settings.app_environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Authorization", "Content-Type"],
)

app.include_router(assets_router)


@app.get("/health", response_model=HealthResponse, tags=["Operations"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="kingaweb-api",
        version=settings.app_version,
        environment=settings.app_environment,
        timestamp=datetime.now(UTC),
    )


@app.get("/ready", response_model=ReadinessResponse, tags=["Operations"])
def readiness(db: Annotated[Session, Depends(get_db)]) -> ReadinessResponse:
    try:
        db.execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(status_code=503, detail="Database is unavailable") from error
    return ReadinessResponse(status="ready", database="connected", timestamp=datetime.now(UTC))
