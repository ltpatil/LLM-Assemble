from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AskRequest(BaseModel):
    """Request model for the aggregation endpoint."""
    prompt: str

class LLMProviderResponse(BaseModel):
    """A single LLM's response."""
    provider_name: str
    text: str
    model_name: str

class ScoredCandidate(BaseModel):
    """One evaluated candidate with scores."""
    candidate_id: int
    final_score: float
    evidence_score: float
    consensus_score: float
    sentiment_score: float
    response: LLMProviderResponse
    evidence_snippets: List[str]

class AggregateResponse(BaseModel):
    """The full API response with winner and all candidates."""
    winner: Optional[ScoredCandidate]
    explainability: str
    all_candidates: List[ScoredCandidate]
    prompt: str