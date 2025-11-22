# backend/src/api/routes/votes.py
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.models.vote import VoteCreate
from src.queries.votes import create_vote, has_user_voted
from src.api.dependencies import DatabaseDep, CurrentUser

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def vote(
    vote_data: VoteCreate,
    db: DatabaseDep,
    student_id: CurrentUser
):
    """
    Проголосовать в опросе
    """
    try:
        # Проверяем, не голосовал ли уже пользователь
        if await has_user_voted(db, vote_data.poll_id, student_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Вы уже голосовали в этом опросе"
            )
        
        # Создаем голос
        vote_result = await create_vote(
            db, 
            vote_data.poll_id, 
            vote_data.option_id, 
            student_id
        )
        
        return {
            "success": True, 
            "message": "Голос успешно принят", 
            "vote": vote_result
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Ошибка при голосовании: {str(e)}"
        )

@router.get("/check/{poll_id}")
async def check_vote(
    poll_id: int,
    db: DatabaseDep,
    student_id: CurrentUser
):
    """
    Проверить, голосовал ли пользователь в указанном опросе
    """
    try:
        voted = await has_user_voted(db, poll_id, student_id)
        return {
            "has_voted": voted, 
            "poll_id": poll_id,
            "student_id": student_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при проверке голоса: {str(e)}"
        )

@router.get("/user-votes")
async def get_user_votes(
    db: DatabaseDep,
    student_id: CurrentUser
):
    """
    Получить все голоса текущего пользователя
    """
    from src.queries.votes import get_user_votes as get_user_votes_query
    
    try:
        votes = await get_user_votes_query(db, student_id)
        return {
            "student_id": student_id,
            "votes": votes
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении голосов: {str(e)}"
        )