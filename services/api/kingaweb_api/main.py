from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import get_settings

settings = get_settings()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
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
    allow_methods=["GET"],
    allow_headers=["Accept", "Content-Type"],
)


@app.get("/health", response_model=HealthResponse, tags=["Operations"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="kingaweb-api",
        version=settings.app_version,
        environment=settings.app_environment,
        timestamp=datetime.now(UTC),
    )
