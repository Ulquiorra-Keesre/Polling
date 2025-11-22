# backend/src/queries/polls.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from src.models.poll import Poll, Option
from src.models.poll import PollCreate, PollResponse
from datetime import datetime

async def get_all_polls(db: AsyncSession) -> list[PollResponse]:
    """Получить все активные опросы"""
    result = await db.execute(
        select(Poll)
        .where(Poll.end_date > datetime.utcnow())
        .options(selectinload(Poll.options))
        .order_by(Poll.created_at.desc())
    )
    polls = result.scalars().all()
    return [PollResponse.model_validate(poll) for poll in polls]

async def get_poll_by_id(db: AsyncSession, poll_id: int) -> PollResponse | None:
    """Получить опрос по ID"""
    result = await db.execute(
        select(Poll)
        .where(Poll.id == poll_id)
        .options(selectinload(Poll.options))
    )
    poll = result.scalar_one_or_none()
    return PollResponse.model_validate(poll) if poll else None

async def get_poll_results(db: AsyncSession, poll_id: int) -> PollResponse | None:
    """Получить результаты опроса"""
    return await get_poll_by_id(db, poll_id)

async def create_poll(db: AsyncSession, poll: PollCreate) -> PollResponse:
    """Создать новый опрос"""
    db_poll = Poll(
        title=poll.title,
        description=poll.description,
        end_date=poll.end_date
    )
    
    # Добавляем варианты ответов
    for option in poll.options:
        db_option = Option(text=option.text)
        db_poll.options.append(db_option)
    
    db.add(db_poll)
    await db.commit()
    await db.refresh(db_poll)
    
    # Загружаем с options
    result = await db.execute(
        select(Poll)
        .where(Poll.id == db_poll.id)
        .options(selectinload(Poll.options))
    )
    poll_with_options = result.scalar_one()
    
    return PollResponse.model_validate(poll_with_options)