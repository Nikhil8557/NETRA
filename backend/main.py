# backend/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware import ImmutableAuditLoggerMiddleware
from app.database import db_manager
from routes.api import router

def create_app() -> FastAPI:
    app = FastAPI(title="KSP-NETRA Gateway Engine", version="4.0.0")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Emergency-Override-Reason", "X-Active-Investigation-FIR"]
    )
    app.add_middleware(ImmutableAuditLoggerMiddleware)
    app.include_router(router)
    return app

app = create_app()

@app.on_event("startup")
async def startup_event():
    # Establish connection pooling to Neo4j and Elasticsearch
    db_manager.initialize_connections()

@app.on_event("shutdown")
async def shutdown_event():
    await db_manager.close_connections()

if __name__ == "__main__":
    uvicorn.run("main.py:app", host="127.0.0.1", port=8000, reload=True)
