from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result
from typing import List, Optional, Any, Type, TypeVar
import logging

logger = logging.getLogger(__name__)

# Generic type
ModelType = TypeVar('ModelType')

class DatabaseManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute_query(self, query) -> Result:
        """Выполнить произвольный запрос"""
        return await self.session.execute(query)

    async def get_all(self, model: Type[ModelType]) -> List[ModelType]:
        """Получить все записи модели"""
        result = await self.session.execute(select(model))
        return result.scalars().all()

    async def get_by_id(self, model: Type[ModelType], record_id: int) -> Optional[ModelType]:
        """Получить запись по ID"""
        result = await self.session.execute(
            select(model).where(model.id == record_id)
        )
        return result.scalar_one_or_none()

    async def create(self, model: Type[ModelType], **data) -> ModelType:
        """Создать новую запись"""
        try:
            instance = model(**data)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)
            return instance
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating record in {model.__name__}: {e}")
            raise

    async def bulk_create(self, model: Type[ModelType], data_list: List[dict]) -> List[ModelType]:
        """Создать несколько записей"""
        try:
            instances = [model(**data) for data in data_list]
            self.session.add_all(instances)
            await self.session.commit()
            
            # Refresh всех instances
            for instance in instances:
                await self.session.refresh(instance)
                
            return instances
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error bulk creating records in {model.__name__}: {e}")
            raise

    async def update(self, model: Type[ModelType], record_id: int, **data) -> Optional[ModelType]:
        """Обновить запись"""
        try:
            instance = await self.get_by_id(model, record_id)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await self.session.commit()
                await self.session.refresh(instance)
            return instance
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating record in {model.__name__}: {e}")
            raise

    async def delete(self, model: Type[ModelType], record_id: int) -> bool:
        """Удалить запись"""
        try:
            instance = await self.get_by_id(model, record_id)
            if instance:
                await self.session.delete(instance)
                await self.session.commit()
                return True
            return False
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting record in {model.__name__}: {e}")
            raise

    async def get_by_field(self, model: Type[ModelType], field_name: str, value: Any) -> Optional[ModelType]:
        """Получить запись по значению поля"""
        result = await self.session.execute(
            select(model).where(getattr(model, field_name) == value)
        )
        return result.scalar_one_or_none()

    async def get_many_by_field(self, model: Type[ModelType], field_name: str, value: Any) -> List[ModelType]:
        """Получить несколько записей по значению поля"""
        result = await self.session.execute(
            select(model).where(getattr(model, field_name) == value)
        )
        return result.scalars().all()

    async def exists(self, model: Type[ModelType], record_id: int) -> bool:
        """Проверить существование записи"""
        instance = await self.get_by_id(model, record_id)
        return instance is not None

    async def count(self, model: Type[ModelType]) -> int:
        """Получить количество записей в таблице"""
        result = await self.session.execute(select(model))
        return len(result.scalars().all())

# Утилиты для работы с базой
async def check_database_connection(async_engine):
    """Проверить подключение к базе данных"""
    async with async_engine.connect() as conn:
        result = await conn.execute(select(1))
        version = result.first()
        logger.info("Database connection successful")
        return version

async def create_tables(async_engine):
    """Создать все таблицы"""
    from src.database.connection import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("All tables created successfully")

async def get_database_status(async_engine):
    """Получить статус базы данных и статистику таблиц"""
    from src.models.user import User
    from src.models.poll import Poll, Option
    from src.models.vote import Vote
    
    async with async_engine.connect() as conn:
        # Проверяем подключение
        connection_ok = await check_database_connection(async_engine)
        
        # Получаем количество записей в каждой таблице
        tables_info = {}
        
        for model, name in [(User, "users"), (Poll, "polls"), (Option, "options"), (Vote, "votes")]:
            try:
                result = await conn.execute(select(model))
                count = len(result.scalars().all())
                tables_info[name] = count
            except Exception as e:
                tables_info[name] = f"error: {e}"
        
        return {
            "connection": "ok" if connection_ok else "failed",
            "tables": tables_info
        }