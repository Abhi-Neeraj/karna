"""FastAPI application composition for the KARNA backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import app.models.correction  # Registers correction metadata before initialization.
import app.models.fix_statistics  # Registers fix-statistics metadata before initialization.
import app.models.incident  # Registers incident metadata before initialization.
import app.models.memory_record  # Registers memory metadata before initialization.
import app.models.outcome  # Registers outcome metadata before initialization.
from app.api.v1.routers import (
    analytics,
    health,
    incidents,
    learning,
    memory_inspector,
    recommendations,
)
from app.core.config import settings
from app.core.database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize database metadata and log application lifecycle events.

    Yields:
        Control to FastAPI while the KARNA application is running.
    """
    logger.info("Starting %s API version %s", settings.app_name, settings.app_version)
    init_db()
    yield
    logger.info("Stopping %s API", settings.app_name)


app = FastAPI(
    title="KARNA API",
    version="1.0.0",
    description="Memory-centric incident response and learning API.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(learning.router, prefix="/api/v1")
app.include_router(memory_inspector.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    """Return request-validation failures in the common JSON error envelope.

    Args:
        exception: FastAPI/Pydantic validation failure details.

    Returns:
        A 422 response containing structured field errors.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed.",
                "details": exception.errors(),
            }
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exception: ValueError) -> JSONResponse:
    """Map invalid application inputs to a consistent client-error response.

    Args:
        exception: Value error raised by a service, provider, or repository.

    Returns:
        A 400 response with the invalid-operation explanation.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "invalid_operation",
                "message": str(exception),
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    _: Request,
    exception: HTTPException,
) -> JSONResponse:
    """Normalize explicitly raised HTTP exceptions into the common envelope.

    Args:
        exception: HTTP exception raised during request handling.

    Returns:
        A response retaining the requested status code and safe detail.
    """
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "error": {
                "code": "http_error",
                "message": str(exception.detail),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exception: Exception) -> JSONResponse:
    """Log unexpected failures and return a safe internal-error response.

    Args:
        exception: Unexpected exception raised while handling a request.

    Returns:
        A consistent 500 response without exposing internal details.
    """
    logger.exception("Unhandled KARNA API exception", exc_info=exception)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected server error occurred.",
            }
        },
    )
