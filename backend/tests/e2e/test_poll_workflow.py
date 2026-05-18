"""
E2E-тест полного сценария работы с опросом:
1. Регистрация админа и пользователя
2. Создание опроса админом
3. Голосование пользователя
4. Получение результатов
5. Удаление опроса админом
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta


@pytest.mark.e2e
@pytest.mark.asyncio
class TestPollWorkflow:
    """E2E-тест полного цикла работы с опросом"""

    async def test_full_poll_workflow(self, client: AsyncClient):
        """
        ✅ Полный сценарий:
        - Админ создаёт опрос
        - Пользователь голосует
        - Проверяем результаты
        - Админ удаляет опрос
        """

        admin_data = {
            "student_id": "E2E_ADMIN_001",
            "name": "E2E Admin",
            "faculty": "Test Faculty",
            "password": "AdminPass123!",
            "role": "admin",
        }

        admin_reg = await client.post("/api/auth/register/", json=admin_data)
        assert admin_reg.status_code in [200, 201], (
            f"Admin registration failed: {admin_reg.text}"
        )

        admin_resp = admin_reg.json() if admin_reg.content else {}
        admin_token = None
        if (
            "data" in admin_resp
            and isinstance(admin_resp["data"], dict)
            and "access_token" in admin_resp["data"]
        ):
            admin_token = admin_resp["data"]["access_token"]
        elif "access_token" in admin_resp:
            admin_token = admin_resp["access_token"]

        assert admin_token is not None, f"Could not extract admin token: {admin_resp}"

        user_data = {
            "student_id": "E2E_USER_001",
            "name": "E2E User",
            "faculty": "Test Faculty",
            "password": "UserPass123!",
            "role": "user",
        }

        user_reg = await client.post("/api/auth/register/", json=user_data)
        assert user_reg.status_code in [200, 201], (
            f"User registration failed: {user_reg.text}"
        )

        user_resp = user_reg.json() if user_reg.content else {}
        user_token = None
        if (
            "data" in user_resp
            and isinstance(user_resp["data"], dict)
            and "access_token" in user_resp["data"]
        ):
            user_token = user_resp["data"]["access_token"]
        elif "access_token" in user_resp:
            user_token = user_resp["access_token"]

        assert user_token is not None, f"Could not extract user token: {user_resp}"

        client.headers["Authorization"] = f"Bearer {admin_token}"

        poll_data = {
            "title": "E2E Test Poll",
            "description": "Full workflow test for poll system",
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "options": [
                {"text": "Option A"},
                {"text": "Option B"},
                {"text": "Option C"},
            ],
        }

        create = await client.post("/api/polls/", json=poll_data)
        assert create.status_code in [200, 201], f"Poll creation failed: {create.text}"

        create_data = create.json() if create.content else {}
        poll_id = None
        if isinstance(create_data, dict):
            if "data" in create_data and isinstance(create_data["data"], dict):
                poll_id = create_data["data"].get("id")
            elif "id" in create_data:
                poll_id = create_data["id"]

        assert poll_id is not None, f"Could not extract poll_id: {create_data}"

        option_id = None
        if "options" in create_data and create_data["options"]:
            option_id = create_data["options"][0].get("id")
        elif (
            "data" in create_data
            and "options" in create_data["data"]
            and create_data["data"]["options"]
        ):
            option_id = create_data["data"]["options"][0].get("id")

        assert option_id is not None, f"Could not extract option_id: {create_data}"

        client.headers["Authorization"] = f"Bearer {user_token}"

        vote_response = await client.post(
            "/api/votes/", json={"poll_id": poll_id, "option_id": option_id}
        )
        assert vote_response.status_code == 201, f"Vote failed: {vote_response.text}"

        results = await client.get(f"/api/polls/{poll_id}/results")
        assert results.status_code == 200, f"Failed to get results: {results.text}"

        results_data = results.json() if results.content else {}

        if "data" in results_data and isinstance(results_data["data"], dict):
            results_payload = results_data["data"]
        else:
            results_payload = results_data

        assert "total_votes" in results_payload or "options" in results_payload, (
            f"Unexpected results format: {results_payload}"
        )
        assert results_payload.get("total_votes", 0) >= 1, "Expected at least 1 vote"

        client.headers["Authorization"] = f"Bearer {admin_token}"

        delete = await client.delete(f"/api/polls/{poll_id}")
        assert delete.status_code == 204, (
            f"Delete failed: {delete.status_code} - {delete.text}"
        )

        get_deleted = await client.get(f"/api/polls/{poll_id}")
        assert get_deleted.status_code in [404, 410], (
            f"Expected 404/410 after delete, got {get_deleted.status_code}: {get_deleted.text}"
        )
