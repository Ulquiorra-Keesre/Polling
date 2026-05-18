from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.models.vote import Vote
from src.models.poll import Option

from src.queries.orm import Repository


async def create_vote(
    db: AsyncSession, poll_id: int, option_id: int, student_id: str
) -> dict:
    """Создать голос"""
    repo = Repository(db)

    result = await repo.votes.create_vote(
        poll_id=poll_id, option_id=option_id, student_id=student_id
    )
    return result


async def has_user_voted(db: AsyncSession, poll_id: int, student_id: str) -> bool:
    """Проверить, голосовал ли пользователь в опросе"""
    repo = Repository(db)
    return await repo.votes.has_user_voted_in_poll(poll_id, student_id)


async def get_user_votes(db: AsyncSession, student_id: str) -> List[dict]:
    """Получить все голоса пользователя"""
    repo = Repository(db)

    votes = await repo.votes.get_many_by_field(Vote, "student_id", student_id)

    vote_list = []
    for vote in votes:
        poll = await repo.polls.get_by_id_with_details(vote.poll_id)
        option = await repo.options.get_by_id(Option, vote.option_id)

        if poll and option:
            vote_list.append(
                {
                    "id": vote.id,
                    "poll_id": vote.poll_id,
                    "poll_title": poll.title,
                    "option_id": vote.option_id,
                    "option_text": option.text,
                    "created_at": vote.created_at,
                }
            )

    return vote_list
