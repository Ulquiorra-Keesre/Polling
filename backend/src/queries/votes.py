# backend/src/queries/votes.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.models.vote import Vote
from src.models.poll import Option, Poll
from src.models.vote import VoteCreate, VoteResponse

async def has_user_voted(db: AsyncSession, poll_id: int, student_id: str) -> bool:
    """Проверить, голосовал ли пользователь в опросе"""
    result = await db.execute(
        select(Vote).where(
            and_(
                Vote.poll_id == poll_id,
                Vote.student_id == student_id
            )
        )
    )
    return result.scalar_one_or_none() is not None

async def create_vote(db: AsyncSession, poll_id: int, option_id: int, student_id: str) -> VoteResponse:
    """Создать голос"""
    
    # Проверяем существование опроса и варианта
    poll_result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = poll_result.scalar_one_or_none()
    if not poll:
        raise ValueError("Опрос не найден")
    
    option_result = await db.execute(
        select(Option).where(
            and_(
                Option.id == option_id,
                Option.poll_id == poll_id
            )
        )
    )
    option = option_result.scalar_one_or_none()
    if not option:
        raise ValueError("Вариант ответа не найден")
    
    # Создаем голос
    db_vote = Vote(
        poll_id=poll_id,
        option_id=option_id,
        student_id=student_id
    )
    
    # Обновляем счетчики
    option.votes += 1
    poll.total_votes += 1
    
    db.add(db_vote)
    await db.commit()
    await db.refresh(db_vote)
    
    return VoteResponse.model_validate(db_vote)

async def get_user_votes(db: AsyncSession, student_id: str):
    """Получить все голоса пользователя"""
    from sqlalchemy import select
    from src.models.vote import Vote
    
    result = await db.execute(
        select(Vote).where(Vote.student_id == student_id)
    )
    votes = result.scalars().all()
    return [VoteResponse.model_validate(vote) for vote in votes]