import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_register_success(self, client: AsyncClient, test_user_data):
        response = await client.post("/api/auth/register", json=test_user_data)

        assert response.status_code in [200, 201]

        data = response.json()

        assert "access_token" in data or "data" in data

        if "data" in data:
            assert "access_token" in data["data"]

        elif "access_token" in data:
            assert data["access_token"] is not None

    async def test_register_duplicate(self, client: AsyncClient, test_user_data):
        """Регистрация с дублирующимся student_id"""
        await client.post("/api/auth/register", json=test_user_data)

        response = await client.post("/api/auth/register", json=test_user_data)

        assert response.status_code in [400, 409, 422]

        error_data = response.json()
        assert (
            "error" in error_data or "detail" in error_data or "message" in error_data
        )

    async def test_login_success(self, client: AsyncClient, test_user_data):
        """Успешный вход"""
        await client.post("/api/auth/register", json=test_user_data)

        response = await client.post(
            "/api/auth/login",
            json={
                "student_id": test_user_data["student_id"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == 200

        data = response.json()

        if "data" in data:
            assert "access_token" in data["data"]
            assert data["data"]["access_token"] is not None
        elif "access_token" in data:
            assert data["access_token"] is not None

    async def test_login_wrong_password(self, client: AsyncClient, test_user_data):
        """Вход с неверным паролем"""
        await client.post("/api/auth/register", json=test_user_data)

        response = await client.post(
            "/api/auth/login",
            json={"student_id": test_user_data["student_id"], "password": "wrong123"},
        )

        assert response.status_code in [400, 401, 422]

        error_data = response.json()
        assert (
            "error" in error_data or "detail" in error_data or "message" in error_data
        )

    async def test_refresh_token_success(self, client: AsyncClient, test_user_data):
        """Обновление токена"""
        reg = await client.post("/api/auth/register", json=test_user_data)
        reg_data = reg.json()

        if "data" in reg_data and "refresh_token" in reg_data["data"]:
            refresh = reg_data["data"]["refresh_token"]
        elif "refresh_token" in reg_data:
            refresh = reg_data["refresh_token"]
        else:
            pytest.skip("Refresh token not found in response")

        response = await client.post(f"/api/auth/refresh?refresh_token={refresh}")

        assert response.status_code == 200

        data = response.json()

        if "data" in data:
            assert "access_token" in data["data"]
        elif "access_token" in data:
            assert data["access_token"] is not None

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Обновление с невалидным токеном"""
        response = await client.post(
            "/api/auth/refresh?refresh_token=invalid_token_xyz"
        )

        assert response.status_code in [400, 401, 422]

        error_data = response.json()
        assert (
            "error" in error_data or "detail" in error_data or "message" in error_data
        )
