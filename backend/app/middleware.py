# backend/app/middleware.py
import logging
import jwt
from datetime import datetime
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.database import db_manager
from app.models import AuditLedgerEntry

logger = logging.getLogger("ksp_netra.middleware")

class ImmutableAuditLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.emergency_override = {"triggered": False, "reason": None, "linked_fir": None}
        start_time = datetime.utcnow()
        auth_header, user_id = request.headers.get("Authorization"), "ANONYMOUS"
        
        if auth_header and auth_header.startswith("Bearer "):
            try:
                payload = jwt.decode(auth_header.split(" ")[1], options={"verify_signature": False})
                user_id = payload.get("user_id", "UNKNOWN")
            except Exception:
                user_id = "MALFORMED_TOKEN"

        response = await call_next(request)
        latency = (datetime.utcnow() - start_time).total_seconds()
        override_data = getattr(request.state, "emergency_override", {})
        
        # Asynchronously commit write to our append-only database using database pool context
        async with db_manager.async_session_maker() as session:
            try:
                audit_entry = AuditLedgerEntry(
                    timestamp=datetime.utcnow(),
                    user_id=user_id,
                    client_ip=request.client.host if request.client else "127.0.0.1",
                    http_method=request.method,
                    endpoint_path=request.url.path,
                    response_status=response.status_code,
                    latency_seconds=round(latency, 4),
                    emergency_override_triggered=override_data.get("triggered", False),
                    override_justification=override_data.get("reason"),
                    linked_investigation_fir=override_data.get("linked_fir")
                )
                session.add(audit_entry)
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to record transaction audit: {e}")
                await session.rollback()

        if override_data.get("triggered"):
            logger.warning(f"[AUDIT BYPASS WARNING] Emergency Override executed by {user_id} on {request.url.path}")
        else:
            logger.info(f"[AUDIT LOG] {request.method} {request.url.path} ({response.status_code}) User: {user_id}")
            
        return response
