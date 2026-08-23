import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from kingaweb_api.main import health, readiness


def test_health_endpoint_reports_service_state() -> None:
    response = asyncio.run(health())

    assert response.status == "healthy"
    assert response.service == "kingaweb-api"


def test_readiness_checks_database_connection() -> None:
    with Session(create_engine("sqlite+pysqlite:///:memory:")) as db:
        response = readiness(db)

    assert response.status == "ready"
    assert response.database == "connected"
