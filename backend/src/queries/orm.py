from sqlalchemy import select, and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any

from .core import DatabaseManager
from ..models.user import User
from ..models.poll import Poll, Option
from ..models.vote import Vote

class UserRepository(DatabaseManager):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.model = User

    async def get_by_student_id(self, student_id: str) -> Optional[User]:
        """Получить пользователя по student_id"""
        result = await self.session.execute(
            select(User).where(User.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def get_admins(self) -> List[User]:
        """Получить всех администраторов"""
        result = await self.session.execute(
            select(User).where(User.is_admin == True)
        )
        return result.scalars().all()

    async def create_user(self, student_id: str, name: str, faculty: str, is_admin: bool = False) -> User:
        """Создать нового пользователя"""

        admin_student_ids = ["777"]  #Все Админские ID
    
        isadmin = is_admin
        if student_id in admin_student_ids:
            isadmin = True

        return await self.create(User, 
            student_id=student_id,
            name=name,
            faculty=faculty,
            is_admin=isadmin
        )
    
    async def update(self, user_id: int, **data) -> Optional[User]:
        """Обновить пользователя"""
        return await super().update(User, user_id, **data)

class PollRepository(DatabaseManager):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.model = Poll

    async def get_all_with_options(self) -> List[Poll]:
        """Получить все опросы с вариантами ответов"""
        result = await self.session.execute(
            select(Poll).options(selectinload(Poll.options))
        )
        return result.scalars().all()

    async def get_by_id_with_details(self, poll_id: int) -> Optional[Poll]:
        """Получить опрос по ID с детальной информацией"""
        result = await self.session.execute(
            select(Poll)
            .options(selectinload(Poll.options))
            .where(Poll.id == poll_id)
        )
        return result.scalar_one_or_none()

    async def get_active_polls(self) -> List[Poll]:
        """Получить активные опросы (у которых end_date еще не наступил)"""
        from datetime import datetime
        result = await self.session.execute(
            select(Poll)
            .options(selectinload(Poll.options))
            .where(Poll.end_date > datetime.now())
        )
        return result.scalars().all()

    async def create_poll_with_options(self, title: str, description: str, end_date: str, options: List[str]) -> Poll:
        """Создать опрос с вариантами ответов"""
        try:
            # Создаем опрос
            poll = Poll(
                title=title,
                description=description,
                end_date=end_date,
                total_votes=0
            )
            self.session.add(poll)
            await self.session.flush()  # Получаем ID опроса

            # Создаем варианты ответов
            for option_text in options:
                option = Option(
                    poll_id=poll.id,
                    text=option_text,
                    votes=0
                )
                self.session.add(option)

            await self.session.commit()
            await self.session.refresh(poll)
            return poll
        except Exception as e:
            await self.session.rollback()
            raise

    async def update_poll_votes(self, poll_id: int) -> None:
        """Обновить total_votes для опроса"""
        # Считаем общее количество голосов для этого опроса
        result = await self.session.execute(
            select(func.sum(Option.votes))
            .where(Option.poll_id == poll_id)
        )
        total_votes = result.scalar() or 0

        # Обновляем опрос
        await self.session.execute(
            update(Poll)
            .where(Poll.id == poll_id)
            .values(total_votes=total_votes)
        )
        await self.session.commit()

class OptionRepository(DatabaseManager):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.model = Option

    async def get_by_poll_id(self, poll_id: int) -> List[Option]:
        """Получить все варианты ответов для опроса"""
        result = await self.session.execute(
            select(Option).where(Option.poll_id == poll_id)
        )
        return result.scalars().all()

    async def increment_votes(self, option_id: int) -> Option:
        """Увеличить счетчик голосов для варианта ответа"""
        option = await self.get_by_id(Option, option_id)
        if option:
            option.votes += 1
            await self.session.commit()
            await self.session.refresh(option)
        return option

class VoteRepository(DatabaseManager):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.model = Vote

    async def get_user_votes_for_poll(self, poll_id: int, student_id: str) -> List[Vote]:
        """Получить голоса пользователя в конкретном опросе"""
        result = await self.session.execute(
            select(Vote).where(
                and_(Vote.poll_id == poll_id, Vote.student_id == student_id)
            )
        )
        return result.scalars().all()

    async def has_user_voted_in_poll(self, poll_id: int, student_id: str) -> bool:
        """Проверить, голосовал ли пользователь в этом опросе"""
        votes = await self.get_user_votes_for_poll(poll_id, student_id)
        return len(votes) > 0

    async def create_vote(self, poll_id: int, option_id: int, student_id: str) -> Dict[str, Any]:
        """Создать голос и обновить счетчики"""
        try:
            # Проверяем, существует ли вариант ответа и принадлежит ли он опросу
            option_result = await self.session.execute(
                select(Option).where(
                    and_(Option.id == option_id, Option.poll_id == poll_id)
                )
            )
            option = option_result.scalar_one_or_none()
            
            if not option:
                raise ValueError("Option not found or does not belong to the poll")

            # Проверяем, не голосовал ли уже пользователь в этом опросе
            if await self.has_user_voted_in_poll(poll_id, student_id):
                raise ValueError("User has already voted in this poll")

            # Создаем запись голоса
            vote = await self.create(Vote,
                poll_id=poll_id,
                option_id=option_id,
                student_id=student_id
            )

            # Обновляем счетчик голосов для варианта ответа
            option_repo = OptionRepository(self.session)
            await option_repo.increment_votes(option_id)

            # Обновляем общее количество голосов для опроса
            poll_repo = PollRepository(self.session)
            await poll_repo.update_poll_votes(poll_id)

            return {
                "vote": vote,
                "option": option,
                "poll_id": poll_id
            }
        except Exception as e:
            await self.session.rollback()
            raise

    async def get_poll_results(self, poll_id: int) -> Dict[str, Any]:
        """Получить результаты голосования для опроса"""
        # Получаем опрос с вариантами
        poll_repo = PollRepository(self.session)
        poll = await poll_repo.get_by_id_with_details(poll_id)
        
        if not poll:
            return None

        # Получаем общее количество голосовавших
        result = await self.session.execute(
            select(func.count(Vote.id))
            .where(Vote.poll_id == poll_id)
        )
        total_voters = result.scalar()

        return {
            "poll": {
                "id": poll.id,
                "title": poll.title,
                "description": poll.description,
                "total_votes": poll.total_votes,
                "total_voters": total_voters,
                "end_date": poll.end_date
            },
            "options": [
                {
                    "id": option.id,
                    "text": option.text,
                    "votes": option.votes,
                    "percentage": (option.votes / poll.total_votes * 100) if poll.total_votes > 0 else 0
                }
                for option in poll.options
            ]
        }

class Repository:
    def __init__(self, session: AsyncSession):
        self.users = UserRepository(session)
        self.polls = PollRepository(session)
        self.options = OptionRepository(session)
        self.votes = VoteRepository(session)