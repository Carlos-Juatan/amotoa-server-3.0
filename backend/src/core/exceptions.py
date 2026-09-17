from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details

class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)

class RateLimitError(AppException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message=message, status_code=429)

class AccountNotActiveError(AppException):
    def __init__(self, message: str = "Invalid or missing active account"):
        super().__init__(message=message, status_code=401)

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.message, "details": exc.details},
        )
        
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail},
        )
