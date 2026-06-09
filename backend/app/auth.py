# backend/app/auth.py
import jwt
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import get_db
from app.models import TemporaryAccessGrant
from app.schemas_api import UserClaims

logger = logging.getLogger("ksp_netra.auth")

class JurisdictionalGuard:
    def __init__(self):
        self.security = HTTPBearer()

    async def get_user_claims(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> UserClaims:
        token = credentials.credentials
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return UserClaims(
                user_id=payload.get("user_id"),
                role=payload.get("role"),
                jurisdiction=payload.get("jurisdiction"),
                ps_limit=payload.get("ps_limit")
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization token has expired.")
        except jwt.PyJWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization signature.")

    async def enforce_rls(
        self, 
        user: UserClaims, 
        resource_id: str, 
        resource_jurisdiction: str, 
        request: Request,
        db: AsyncSession
    ) -> bool:
        if user.role == "STATE_ADMIN":
            return True
            
        if user.jurisdiction.upper() == resource_jurisdiction.upper():
            return True
            
        # Standard temporary grants verification checking from PostgreSQL schemas
        stmt = select(TemporaryAccessGrant).where(
            TemporaryAccessGrant.user_id == user.user_id,
            TemporaryAccessGrant.resource_id == resource_id,
            TemporaryAccessGrant.expires_at > datetime.utcnow()
        )
        result = await db.execute(stmt)
        active_grant = result.scalar_one_or_none()
        if active_grant:
            return True
            
        # Emergency Override bypass evaluation
        override_reason = request.headers.get("X-Emergency-Override-Reason")
        active_fir = request.headers.get("X-Active-Investigation-FIR")
        
        if override_reason and active_fir:
            request.state.emergency_override = {
                "triggered": True,
                "reason": override_reason,
                "linked_fir": active_fir
            }
            return True
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied. Resource jurisdiction ({resource_jurisdiction}) mismatch."
        )

jurisdictional_guard = JurisdictionalGuard()
