# backend/app/models.py
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON, Text, ForeignKey, Integer
from app.database import Base

class CaseRecord(Base):
    __tablename__ = "cases"

    case_id = Column(String(50), primary_key=True, index=True)
    jurisdiction = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    sensitive_notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SuspectRecord(Base):
    __tablename__ = "suspects"

    ksp_guid = Column(String(100), primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    father_name = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True, index=True)
    aliases = Column(JSON, default=list)

class TemporaryAccessGrant(Base):
    __tablename__ = "temporary_access_grants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(100), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)

class AuditLedgerEntry(Base):
    __tablename__ = "immutable_audit_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String(100), nullable=False, index=True)
    client_ip = Column(String(45), nullable=False)
    http_method = Column(String(10), nullable=False)
    endpoint_path = Column(Text, nullable=False)
    response_status = Column(Integer, nullable=False)
    latency_seconds = Column(Float, nullable=False)
    emergency_override_triggered = Column(Boolean, default=False, nullable=False)
    override_justification = Column(Text, nullable=True)
    linked_investigation_fir = Column(String(100), nullable=True)
