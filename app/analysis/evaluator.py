import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import numpy as np
from typing import List, Dict, Any
from scipy.spatial.distance import cosine

from app.utils.embeddings import Embeddings
from app.providers.llm_providers import LLMResponse
from app.analysis.evidence import EvidenceRetriever
from app.analysis.sentiment import SentimentAnalyzer
import config

logger = logging.getLogger(__name__)

class Evaluator:
    def __init__(self):
        self.embeddings_service = Embeddings()
        self.evidence_retriever = EvidenceRetriever()
        self.sentiment_analyzer = SentimentAnalyzer()
        logger.info("Evaluator initialized")

    def _calculate_consensus_score(self, target_embedding: np.ndarray, all_embeddings: List[np.ndarray]) -> float:
        """Calculate how well this response agrees with others."""
        if len(all_embeddings) < 2:
            return 0.0

        similarities = []
        for emb in all_embeddings:
            if emb.shape[0] > 0 and target_embedding.shape[0] > 0 and not np.array_equal(emb, target_embedding):
                similarity = 1 - cosine(target_embedding, emb)
                similarities.append(similarity)
        
        if not similarities:
            return 0.0

        return float(np.mean(similarities))

    async def evaluate_responses(self, prompt: str, llm_responses: List[LLMResponse]) -> Dict[str, Any]:
        if not llm_responses:
             return {"winner": None, "explainability": "No responses to evaluate", "all_candidates": []}

        response_texts = [resp.text for resp in llm_responses]
        response_embeddings_raw = self.embeddings_service.get_sentence_embeddings(response_texts)
        all_embeddings = [np.array(e) for e in response_embeddings_raw if e]

        scored_candidates = []
        for i, response in enumerate(llm_responses):
            logger.debug(f"Scoring candidate {i+1}: {response.provider_name}")
            
            # CRITICAL FIX: Check evidence for the RESPONSE, not the prompt
            evidence_snippets, evidence_score = self.evidence_retriever.get_evidence_and_score(response.text)
            
            # Analyze sentiment/clarity
            sentiment_result = self.sentiment_analyzer.analyze_sentiment(response.text)
            if sentiment_result['label'] == 'POSITIVE':
                clarity_score = sentiment_result['score']
            elif sentiment_result['label'] == 'NEGATIVE':
                clarity_score = 1.0 - sentiment_result['score']
            else:
                clarity_score = 0.5

            # Calculate consensus
            target_embedding = all_embeddings[i]
            consensus_score = self._calculate_consensus_score(target_embedding, all_embeddings)

            # Final weighted score
            final_score = (
                evidence_score * config.WEIGHT_EVIDENCE +
                consensus_score * config.WEIGHT_CONSENSUS +
                clarity_score * config.WEIGHT_CLARITY
            )

            logger.debug(f"Scores - Evidence: {evidence_score:.2f}, Consensus: {consensus_score:.2f}, Clarity: {clarity_score:.2f}, Final: {final_score:.2f}")

            scored_candidates.append({
                "candidate_id": i,
                "final_score": float(final_score),
                "evidence_score": float(evidence_score),
                "consensus_score": float(consensus_score),
                "sentiment_score": float(clarity_score),
                "response": response.to_dict(),
                "evidence_snippets": evidence_snippets,
            })

        if not scored_candidates:
            return {"winner": None, "explainability": "No candidates could be scored", "all_candidates": []}

        winner = sorted(scored_candidates, key=lambda x: x['final_score'], reverse=True)[0]
        
        explanation = (
            f"Selected {winner['response']['provider_name']} "
            f"(score: {winner['final_score']:.2f}). "
            f"Evidence: {winner['evidence_score']:.2f}, "
            f"Consensus: {winner['consensus_score']:.2f}, "
            f"Clarity: {winner['sentiment_score']:.2f}"
        )

        return {
            "winner": winner,
            "explainability": explanation,
            "all_candidates": scored_candidates
        }