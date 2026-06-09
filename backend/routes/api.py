# backend/routes/api.py
import jwt
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from app.config import settings
from app.database import get_db
from app.auth import jurisdictional_guard, temporary_access_grants
from app.orchestrator import orchestrator
from app.models import CaseRecord, TemporaryAccessGrant
from app.schemas_api import TokenResponse, UserClaims, CaseDetailResponse, AccessRequest, AccessRequestResponse, SearchResponse

router = APIRouter(prefix="/api/v1")

@router.post("/auth/token", response_model=TokenResponse)
async def generate_sandbox_token(claims: UserClaims):
    expiry = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": claims.user_id,
        "role": claims.role,
        "jurisdiction": claims.jurisdiction.upper(),
        "ps_limit": claims.ps_limit,
        "exp": expiry
    }
    encoded = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return TokenResponse(access_token=encoded)

@router.get("/search", response_model=SearchResponse)
async def execute_search(
    q: str = Query(...), 
    credentials: HTTPAuthorizationCredentials = Depends(jurisdictional_guard.security)
):
    user = await jurisdictional_guard.get_user_claims(credentials)
    return await orchestrator.federated_search(
        query=q, 
        user_jurisdiction=user.jurisdiction, 
        is_state_admin=(user.role == "STATE_ADMIN")
    )

@router.get("/case/{case_id}", response_model=CaseDetailResponse)
async def get_case_details(
    case_id: str, 
    request: Request, 
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(jurisdictional_guard.security)
):
    user = await jurisdictional_guard.get_user_claims(credentials)
    
    stmt = select(CaseRecord).where(CaseRecord.case_id == case_id)
    result = await db.execute(stmt)
    case_data = result.scalar_one_or_none()
    
    if not case_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")

    await jurisdictional_guard.enforce_rls(
        user=user, 
        resource_id=case_id, 
        resource_jurisdiction=case_data.jurisdiction, 
        request=request,
        db=db
    )
    return await orchestrator.gather_board_data(case_id, db)

@router.post("/access-request", response_model=AccessRequestResponse)
async def submit_temporary_access_request(
    form: AccessRequest, 
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(jurisdictional_guard.security)
):
    user = await jurisdictional_guard.get_user_claims(credentials)
    expiry = datetime.utcnow() + timedelta(hours=form.duration_hours)
    
    grant = TemporaryAccessGrant(
        user_id=user.user_id,
        resource_id=form.resource_id,
        expires_at=expiry
    )
    db.add(grant)
    await db.commit()
    
    return AccessRequestResponse(
        request_id=f"GRANT-{hash((user.user_id, form.resource_id)) % 100000:05d}", 
        user_id=user.user_id, 
        resource_id=form.resource_id, 
        expires_at=expiry
    )
