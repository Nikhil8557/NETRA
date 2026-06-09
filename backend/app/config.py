# backend/app/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class PipelineSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )
    
    # Message Broker
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092")
    
    # National VAHAN API
    VAHAN_API_ENDPOINT: str = Field(default="https://vahan.parivahan.gov.in/api/v1/vehicle")
    VAHAN_CLIENT_ID: str = Field(default="KSP_NETRA_SECURE_CLIENT")
    VAHAN_API_SECRET: str = Field(default="super_secret_sha256_signing_key_generated_by_morth")
    
    # Local Self-Hosted Translation Service (e.g., IndicTrans2 API Server)
    INDIC_TRANSLATOR_ENDPOINT: str = Field(default="http://localhost:5001/translate")
    
    # NLP Configuration
    SPACY_MODEL_PATH: str = Field(default="en_core_web_sm")
    
    # Databases
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:securepassword@localhost:5432/ksp_netra")
    NEO4J_URI: str = Field(default="bolt://localhost:7687")
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="password")
    ELASTICSEARCH_URL: str = Field(default="http://localhost:9200")
    
    # JWT Authentication
    JWT_SECRET: str = Field(default="ksp-netra-secure-jwt-secret-key-2026-state-level-encryption")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    
    # Thresholds
    AUTO_MERGE_THRESHOLD: float = Field(default=0.85)
    MANUAL_REVIEW_THRESHOLD: float = Field(default=0.60)

settings = PipelineSettings()
