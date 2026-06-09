# backend/app/database.py
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from elasticsearch import AsyncElasticsearch
from neo4j import AsyncGraphDatabase
from app.config import settings

logger = logging.getLogger("ksp_netra.database")

# Declarative base for SQLAlchemy
Base = declarative_base()

class DatabaseManager:
    def __init__(self):
        # 1. PostgreSQL Engine Setup
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=20,
            max_overflow=10,
            pool_recycle=3600,
            echo=False
        )
        self.async_session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # 2. Neo4j Driver Setup
        self.neo4j_driver = None
        
        # 3. Elasticsearch Client Setup
        self.es_client = None

    def initialize_connections(self):
        # Initialize Neo4j Pool
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            logger.info("Connection pool to Neo4j Graph DB established.")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connection pool: {e}")
            self.neo4j_driver = None

        # Initialize Elasticsearch Pool
        try:
            self.es_client = AsyncElasticsearch([settings.ELASTICSEARCH_URL])
            logger.info("Elasticsearch asynchronous driver pool initialized.")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch instance: {e}")
            self.es_client = None

    async def close_connections(self):
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        if self.es_client:
            await self.es_client.close()
        await self.engine.dispose()
        logger.info("All downstream database pools safely closed.")

db_manager = DatabaseManager()

# FastAPI dependency generator for PostgreSQL database sessions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db_manager.async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
