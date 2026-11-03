"""Standard error body for every API error:
   { "error": { "code": "STRING_CODE", "message": "Readable message" } }   (SAD 4.4)
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("hap")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def not_found(what: str = "Resource") -> ApiError:
    return ApiError(404, "NOT_FOUND", f"{what} not found.")


def forbidden(message: str = "You are not allowed to do this.") -> ApiError:
    return ApiError(403, "FORBIDDEN", message)


def conflict(code: str, message: str) -> ApiError:
    return ApiError(409, code, message)


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status, content=body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(p) for p in first.get("loc", []) if p not in ("body", "query", "path"))
        msg = first.get("msg", "Invalid input")
        return JSONResponse(status_code=422, content=body("VALIDATION_ERROR", f"{field}: {msg}" if field else msg))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        codes = {401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
        return JSONResponse(status_code=exc.status_code,
                            content=body(codes.get(exc.status_code, "ERROR"), str(exc.detail)))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception):
        log.exception("Unhandled error")  # never log request bodies (patient data)
        return JSONResponse(status_code=500, content=body("INTERNAL_ERROR", "Something went wrong. Please try again."))
