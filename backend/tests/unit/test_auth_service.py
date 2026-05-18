import pytest
from src.services.auth_service import AuthService
from src.models.user import User, UserRole


@pytest.mark.unit
class TestAuthService:
    def test_hash_password(self, test_user_data):
        auth = AuthService.__new__(AuthService)
        hashed = auth.hash_password(test_user_data["password"])
        assert hashed != test_user_data["password"]
        assert len(hashed) > 50

    def test_verify_password_correct(self, test_user_data):
        auth = AuthService.__new__(AuthService)
        hashed = auth.hash_password(test_user_data["password"])
        assert auth.verify_password(test_user_data["password"], hashed) is True

    def test_verify_password_incorrect(self, test_user_data):
        auth = AuthService.__new__(AuthService)
        hashed = auth.hash_password(test_user_data["password"])
        assert auth.verify_password("wrong", hashed) is False

    def test_check_user_role_admin(self, test_admin_data):
        auth = AuthService.__new__(AuthService)
        user = User(
            student_id=test_admin_data["student_id"],
            name=test_admin_data["name"],
            faculty=test_admin_data["faculty"],
            role=UserRole.ADMIN,
        )
        assert auth.check_user_role(user, [UserRole.ADMIN]) is True

    def test_check_user_role_denied(self, test_user_data):
        auth = AuthService.__new__(AuthService)
        user = User(
            student_id=test_user_data["student_id"],
            name=test_user_data["name"],
            faculty=test_user_data["faculty"],
            role=UserRole.USER,
        )
        assert auth.check_user_role(user, [UserRole.ADMIN]) is False
