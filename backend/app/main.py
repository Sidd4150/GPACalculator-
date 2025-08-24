"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api.endpoints import router, limiter
from app.config import get_settings
from app.utils.logger import setup_logger

logger = setup_logger("main")
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    logger.info("GPA Calculator API starting up")
    yield
    # Shutdown
    logger.info("GPA Calculator API shutting down")


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Add rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include API routes with versioning
app.include_router(router, prefix="/api/v1")


# Application startup/shutdown events handled by lifespan context manager


if __name__ == "__main__":
    import uvicorn
    import os

    # Use PORT from environment if set (production), otherwise use config default
    port = int(os.getenv("PORT", str(settings.port)))
    uvicorn.run(app, host=settings.host, port=port)
