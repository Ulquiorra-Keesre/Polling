import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta


@pytest.mark.integration
@pytest.mark.asyncio
class TestPollEndpoints:
    """Тесты CRUD для опросов"""

    async def test_create_poll_admin_success(self, admin_client: AsyncClient):

        test_poll_data = {
            "title": "Test Poll Title Here",
            "description": "Test description for poll",
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "options": [
                {"text": "Option 1"},
                {"text": "Option 2"},
            ],
        }

        response = await admin_client.post("/api/polls/", json=test_poll_data)

        assert response.status_code in [200, 201], (
            f"Failed to create poll: {response.status_code} - {response.text}"
        )

        resp_data = response.json() if response.content else {}

        poll_id = None
        if isinstance(resp_data, dict):
            if "data" in resp_data and isinstance(resp_data["data"], dict):
                poll_id = resp_data["data"].get("id")
            elif "id" in resp_data:
                poll_id = resp_data["id"]

        assert poll_id is not None, (
            f"Could not extract poll_id from response: {resp_data}"
        )

        assert "title" in resp_data or (
            "data" in resp_data and "title" in resp_data["data"]
        )

    async def test_create_poll_user_forbidden(self, authenticated_client: AsyncClient):
        """Обычный пользователь НЕ может создавать опросы"""

        test_poll_data = {
            "title": "User Poll",
            "description": "User description here",
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "options": [{"text": "A"}, {"text": "B"}],
        }

        response = await authenticated_client.post("/api/polls/", json=test_poll_data)

        assert response.status_code in [401, 403], (
            f"Expected 403/401, got {response.status_code}: {response.text}"
        )

    async def test_create_poll_min_options(self, admin_client: AsyncClient):
        """Нельзя создать опрос с менее чем 2 вариантами"""

        test_poll_data = {
            "title": "Test Poll Title Here",
            "description": "Test description for poll",
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "options": [{"text": "Only one"}],
        }

        response = await admin_client.post("/api/polls/", json=test_poll_data)

        assert response.status_code in [400, 422], (
            f"Expected 400/422 for validation error, got {response.status_code}"
        )

        if response.content:
            error_data = response.json()
            assert (
                "error" in error_data
                or "detail" in error_data
                or "too_short" in str(error_data).lower()
                or "validation" in str(error_data).lower()
            )

    async def test_get_polls_list(self, admin_client: AsyncClient):

        response = await admin_client.get("/api/polls/")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

        resp_data = response.json() if response.content else {}

        if "items" in resp_data:
            assert "total" in resp_data
            assert "page" in resp_data
            assert isinstance(resp_data["items"], list)
        else:
            assert isinstance(resp_data, list) or "polls" in resp_data

    async def test_get_poll_by_id(self, admin_client: AsyncClient):
        """Можно получить опрос по ID"""

        test_poll_data = {
            "title": "Test Poll for Fetch",
            "description": "Description for fetch test",
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "options": [{"text": "A"}, {"text": "B"}],
        }

        create = await admin_client.post("/api/polls/", json=test_poll_data)
        assert create.status_code in [200, 201]

        create_data = create.json() if create.content else {}
        poll_id = None
        if isinstance(create_data, dict):
            if "data" in create_data and isinstance(create_data["data"], dict):
                poll_id = create_data["data"].get("id")
            elif "id" in create_data:
                poll_id = create_data["id"]

        assert poll_id is not None, f"Could not extract poll_id: {create_data}"

        response = await admin_client.get(f"/api/polls/{poll_id}")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

        resp_data = response.json() if response.content else {}
        assert (
            "id" in resp_data
            or ("data" in resp_data and "id" in resp_data["data"])
            or "title" in resp_data
        )

    async def test_get_poll_not_found(self, admin_client: AsyncClient):
        """Получение несуществующего опроса возвращает 404"""

        response = await admin_client.get("/api/polls/999999")

        assert response.status_code == 404, (
            f"Expected 404, got {response.status_code}: {response.text}"
        )

    async def test_delete_poll_admin(self, admin_client: AsyncClient):
        """Администратор может удалить опрос"""

        test_poll_data = {
            "title": "Test Poll for Delete",
            "description": "Description for delete test",
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "options": [{"text": "A"}, {"text": "B"}],
        }

        create = await admin_client.post("/api/polls/", json=test_poll_data)
        assert create.status_code in [200, 201]

        create_data = create.json() if create.content else {}
        poll_id = None
        if isinstance(create_data, dict):
            if "data" in create_data and isinstance(create_data["data"], dict):
                poll_id = create_data["data"].get("id")
            elif "id" in create_data:
                poll_id = create_data["id"]

        assert poll_id is not None, f"Could not extract poll_id: {create_data}"

        response = await admin_client.delete(f"/api/polls/{poll_id}")

        assert response.status_code == 204, (
            f"Expected 204, got {response.status_code}: {response.text}"
        )

        get_response = await admin_client.get(f"/api/polls/{poll_id}")
        assert get_response.status_code in [404, 410], (
            f"Expected 404/410 after delete, got {get_response.status_code}"
        )
