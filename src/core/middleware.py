from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from core.error_code import ErrorCode
from entity.constants import Constants

SKIP_VERIFICATION_ROUTERS = set()

def skip_client_verification_for_router(router):
    router.skip_client_verification = True

    if hasattr(router, 'prefix') and router.prefix:
        SKIP_VERIFICATION_ROUTERS.add(router.prefix)
    
    return router

class ClientVerificationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path == "/health":
            return await call_next(request)
        
        if self._is_skip_verification_router(path):
            return await call_next(request)
        
        # 执行客户端验证
        client_type = request.headers.get(Constants.HEADERS_CLIENT_TYPE)
        if not client_type or client_type.lower() != Constants.CLIENT_TYPE:
            logger.warning(
                f"Client type validation failed, path: {path}, "
                f"client_type: {client_type or 'missing'}, "
                f"ip: {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "code": ErrorCode.CLIENT_TYPE_INVALID.id,
                    "data": None,
                    "message": ErrorCode.CLIENT_TYPE_INVALID.msg
                }
            )
        
        return await call_next(request)
    
    def _is_skip_verification_router(self, path: str) -> bool:
        for router_prefix in SKIP_VERIFICATION_ROUTERS:
            full_prefix = f"/app/api{router_prefix}"
            if path.startswith(full_prefix):
                return True
        
        return False