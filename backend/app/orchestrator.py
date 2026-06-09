# backend/app/orchestrator.py
import asyncio
import logging
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import db_manager
from app.models import CaseRecord
from app.schemas_api import CaseDetailResponse, SearchHit, SearchResponse

logger = logging.getLogger("ksp_netra.orchestrator")

class BoardDataOrchestrator:
    def __init__(self):
        self.db_manager = db_manager

    async def gather_board_data(self, case_id: str, db: AsyncSession) -> CaseDetailResponse:
        """
        Gathers relational, spatial, and analytical properties for standard UI rendering.
        """
        # 1. Fetch SQL case metadata
        stmt = select(CaseRecord).where(CaseRecord.case_id == case_id)
        result = await db.execute(stmt)
        case_meta = result.scalar_one_or_none()
        
        if not case_meta:
            raise KeyError(f"Case details for ID '{case_id}' could not be located.")
            
        # 2. Concurrently fetch Neo4j relationship targets
        suspects_list = []
        if self.db_manager.neo4j_driver:
            try:
                async with self.db_manager.neo4j_driver.session() as session:
                    query = """
                    MATCH (c:Case {id: $case_id})-[r:ASSOCIATED_SUSPECT]->(s:Suspect)
                    RETURN s.guid AS guid
                    """
                    records = await session.run(query, case_id=case_id)
                    suspects_list = [row["guid"] async for row in records]
            except Exception as e:
                logger.error(f"Failed to fetch Neo4j links for {case_id}: {e}")
                
        return CaseDetailResponse(
            case_id=case_id,
            jurisdiction=case_meta.jurisdiction,
            title=case_meta.title,
            summary=case_meta.summary,
            suspects=suspects_list,
            sensitive_notes=case_meta.sensitive_notes
        )

    async def federated_search(self, query: str, user_jurisdiction: str, is_state_admin: bool) -> SearchResponse:
        """
        Executes full-text multi-field search against Elasticsearch nodes, sanitizing PII for out-of-jurisdiction hits.
        """
        if not self.db_manager.es_client:
            logger.error("Federated Search aborted: Elasticsearch instance is offline.")
            return SearchResponse(query=query, hits=[])
            
        es_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "snippet", "address", "witness_name"]
                }
            }
        }
        
        try:
            response = await self.db_manager.es_client.search(index="netra_documents", body=es_query)
            hits = []
            
            for hit in response["hits"]["hits"]:
                src = hit["_source"]
                is_authorized = is_state_admin or (src["jurisdiction"].upper() == user_jurisdiction.upper())
                
                if not is_authorized:
                    hits.append(SearchHit(
                        document_id=hit["_id"],
                        title=src["title"],
                        jurisdiction=src["jurisdiction"],
                        snippet=src["snippet"],
                        phone="+91 ******" + src["phone"][-4:] if src.get("phone") else "",
                        address="REDACTED [CROSS-JURISDICTIONAL POLICY ENFORCED]",
                        witness_name=src["witness_name"][0] + "*********" if src.get("witness_name") else "",
                        access_restricted=True
                    ))
                else:
                    hits.append(SearchHit(
                        document_id=hit["_id"],
                        title=src["title"],
                        jurisdiction=src["jurisdiction"],
                        snippet=src["snippet"],
                        phone=src.get("phone", ""),
                        address=src.get("address", ""),
                        witness_name=src.get("witness_name", ""),
                        access_restricted=False
                    ))
            return SearchResponse(query=query, hits=hits)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return SearchResponse(query=query, hits=[])

orchestrator = BoardDataOrchestrator()
