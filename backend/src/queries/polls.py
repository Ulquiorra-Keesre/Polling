# backend/src/queries/polls.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.queries.orm import Repository
from src.models.poll import Poll, PollCreate

async def get_all_polls(db: AsyncSession) -> List[Poll]:
    """Получить все опросы"""
    repo = Repository(db)
    polls = await repo.polls.get_all_with_options()
    return polls

async def get_poll_by_id(db: AsyncSession, poll_id: int) -> Optional[Poll]:
    """Получить опрос по ID"""
    repo = Repository(db)
    poll = await repo.polls.get_by_id_with_details(poll_id)
    return poll

async def get_poll_results(db: AsyncSession, poll_id: int) -> Optional[dict]:
    """Получить результаты опроса"""
    repo = Repository(db)
    results = await repo.votes.get_poll_results(poll_id)
    return results

async def create_poll(db: AsyncSession, poll_data: PollCreate) -> Poll:
    """Создать новый опрос"""
    repo = Repository(db)
    
    poll = await repo.polls.create_poll_with_options(
        title=poll_data.title,
        description=poll_data.description,
        end_date=poll_data.end_date,
        options=[option.text for option in poll_data.options]
    )
    return poll

async def get_active_polls(db: AsyncSession) -> List[Poll]:
    """Получить активные опросы"""
    repo = Repository(db)
    polls = await repo.polls.get_active_polls()
    return polls