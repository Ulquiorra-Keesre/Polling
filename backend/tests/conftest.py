import os
import sys
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.main import app
from src.database.connection import Base, get_db

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_password@localhost:5432/poll_system_test",
)


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Создаёт и очищает схему БД для каждого теста"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Асинхронная сессия с явным управлением транзакцией"""
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client с переопределённой зависимостью get_db"""

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=30.0,
        follow_redirects=True,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client, test_user_data):
    """Клиент с токеном обычного пользователя (гибкое извлечение токена)"""
    reg = await client.post("/api/auth/register", json=test_user_data)
    reg_data = reg.json()

    if (
        "data" in reg_data
        and isinstance(reg_data["data"], dict)
        and "access_token" in reg_data["data"]
    ):
        token = reg_data["data"]["access_token"]
    elif "access_token" in reg_data:
        token = reg_data["access_token"]
    else:
        pytest.fail(f"access_token not found in response: {reg_data}")

    client.headers["Authorization"] = f"Bearer {token}"
    yield client
    client.headers.pop("Authorization", None)


@pytest_asyncio.fixture(scope="function")
async def admin_client(client, test_admin_data):
    """Клиент с токеном администратора (гибкое извлечение токена)"""
    reg = await client.post("/api/auth/register", json=test_admin_data)
    reg_data = reg.json()

    if (
        "data" in reg_data
        and isinstance(reg_data["data"], dict)
        and "access_token" in reg_data["data"]
    ):
        token = reg_data["data"]["access_token"]
    elif "access_token" in reg_data:
        token = reg_data["access_token"]
    else:
        pytest.fail(f"access_token not found in response: {reg_data}")

    client.headers["Authorization"] = f"Bearer {token}"
    yield client
    client.headers.pop("Authorization", None)


@pytest.fixture
def test_user_data():
    """Данные для регистрации обычного пользователя"""
    return {
        "student_id": "TEST_USER_001",
        "name": "Test User",
        "faculty": "Test Faculty",
        "password": "TestPassword123!",
        "role": "user",
    }


@pytest.fixture
def test_admin_data():
    """Данные для регистрации администратора"""
    return {
        "student_id": "TEST_ADMIN_777",
        "name": "Test Admin",
        "faculty": "Test Faculty",
        "password": "AdminPassword123!",
        "role": "admin",
    }


@pytest.fixture
def test_poll_data():
    """Данные для создания опроса"""
    return {
        "title": "Тестовый опрос",
        "description": "Описание для автоматических тестов",
        "end_date": "2027-12-31T23:59:59Z",
        "options": [
            {"text": "Вариант 1"},
            {"text": "Вариант 2"},
        ],
    }


@pytest_asyncio.fixture(scope="function")
async def test_banner_file(test_session: AsyncSession):
    """
    Создаёт тестовый файл в БД для привязки баннеров к опросам.
    Сначала создаёт тестового пользователя, чтобы избежать FK-ошибки.
    """
    from src.models.file import FileMetadata
    from src.models.user import User, UserRole
    from sqlalchemy import select

    test_student_id = "FILE_TEST_USER_9999"

    existing_user = await test_session.execute(
        select(User).where(User.student_id == test_student_id)
    )
    user = existing_user.scalar_one_or_none()

    if not user:
        user = User(
            student_id=test_student_id,
            name="File Test User",
            faculty="Test Faculty",
            password_hash="dummy_hash",
            role=UserRole.USER,
        )
        test_session.add(user)
        await test_session.flush()

    file_meta = FileMetadata(
        id=9999,
        entity_type="poll",
        entity_id=1,
        category="banner",
        file_key="test/test_banner.jpg",
        original_filename="test_banner.jpg",
        content_type="image/jpeg",
        size_bytes=1024,
        uploaded_by=test_student_id,
    )

    test_session.add(file_meta)
    await test_session.commit()
    await test_session.refresh(file_meta)

    yield file_meta

    try:
        await test_session.delete(file_meta)
        await test_session.commit()
    except Exception as e:
        print(f"Warning: cleanup failed for test_banner_file: {e}")
        await test_session.rollback()
