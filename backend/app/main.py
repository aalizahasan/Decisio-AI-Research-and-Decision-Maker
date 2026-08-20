import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import router
from app.db.database import init_db

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API foundation for AI Research & Decision Platform",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup():
    """
    Initializes database tables on application startup.
    """
    init_db()


# Enable CORS so frontend (e.g. http://localhost:5173) can make requests to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount application API routes
app.include_router(router)



@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs_url": "/docs",
        "health_check": "/health",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
