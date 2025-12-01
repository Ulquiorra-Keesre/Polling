# # backend/src/api/routes/polls.py
# from fastapi import APIRouter, HTTPException, status, Depends, Query
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import Annotated, List

# from src.models.poll import PollResponse, PollCreate, PollResults
# from src.queries.polls import (
#     get_all_polls, 
#     get_poll_by_id, 
#     get_poll_results, 
#     create_poll
# )
# from src.api.dependencies import DatabaseDep, CurrentUser, CurrentAdmin

# router = APIRouter()

# @router.get("/", response_model=List[PollResponse])
# async def get_polls(
#     db: DatabaseDep,
#     skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
#     limit: int = Query(100, ge=1, le=100, description="Лимит записей")
# ):
#     """
#     Получить список всех активных опросов
#     """
#     try:
#         polls = await get_all_polls(db)
#         return polls[skip:skip + limit]
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Ошибка при получении опросов: {str(e)}"
#         )

# @router.get("/{poll_id}", response_model=PollResponse)
# async def get_poll(
#     poll_id: int,
#     db: DatabaseDep
# ):
#     """
#     Получить опрос по ID
#     """
#     poll = await get_poll_by_id(db, poll_id)
#     if not poll:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Опрос не найден"
#         )
#     return poll

# @router.get("/{poll_id}/results", response_model=PollResults)
# async def get_poll_results(
#     poll_id: int,
#     db: DatabaseDep
# ):
#     """
#     Получить результаты опроса
#     """
#     results = await get_poll_results(db, poll_id)
#     if not results:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Опрос не найден"
#         )
#     return results


# @router.post("/", response_model=PollResponse, status_code=status.HTTP_201_CREATED)
# async def create_new_poll(
#     poll: PollCreate,
#     db: DatabaseDep,
#     admin_id: CurrentAdmin  # ← Используем dependency для админов
# ):
#     """
#     Создать новый опрос (только для администраторов)
#     """
#     try:
#         # Логирование
#         print(f"Администратор {admin_id} создает новый опрос: {poll.title}")
        
#         return await create_poll(db, poll)
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Ошибка при создании опроса: {str(e)}"
#         )

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import select, func

from src.models.poll import Poll, Option
from src.api.dependencies import DatabaseDep, CurrentUser, CurrentAdmin

router = APIRouter()

# ========== GET ALL POLLS ==========
@router.get("/")
async def get_polls(
    db: DatabaseDep,
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(100, ge=1, le=100, description="Лимит записей")
):
    """
    Получить список всех активных опросов
    """
    try:
        # Получаем опросы
        result = await db.execute(
            select(Poll).order_by(Poll.created_at.desc())
        )
        polls = result.scalars().all()
        
        # Вручную создаем ответ для каждого опроса
        response_polls = []
        for poll in polls[skip:skip + limit]:
            # Получаем варианты для этого опроса
            options_result = await db.execute(
                select(Option).where(Option.poll_id == poll.id)
            )
            options = options_result.scalars().all()
            
            # Создаем словарь вручную
            poll_dict = {
                "id": poll.id,
                "title": poll.title,
                "description": poll.description,
                "end_date": poll.end_date.isoformat() if poll.end_date else None,
                "total_votes": poll.total_votes,
                "created_at": poll.created_at.isoformat() if poll.created_at else None,
                "options": [
                    {
                        "id": opt.id,
                        "text": opt.text,
                        "votes": opt.votes
                    }
                    for opt in options
                ]
            }
            response_polls.append(poll_dict)
        
        return response_polls
        
    except Exception as e:
        print(f"Error getting polls: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении опросов: {str(e)}"
        )

# ========== CREATE POLL ==========
@router.post("/")
async def create_new_poll(
    poll_data: Dict[str, Any],
    db: DatabaseDep,
    admin_id: CurrentAdmin
):
    """
    Создать новый опрос (только для администраторов)
    """
    print(f"=== CREATE POLL REQUEST ===")
    print(f"Admin ID: {admin_id}")
    print(f"Poll data: {poll_data}")
    
    try:
        # Валидация входных данных
        if not poll_data.get("title") or not isinstance(poll_data["title"], str):
            return {
                "success": False,
                "error": "Заголовок обязателен и должен быть строкой"
            }
        
        options = poll_data.get("options", [])
        if not options or not isinstance(options, list) or len(options) < 1:
            return {
                "success": False,
                "error": "Должен быть хотя бы один вариант ответа"
            }
        
        # 1. Создаем опрос
        poll = Poll(
            title=poll_data["title"],
            description=poll_data.get("description", ""),
            end_date=poll_data.get("end_date") or datetime.now() + timedelta(days=7),
            total_votes=0
        )
        
        db.add(poll)
        await db.flush()
        
        # 2. Создаем варианты ответов
        created_options = []
        for option_text in options:
            option = Option(
                poll_id=poll.id,
                text=str(option_text),
                votes=0
            )
            db.add(option)
            created_options.append(option)
        
        await db.commit()
        
        print(f"✅ Poll created successfully with ID: {poll.id}")
        
        # 3. Возвращаем ответ
        return {
            "success": True,
            "message": "Опрос успешно создан",
            "poll_id": poll.id,
            "title": poll.title,
            "options_count": len(options)
        }
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Error creating poll: {str(e)}")
        return {
            "success": False,
            "error": f"Ошибка при создании опроса: {str(e)}"
        }

