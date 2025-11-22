# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routes import auth, polls, votes
from src.database.connection import create_tables
from config import settings

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    uvicorn.run(app, host="0.0.0.0", port=8000)