import pytest
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError
from src.schemas.poll import PollCreate
from src.schemas.user import UserRegister


@pytest.mark.unit
class TestSchemaValidation:
    def test_poll_create_valid(self, test_poll_data):
        poll = PollCreate(**test_poll_data)
        assert poll.title == test_poll_data["title"]
        assert len(poll.options) == 2

    def test_poll_create_empty_title(self, test_poll_data):
        test_poll_data["title"] = ""
        with pytest.raises(ValidationError):
            PollCreate(**test_poll_data)

    def test_poll_create_single_option(self, test_poll_data):
        test_poll_data["options"] = [{"text": "One"}]
        with pytest.raises(ValidationError, match="too_short|at least 2"):
            PollCreate(**test_poll_data)

    def test_poll_create_past_end_date(self, test_poll_data):
        test_poll_data["end_date"] = datetime.now(timezone.utc) - timedelta(days=1)
        with pytest.raises(ValueError, match="будущем"):
            PollCreate(**test_poll_data)

    def test_user_register_valid(self, test_user_data):
        user = UserRegister(**test_user_data)
        assert user.student_id == test_user_data["student_id"]
