# tests/conftest.py
"""Фикстуры и конфигурация для интеграционных тестов"""

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

# =============================================================================
# 🔹 ИСПРАВЛЕНИЕ ДЛЯ WINDOWS (обязательно в начале файла!)
# =============================================================================
# Решает проблемы asyncpg + ProactorEventLoop на Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# =============================================================================
# 🔹 КОНФИГУРАЦИЯ
# =============================================================================
# Если тестовая БД не создана — создайте: createdb -U postgres poll_system_test
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:1878@localhost:5432/poll_system_test",
)


# =============================================================================
# 🔹 ТЕСТОВЫЙ ДВИЖОК БД (function scope для изоляции)
# =============================================================================
@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Создаёт и очищает схему БД для каждого теста"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,  # Без пула для тестов — чище
        echo=False,
    )

    # Создаём таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Очищаем после теста (изоляция)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# =============================================================================
# 🔹 СЕССИЯ С ТРАНЗАКЦИЕЙ (function scope)
# =============================================================================
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
        # 🔹 Явно начинаем транзакцию (НЕ как контекстный менеджер!)
        await session.begin()
        try:
            # 🔹 Отдаём сессию тесту — транзакция ещё открыта!
            yield session
        finally:
            # 🔹 Откатываем все изменения после теста (полная изоляция)
            await session.rollback()


# =============================================================================
# 🔹 HTTP КЛИЕНТ (function scope)
# =============================================================================
@pytest_asyncio.fixture(scope="function")
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client с переопределённой зависимостью get_db"""

    # Переопределяем get_db для использования тестовой сессии
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=30.0,
        follow_redirects=True,  # 🔹 🔥 ДОБАВЛЕНО: для обработки 307 редиректов! 🔥
    ) as ac:
        yield ac

    # Очищаем переопределения после теста
    app.dependency_overrides.clear()


# =============================================================================
# 🔹 АВТОРИЗОВАННЫЕ КЛИЕНТЫ (function scope)
# =============================================================================


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client, test_user_data):
    """Клиент с токеном обычного пользователя (гибкое извлечение токена)"""
    reg = await client.post("/api/auth/register", json=test_user_data)
    reg_data = reg.json()

    # 🔹 Гибкое извлечение access_token (поддерживает разные форматы):
    if (
        "data" in reg_data
        and isinstance(reg_data["data"], dict)
        and "access_token" in reg_data["data"]
    ):
        token = reg_data["data"]["access_token"]
    elif "access_token" in reg_data:
        token = reg_data["access_token"]
    else:
        # 🔹 Если токен не найден — выводим ответ для отладки:
        pytest.fail(f"access_token not found in response: {reg_data}")

    client.headers["Authorization"] = f"Bearer {token}"
    yield client
    client.headers.pop("Authorization", None)


@pytest_asyncio.fixture(scope="function")
async def admin_client(client, test_admin_data):
    """Клиент с токеном администратора (гибкое извлечение токена)"""
    reg = await client.post("/api/auth/register", json=test_admin_data)
    reg_data = reg.json()

    # 🔹 Гибкое извлечение access_token:
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


# =============================================================================
# 🔹 ТЕСТОВЫЕ ДАННЫЕ (синхронные фикстуры — обычный @pytest.fixture)
# =============================================================================
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


# =============================================================================
# 🔹 🔥 НОВАЯ ФИКСТУРА: Тестовый файл для баннеров (ДОБАВЬТЕ ЭТО В КОНЕЦ ФАЙЛА) 🔥
# =============================================================================

# tests/conftest.py - замените фикстуру test_banner_file на эту:

# tests/conftest.py - замените фикстуру test_banner_file на эту:


@pytest_asyncio.fixture(scope="function")
async def test_banner_file(test_session: AsyncSession):
    """
    Создаёт тестовый файл в БД для привязки баннеров к опросам.
    Сначала создаёт тестового пользователя, чтобы избежать FK-ошибки.
    """
    from src.models.file import FileMetadata
    from src.models.user import User, UserRole  # ← Импортируйте User!
    from sqlalchemy import select

    # 🔹 Шаг 1: Создаём тестового пользователя (если нужно)
    # Используем уникальный student_id, чтобы не конфликтовать с другими тестами
    test_student_id = "FILE_TEST_USER_9999"

    # Проверяем, существует ли уже пользователь
    existing_user = await test_session.execute(
        select(User).where(User.student_id == test_student_id)
    )
    user = existing_user.scalar_one_or_none()

    if not user:
        # Создаём нового пользователя
        user = User(
            student_id=test_student_id,
            name="File Test User",
            faculty="Test Faculty",
            password_hash="dummy_hash",  # Не используется в тестах
            role=UserRole.USER,
        )
        test_session.add(user)
        await test_session.flush()  # Получаем user.id

    # 🔹 Шаг 2: Создаём файл с валидным uploaded_by
    file_meta = FileMetadata(
        id=9999,
        entity_type="poll",
        entity_id=1,
        category="banner",
        file_key="test/test_banner.jpg",
        original_filename="test_banner.jpg",
        content_type="image/jpeg",
        size_bytes=1024,
        uploaded_by=test_student_id,  # ← Используем реального пользователя!
    )

    test_session.add(file_meta)
    await test_session.commit()
    await test_session.refresh(file_meta)

    yield file_meta

    # 🔹 Очищаем после теста
    try:
        await test_session.delete(file_meta)
        # Не удаляем пользователя — он может использоваться другими тестами
        await test_session.commit()
    except:
        pass
