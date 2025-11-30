from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class QueryHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    prompt: str
    
    # Winner Details
    winning_provider: str
    winning_text: str
    
    # Scores
    final_score: float
    evidence_score: float
    consensus_score: float
    sentiment_score: float
    
    # Detailed Data (Stored as JSON)
    evidence_snippets_json: str 
    all_candidates_json: str