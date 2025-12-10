from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from fastapi_limiter import FastAPILimiter
from starlette.middleware.cors import CORSMiddleware

from src.auth.router import router as auth_router
from src.books.router import router as books_router
from src.borrows.router import router as borrows_router
from src.core.config import settings
from src.core.exceptions import global_exception_handler
from src.core.logging_config import setup_logging
from src.core.ratelimit import get_rate_limiter, init_rate_limiter
from src.users.router import router as users_router

# Setup logging
logger = setup_logging(log_level="INFO")


def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    return route.name


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    logger.info("Application startup")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: {settings.API_V1_STR}")

    # Init Rate Limiter (skip in testing environment)
    if settings.RATE_LIMIT_ENABLED:
        try:
            await init_rate_limiter()
            logger.info("Rate limiter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {e}")
    else:
        logger.info("Rate limiting disabled (testing environment)")

    yield
    # Shutdown: Clean up resources
    logger.info("Application shutdown")
    if settings.RATE_LIMIT_ENABLED:
        await FastAPILimiter.close()

    from src.core.db import engine

    engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=settings.all_cors_origins
        + ["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Set global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(books_router, prefix=settings.API_V1_STR)
app.include_router(borrows_router, prefix=settings.API_V1_STR)


@app.get("/", dependencies=[Depends(get_rate_limiter(times=60, seconds=60))])
async def root():
    """Root endpoint. Rate limited to 60 requests per minute."""
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to the API",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy"}
