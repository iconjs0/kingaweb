import asyncio

from kingaweb_api.main import health


def test_health_endpoint_reports_service_state() -> None:
    response = asyncio.run(health())

    assert response.status == "healthy"
    assert response.service == "kingaweb-api"
