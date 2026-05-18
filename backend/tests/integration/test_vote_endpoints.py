import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta


@pytest.mark.integration
@pytest.mark.asyncio
class TestVoteEndpoints:
    """Тесты голосования и получения результатов"""

    async def _setup_poll(self, client: AsyncClient, admin_data, user_data, poll_data):

        admin_reg = await client.post("/api/auth/register/", json=admin_data)
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

        if not admin_token:
            pytest.fail(f"Could not extract admin token: {admin_resp}")

        user_reg = await client.post("/api/auth/register/", json=user_data)
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

        if not user_token:
            pytest.fail(f"Could not extract user token: {user_resp}")

        client.headers["Authorization"] = f"Bearer {admin_token}"

        poll_data_with_date = {
            **poll_data,
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }

        create = await client.post("/api/polls/", json=poll_data_with_date)
        assert create.status_code in [200, 201], f"Failed to create poll: {create.text}"

        create_data = create.json() if create.content else {}

        poll_id = None
        if isinstance(create_data, dict):
            if "data" in create_data and isinstance(create_data["data"], dict):
                poll_id = create_data["data"].get("id")
            elif "id" in create_data:
                poll_id = create_data["id"]

        if poll_id is None:
            pytest.fail(f"Could not extract poll_id: {create_data}")

        option_id = None
        if "options" in create_data and create_data["options"]:
            option_id = create_data["options"][0].get("id")
        elif (
            "data" in create_data
            and "options" in create_data["data"]
            and create_data["data"]["options"]
        ):
            option_id = create_data["data"]["options"][0].get("id")

        if option_id is None:
            pytest.fail(f"Could not extract option_id: {create_data}")

        return poll_id, option_id, user_token

    async def test_vote_success(
        self, client: AsyncClient, test_admin_data, test_user_data, test_poll_data
    ):
        """Пользователь может проголосовать"""

        poll_id, option_id, user_token = await self._setup_poll(
            client, test_admin_data, test_user_data, test_poll_data
        )

        client.headers["Authorization"] = f"Bearer {user_token}"

        response = await client.post(
            "/api/votes/", json={"poll_id": poll_id, "option_id": option_id}
        )

        assert response.status_code == 201, (
            f"Vote failed: {response.status_code} - {response.text}"
        )

        resp_data = response.json() if response.content else {}
        assert resp_data.get("success") is True, f"Unexpected response: {resp_data}"
        assert "vote_id" in resp_data, f"vote_id missing in response: {resp_data}"

    async def test_vote_duplicate_forbidden(
        self, client: AsyncClient, test_admin_data, test_user_data, test_poll_data
    ):
        """Нельзя проголосовать дважды за один опрос"""

        poll_id, option_id, user_token = await self._setup_poll(
            client, test_admin_data, test_user_data, test_poll_data
        )

        client.headers["Authorization"] = f"Bearer {user_token}"

        first = await client.post(
            "/api/votes/", json={"poll_id": poll_id, "option_id": option_id}
        )
        assert first.status_code == 201

        second = await client.post(
            "/api/votes/", json={"poll_id": poll_id, "option_id": option_id}
        )

        assert second.status_code == 400, (
            f"Expected 400 for duplicate vote, got {second.status_code}: {second.text}"
        )

        if second.content:
            error_data = second.json()
            assert (
                "already" in str(error_data).lower()
                or "уже голосовали" in str(error_data).lower()
                or "detail" in error_data
            ), f"Unexpected error format: {error_data}"

    async def test_get_results(
        self, client: AsyncClient, test_admin_data, test_user_data, test_poll_data
    ):

        poll_id, option_id, user_token = await self._setup_poll(
            client, test_admin_data, test_user_data, test_poll_data
        )

        client.headers["Authorization"] = f"Bearer {user_token}"
        await client.post(
            "/api/votes/", json={"poll_id": poll_id, "option_id": option_id}
        )

        response = await client.get(f"/api/polls/{poll_id}/results")

        if response.status_code in [401, 403]:
            response = await client.get(
                f"/api/polls/{poll_id}/results",
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert response.status_code == 200, (
            f"Expected 200 for results, got {response.status_code}: {response.text}"
        )

        resp_data = response.json() if response.content else {}

        if "data" in resp_data and isinstance(resp_data["data"], dict):
            results = resp_data["data"]
        else:
            results = resp_data

        assert (
            "poll_id" in results
            or "total_votes" in results
            or "options" in results
            or "title" in results
        ), f"Unexpected results format: {results}"
