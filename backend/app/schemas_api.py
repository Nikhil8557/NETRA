# backend/app/schemas_api.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class UserClaims(BaseModel):
    user_id: str = Field(..., examples=["KSP-BADGE-772"])
    role: str = Field(..., examples=["STATION_OFFICER"])
    jurisdiction: str = Field(..., examples=["MANDYA"])
    ps_limit: Optional[str] = Field(None, examples=["MADDUR-PS"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AccessRequest(BaseModel):
    resource_id: str = Field(..., examples=["CASE-101"])
    duration_hours: int = Field(default=24, ge=1, le=168)

class AccessRequestResponse(BaseModel):
    request_id: str
    user_id: str
    resource_id: str
    status: str = "APPROVED"
    expires_at: datetime

class CaseDetailResponse(BaseModel):
    case_id: str
    jurisdiction: str
    title: str
    summary: str
    suspects: List[str] = Field(default_factory=list)
    sensitive_notes: str
    access_restricted: bool = False

class SearchHit(BaseModel):
    document_id: str
    title: str
    jurisdiction: str
    snippet: str
    phone: str
    address: str
    witness_name: str
    access_restricted: bool = False

class SearchResponse(BaseModel):
    query: str
    hits: List[SearchHit] = Field(default_factory=list)

class HotspotCluster(BaseModel):
    cluster_id: int
    centroid_latitude: float
    centroid_longitude: float
    radius_meters: float
    incident_count: int
    incident_ids: List[str]

class SpikeAlert(BaseModel):
    region_id: str
    calculated_z_score: float
    trigger_pulse_alert: bool
    current_count: int
    historical_mean: float
    historical_std: float
    timestamp: datetime

class MOSimilarityResult(BaseModel):
    offender_id: str
    full_name: str
    jaccard_score: float
    matching_tags: List[str]
    non_matching_tags: List[str]

class NodeRepresentation(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any]

class EdgeRepresentation(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class PathSegment(BaseModel):
    nodes: List[NodeRepresentation] = Field(default_factory=list)
    edges: List[EdgeRepresentation] = Field(default_factory=list)
