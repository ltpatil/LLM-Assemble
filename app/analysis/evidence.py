import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import wikipediaapi
import wikipedia
from typing import List, Tuple, Optional
import numpy as np
from scipy.spatial.distance import cosine

from app.utils.embeddings import Embeddings
import config

logger = logging.getLogger(__name__)

class EvidenceRetriever:
    def __init__(self):
        self.wiki_api = wikipediaapi.Wikipedia(
            language=config.WIKIPEDIA_LANGUAGE,
            user_agent="LLMASSEMBLE/1.0"
        )
        wikipedia.set_lang(config.WIKIPEDIA_LANGUAGE)
        self.embeddings_service = Embeddings()

    def _get_page_content(self, title: str) -> Optional[str]:
        page = self.wiki_api.page(title)
        if page.exists():
            sentences = page.summary.split('.')
            content = '.'.join(sentences[:config.WIKIPEDIA_SENTENCES]) + '.' if sentences else ''
            logger.debug(f"Fetched Wikipedia page '{title}'")
            return content
        return None

    def _search_wikipedia(self, query: str) -> List[str]:
        try:
            search_titles = wikipedia.search(query, results=config.WIKIPEDIA_SUGGESTIONS)
            logger.debug(f"Wikipedia search for '{query}': {len(search_titles)} results")
            
            snippets = []
            for title in search_titles:
                content = self._get_page_content(title)
                if content:
                    snippets.append(content)
            
            return snippets
        except wikipedia.exceptions.PageError:
            logger.debug(f"No Wikipedia page found for '{query}'")
            return []
        except wikipedia.exceptions.DisambiguationError as e:
            if e.options:
                content = self._get_page_content(e.options[0])
                return [content] if content else []
            return []
        except Exception as e:
            logger.warning(f"Wikipedia search error: {e}")
            return []

    def get_evidence_and_score(self, claim: str) -> Tuple[List[str], float]:
        if not claim:
            return [], 0.0

        evidence_snippets = self._search_wikipedia(claim)
        
        if not evidence_snippets:
            return [], 0.0

        claim_embedding = self.embeddings_service.get_embedding(claim)
        if not claim_embedding:
            return [], 0.0

        evidence_embeddings = self.embeddings_service.get_sentence_embeddings(evidence_snippets)
        
        supported_snippets = []
        similarity_scores = []

        for i, snippet_embedding in enumerate(evidence_embeddings):
            if snippet_embedding:
                similarity = 1 - cosine(claim_embedding, snippet_embedding)
                logger.debug(f"Snippet similarity: {similarity:.2f}")
                
                if similarity >= config.SIMILARITY_THRESHOLD:
                    supported_snippets.append(evidence_snippets[i])
                    similarity_scores.append(similarity)
        
        if not similarity_scores:
            return [], 0.0

        support_score = np.mean(similarity_scores)
        return supported_snippets, float(support_score)