# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from contextlib import asynccontextmanager
import traceback

from src.api.routes import auth, polls, votes
from src.database.connection import create_tables
from src.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    print("✅ Database tables created")
    yield
    # Shutdown
    print("🛑 Application shutdown")

app = FastAPI(
    title="Система студенческих опросов",
    description="API для системы анонимных студенческих опросов",
    version="1.0.0",
    lifespan=lifespan
)

# ========== CORS MIDDLEWARE ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # добавьте другие если нужно
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ========== EXCEPTION HANDLERS ==========
@app.exception_handler(ResponseValidationError)
async def response_validation_handler(request: Request, exc: ResponseValidationError):
    """Обработчик ошибок валидации ответа"""
    print(f"ResponseValidationError: {exc}")
    print(traceback.format_exc())
    
    return JSONResponse(
        status_code=200,  # Возвращаем 200 чтобы CORS заголовки работали
        content={
            "success": False,
            "error": "Ошибка валидации ответа сервера",
            "details": str(exc)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    print(f"Global exception: {exc}")
    print(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Внутренняя ошибка сервера",
            "details": str(exc)
        }
    )

# ========== OPTIONS HANDLER FOR CORS PREFLIGHT ==========
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    # Обрабатываем OPTIONS (preflight) запросы
    if request.method == "OPTIONS":
        response = JSONResponse(content={"message": "OK"})
    else:
        response = await call_next(request)
    
    # Добавляем CORS заголовки ко всем ответам
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    
    return response

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(polls.router, prefix="/api/polls", tags=["Polls"])
app.include_router(votes.router, prefix="/api/votes", tags=["Votes"])

@app.get("/")
async def root():
    return {"message": "Система студенческих опросов API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)