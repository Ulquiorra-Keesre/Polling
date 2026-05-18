from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import traceback
import logging
from src.exceptions import ResourceGoneException

from src.api.routes import auth, polls, votes, files, seo, weather
from src.database.connection import create_tables


logger = logging.getLogger("poll_system")


@asynccontextmanager
async def lifespan(app: FastAPI):

    await create_tables()
    print("Database tables created !")
    yield

    print("Application shutdown !!!")


app = FastAPI(
    title="Система студенческих опросов",
    description="API для системы анонимных студенческих опросов",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(ResponseValidationError)
async def response_validation_handler(request: Request, exc: ResponseValidationError):
    """Обработчик ошибок валидации ответа"""
    print(f"ResponseValidationError: {exc}")
    print(traceback.format_exc())

    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "error": "Ошибка валидации ответа сервера",
            "details": str(exc),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации Pydantic/FastAPI"""

    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")

    errors = []
    for error in exc.errors():
        loc = " → ".join(str(l) for l in error["loc"] if l != "body")
        errors.append(
            {"field": loc or "body", "message": error["msg"], "type": error["type"]}
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Ошибка валидации данных",
            "details": errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик для НЕОЖИДАННЫХ исключений (серверные ошибки)"""

    logger.error(
        f"Unhandled exception on {request.url.path}",
        exc_info=True,
        extra={
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent"),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Внутренняя ошибка сервера",
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Обработчик стандартных HTTP-ошибок (404, 403, 422, и т.д.)"""

    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} on {request.url.path}", exc_info=False)
    elif exc.status_code >= 400:
        logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")

    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": "Страница не найдена",
                "path": str(request.url.path),
                "suggestions": ["/dashboard", "/polls"],
            },
            headers={"Cache-Control": "public, max-age=300"},
        )
    return JSONResponse(
        status_code=exc.status_code, content={"success": False, "error": exc.detail}
    )


@app.exception_handler(ResourceGoneException)
async def gone_exception_handler(request: Request, exc: ResourceGoneException):
    """Обработчик для навсегда удалённых ресурсов (410 Gone)"""

    logger.info(f"Resource gone: {request.url.path}")

    return JSONResponse(
        status_code=410,
        content={"success": False, "error": "Ресурс был удалён", "message": exc.detail},
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):

    if request.method == "OPTIONS":
        response = JSONResponse(content={"message": "OK"})
    else:
        response = await call_next(request)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"

    return response


app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(polls.router, prefix="/api/polls", tags=["Polls"])
app.include_router(votes.router, prefix="/api/votes", tags=["Votes"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(seo.router, prefix="/api/seo", tags=["SEO"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])


@app.get("/")
async def root():
    return {"message": "Система студенческих опросов API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
