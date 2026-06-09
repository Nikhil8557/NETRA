# backend/bootstrap_data.py
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base
from app.models import CaseRecord, SuspectRecord
from app.config import settings

async def bootstrap():
    engine = create_async_engine(settings.DATABASE_URL)
    
    # 1. Generate tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession)
    
    async with session_maker() as s:
        # 2. Seed Cases
        c1 = CaseRecord(case_id="CASE-101", jurisdiction="MANDYA", title="Mandya Transit Theft", summary="Accused Shivaraj B M was caught transiting through border corridors with stolen property.", sensitive_notes="Unredacted data logs indicate direct associations to Mandya station coordinates.")
        c2 = CaseRecord(case_id="CASE-202", jurisdiction="BANGALORE", title="Corporate Phishing campaign", summary="Investigator logs trace phishing infrastructure to active servers.", sensitive_notes="Classified notes identify active associations to server networks outside state limits.")
        s.add_all([c1, c2])
        await s.commit()
    await engine.dispose()
    print("PostgreSQL tables successfully built and seeded.")

asyncio.run(bootstrap())
