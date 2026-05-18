import re
import pytest
from httpx import AsyncClient

pytest_plugins = ["pytest_httpx"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestWeatherEndpoints:
    """Тесты маршрутов погоды с мокированием внешнего API"""

    async def test_weather_success_mock(self, client: AsyncClient, httpx_mock):

        httpx_mock.add_response(
            url=re.compile(r"https://api\.openweathermap\.org/data/2\.5/weather\?.*"),
            method="GET",
            status_code=200,
            json={
                "name": "Moscow",
                "main": {"temp": 15.5, "humidity": 60, "feels_like": 14.0},
                "weather": [{"description": "Ясно", "icon": "01d"}],
                "wind": {"speed": 3.5},
            },
        )

        response = await client.get("/api/weather/current?city=Moscow")

        assert response.status_code == 200, f"Unexpected status: {response.text}"

        resp_data = response.json()

        assert resp_data.get("success") is True
        assert "data" in resp_data

        data = resp_data["data"]

        assert data["city"] == "Moscow"
        assert data["temperature"] == 15.5
        assert data["humidity"] == 60
        assert data["description"] == "Ясно"
        assert data["icon"] == "01d"
        assert data["wind_speed"] == 3.5

        assert data["is_fallback"] is False

    async def test_weather_api_failure(self, client: AsyncClient, httpx_mock):
        """Тест обработки ошибки внешнего API (fallback-режим)"""

        httpx_mock.add_response(
            url=re.compile(r"https://api\.openweathermap\.org/data/2\.5/weather\?.*"),
            method="GET",
            status_code=500,
            json={"message": "Internal Server Error", "cod": "500"},
        )

        response = await client.get("/api/weather/current?city=Moscow")

        assert response.status_code == 200, (
            f"Expected 200 with fallback, got {response.status_code}: {response.text}"
        )

        resp_data = response.json()
        assert resp_data.get("success") is True
        assert "data" in resp_data

        data = resp_data["data"]

        assert data["is_fallback"] is True

        assert data["temperature"] is None
        assert data["humidity"] is None

        assert "warning" in data
        assert data["warning"] is not None
        assert "500" in data["warning"] or "HTTP" in data["warning"].upper()