# ========== GET POLL BY ID ==========
@router.get("/{poll_id}")
async def get_poll(
    poll_id: int,
    db: DatabaseDep
):
    """
    Получить опрос по ID
    """
    try:
        # Получаем опрос
        result = await db.execute(
            select(Poll).where(Poll.id == poll_id)
        )
        poll = result.scalar_one_or_none()
        
        if not poll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Опрос не найден"
            )
        
        # Получаем варианты
        options_result = await db.execute(
            select(Option).where(Option.poll_id == poll_id)
        )
        options = options_result.scalars().all()
        
        # Создаем ответ вручную
        return {
            "id": poll.id,
            "title": poll.title,
            "description": poll.description,
            "end_date": poll.end_date.isoformat() if poll.end_date else None,
            "total_votes": poll.total_votes,
            "created_at": poll.created_at.isoformat() if poll.created_at else None,
            "options": [
                {
                    "id": opt.id,
                    "text": opt.text,
                    "votes": opt.votes
                }
                for opt in options
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting poll {poll_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении опроса: {str(e)}"
        )

# ========== GET POLL RESULTS ==========
@router.get("/{poll_id}/results")
async def get_poll_results(
    poll_id: int,
    db: DatabaseDep
):
    """
    Получить результаты опроса с процентами
    """
    try:
        # 1. Проверяем существование опроса
        poll_result = await db.execute(
            select(Poll).where(Poll.id == poll_id)
        )
        poll = poll_result.scalar_one_or_none()
        
        if not poll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Опрос не найден"
            )
        
        # 2. Получаем варианты с голосами
        options_result = await db.execute(
            select(Option).where(Option.poll_id == poll_id).order_by(Option.votes.desc())
        )
        options = options_result.scalars().all()
        
        # 3. Рассчитываем проценты
        total_votes = poll.total_votes or 1  # чтобы избежать деления на ноль
        options_with_percents = []
        
        for option in options:
            percentage = (option.votes / total_votes) * 100 if total_votes > 0 else 0
            
            options_with_percents.append({
                "id": option.id,
                "text": option.text,
                "votes": option.votes,
                "percentage": round(percentage, 2)
            })
        
        # 4. Создаем полный ответ
        return {
            "poll_id": poll.id,
            "title": poll.title,
            "description": poll.description,
            "total_votes": poll.total_votes,
            "end_date": poll.end_date.isoformat() if poll.end_date else None,
            "created_at": poll.created_at.isoformat() if poll.created_at else None,
            "options": options_with_percents,
            "has_ended": poll.end_date < datetime.now() if poll.end_date else False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting poll results {poll_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении результатов: {str(e)}"
        )

# ========== GET ACTIVE POLLS ==========
@router.get("/active")
async def get_active_polls(
    db: DatabaseDep
):
    """
    Получить только активные опросы (еще не завершившиеся)
    """
    try:
        current_time = datetime.now()
        
        result = await db.execute(
            select(Poll)
            .where(Poll.end_date > current_time)
            .order_by(Poll.created_at.desc())
        )
        polls = result.scalars().all()
        
        active_polls = []
        for poll in polls:
            options_result = await db.execute(
                select(Option).where(Option.poll_id == poll.id)
            )
            options = options_result.scalars().all()
            
            poll_dict = {
                "id": poll.id,
                "title": poll.title,
                "description": poll.description,
                "end_date": poll.end_date.isoformat(),
                "total_votes": poll.total_votes,
                "created_at": poll.created_at.isoformat(),
                "options": [
                    {
                        "id": opt.id,
                        "text": opt.text,
                        "votes": opt.votes
                    }
                    for opt in options
                ],
                "is_active": True
            }
            active_polls.append(poll_dict)
        
        return active_polls
        
    except Exception as e:
        print(f"Error getting active polls: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении активных опросов: {str(e)}"
        )