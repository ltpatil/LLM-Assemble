import os
import sys
import json
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from sqlmodel import Session, select

import config
from app.providers.llm_providers import LLMProviders
from app.analysis.evaluator import Evaluator
from app.schemas import AskRequest, AggregateResponse
from app.database import create_db_and_tables, get_session
from app.models import QueryHistory

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    create_db_and_tables()
    logger.info("Pre-loading ML models...")
    app.state.llm_provider = LLMProviders()
    app.state.evaluator = Evaluator()
    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")

app = FastAPI(
    title="LLMASSEMBLE",
    description="Evidence-based multi-agent LLM response aggregation system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header_auth = APIKeyHeader(name="Authorization", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header_auth)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing"
        )
    if not api_key.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )
    
    token = api_key.split(" ")[1]
    if token != config.AGGREGATOR_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return token

@app.get("/", tags=["Health"])
async def read_root():
    return {"status": "LLMASSEMBLE API is running"}

@app.post("/api/aggregate", 
          response_model=AggregateResponse, 
          tags=["Aggregation"],
          dependencies=[Depends(verify_api_key)])
async def aggregate_and_evaluate(
    request: AskRequest, 
    session: Session = Depends(get_session)
) -> AggregateResponse:
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    logger.info(f"New request: {request.prompt[:50]}...")

    llm_responses = await app.state.llm_provider.get_all_llm_responses(request.prompt)
    
    if not llm_responses:
        raise HTTPException(status_code=503, detail="No valid responses from LLM providers")

    evaluation_results = await app.state.evaluator.evaluate_responses(request.prompt, llm_responses)
    
    winner_data = evaluation_results.get("winner")
    if winner_data:
        try:
            candidates_json = json.dumps(evaluation_results.get("all_candidates", []))
            snippets_json = json.dumps(winner_data.get("evidence_snippets", []))

            history_record = QueryHistory(
                prompt=request.prompt,
                winning_provider=winner_data["response"]["provider_name"],
                winning_text=winner_data["response"]["text"],
                final_score=winner_data["final_score"],
                evidence_score=winner_data["evidence_score"],
                consensus_score=winner_data["consensus_score"],
                sentiment_score=winner_data["sentiment_score"],
                evidence_snippets_json=snippets_json,
                all_candidates_json=candidates_json
            )
            session.add(history_record)
            session.commit()
            session.refresh(history_record)
            logger.info(f"Saved query to history: ID {history_record.id}")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")

    evaluation_results['prompt'] = request.prompt
    return AggregateResponse(**evaluation_results)

@app.get("/api/history", response_model=List[QueryHistory], tags=["History"])
def read_history(
    offset: int = 0, 
    limit: int = 10, 
    session: Session = Depends(get_session)
):
    statement = select(QueryHistory).order_by(QueryHistory.timestamp.desc()).offset(offset).limit(limit)
    results = session.exec(statement).all()
    return results

@app.delete("/api/history/{item_id}", tags=["History"])
def delete_history_item(
    item_id: int,
    session: Session = Depends(get_session),
    api_key: str = Depends(verify_api_key)
):
    history_item = session.get(QueryHistory, item_id)
    if not history_item:
        raise HTTPException(status_code=404, detail="History item not found")
    
    session.delete(history_item)
    session.commit()
    return {"ok": True}

if __name__ == "__main__":
    logger.info("Starting LLMASSEMBLE server at http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, app_dir=os.path.dirname(__file__))