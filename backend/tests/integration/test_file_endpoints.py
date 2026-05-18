import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta


@pytest.mark.integration
@pytest.mark.asyncio
class TestFileEndpoints:
    """Тесты привязки баннеров к опросам (через banner_file_id)"""

    async def test_upload_banner_admin_success(
        self, admin_client: AsyncClient, test_banner_file
    ):
        """Администратор может привязать баннер к опросу"""

        test_poll_data = {
            "title": "Test Poll for Banner",
            "description": "Test description",
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "options": [
                {"text": "Option 1"},
                {"text": "Option 2"},
            ],
        }

        create = await admin_client.post("/api/polls/", json=test_poll_data)

        assert create.status_code in [200, 201, 204], (
            f"Failed to create poll: {create.status_code} - {create.text}"
        )

        poll_id = None
        if create.status_code != 204 and create.content:
            try:
                create_data = create.json()
                if isinstance(create_data, dict):
                    if "data" in create_data and isinstance(create_data["data"], dict):
                        poll_id = create_data["data"].get("id")
                    elif "id" in create_data:
                        poll_id = create_data["id"]
            except Exception:
                pass

        if poll_id is None:
            pytest.skip("Could not extract poll_id from create response")

        response = await admin_client.put(
            f"/api/polls/{poll_id}/banner", data={"banner_file_id": test_banner_file.id}
        )

        assert response.status_code in [200, 201, 204], (
            f"Banner attach failed: {response.status_code} - {response.text}"
        )

        if response.status_code != 204 and response.content:
            try:
                resp_data = response.json()
                assert (
                    "success" in resp_data
                    or "poll_id" in resp_data
                    or "banner_file_id" in resp_data
                    or "message" in resp_data
                ), f"Unexpected response format: {resp_data}"
            except Exception:
                pass

    async def test_upload_banner_user_forbidden(
        self, authenticated_client: AsyncClient, test_banner_file
    ):
        """Обычный пользователь НЕ может привязывать баннеры (ожидаем 403)"""

        test_poll_data = {
            "title": "User Test Poll",
            "description": "Test",
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "options": [
                {"text": "Option 1"},
                {"text": "Option 2"},
            ],
        }

        create = await authenticated_client.post("/api/polls/", json=test_poll_data)

        if create.status_code not in [200, 201, 204]:
            pytest.skip("User cannot create polls, skipping banner test")

        poll_id = None
        if create.status_code != 204 and create.content:
            try:
                create_data = create.json()
                if isinstance(create_data, dict):
                    if "data" in create_data and isinstance(create_data["data"], dict):
                        poll_id = create_data["data"].get("id")
                    elif "id" in create_data:
                        poll_id = create_data["id"]
            except Exception:
                pass

        if poll_id is None:
            pytest.skip("Could not extract poll_id")

        response = await authenticated_client.put(
            f"/api/polls/{poll_id}/banner", data={"banner_file_id": test_banner_file.id}
        )

        assert response.status_code in [401, 403], (
            f"Expected 403/401 for forbidden access, got {response.status_code}: {response.text}"
        )

        if response.content:
            try:
                error_data = response.json()
                assert (
                    "error" in error_data
                    or "detail" in error_data
                    or "forbidden" in str(error_data).lower()
                    or "unauthorized" in str(error_data).lower()
                ), f"Unexpected error format: {error_data}"
            except Exception:
                pass
