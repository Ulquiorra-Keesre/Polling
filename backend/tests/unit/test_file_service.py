import pytest
from src.services.file_service import FileService


@pytest.mark.unit
class TestFileService:
    def test_validate_file_size_valid(self):
        service = FileService()
        assert service.validate_file_size(5 * 1024 * 1024, "banner") is True

    def test_validate_file_size_exceeded(self):
        service = FileService()
        assert service.validate_file_size(6 * 1024 * 1024, "banner") is False

    def test_validate_file_type_valid(self):
        service = FileService()
        assert service.is_file_type_allowed("image/jpeg", "banner") is True

    def test_validate_file_type_invalid(self):
        service = FileService()
        assert service.is_file_type_allowed("application/exe", "banner") is False

    def test_generate_file_key_unique(self):
        service = FileService()
        key1 = service.generate_file_key("test.jpg", "banner")
        key2 = service.generate_file_key("test.jpg", "banner")
        assert key1 != key2
        assert key1.endswith(".jpg")
