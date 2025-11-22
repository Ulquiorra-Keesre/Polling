# backend/src/api/routes/polls.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List

from src.models.poll import PollResponse, PollCreate, PollResults
from src.queries.polls import (
    get_all_polls, 
    get_poll_by_id, 
    get_poll_results, 
    create_poll
)
from src.api.dependencies import DatabaseDep, CurrentUser, CurrentAdmin

router = APIRouter()

@router.get("/", response_model=List[PollResponse])
async def get_polls(
    db: DatabaseDep,
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(100, ge=1, le=100, description="Лимит записей")
):
    """
    Получить список всех активных опросов
    """
    try:
        polls = await get_all_polls(db)
        return polls[skip:skip + limit]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении опросов: {str(e)}"
        )

@router.get("/{poll_id}", response_model=PollResponse)
async def get_poll(
    poll_id: int,
    db: DatabaseDep
):
    """
    Получить опрос по ID
    """
    poll = await get_poll_by_id(db, poll_id)
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден"
        )
    return poll

@router.get("/{poll_id}/results", response_model=PollResults)
async def get_poll_results(
    poll_id: int,
    db: DatabaseDep
):
    """
    Получить результаты опроса
    """
    results = await get_poll_results(db, poll_id)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Опрос не найден"
        )
    return results


@router.post("/", response_model=PollResponse, status_code=status.HTTP_201_CREATED)
async def create_new_poll(
    poll: PollCreate,
    db: DatabaseDep,
    admin_id: CurrentAdmin  # ← Используем dependency для админов
):
    """
    Создать новый опрос (только для администраторов)
    """
    try:
        # Логирование
        print(f"Администратор {admin_id} создает новый опрос: {poll.title}")
        
        return await create_poll(db, poll)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании опроса: {str(e)}"
        )