"""HTTP exception middleware helpers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"success": False, "detail": str(exc)})

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(_: Request, exc: RuntimeError):
        logger.error("Runtime error: %s", exc)
        return JSONResponse(status_code=500, content={"success": False, "detail": str(exc)})

    @app.exception_handler(Exception)
    async def generic_handler(_: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": "Internal server error"},
        )
