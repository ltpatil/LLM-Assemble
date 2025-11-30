import nltk
from typing import List

class ClaimExtractor:
    def __init__(self):
        pass

    def extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text using sentence tokenization."""
        if not text:
            return []

        sentences = nltk.sent_tokenize(text)

        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            # Filter out questions and very short sentences
            if (len(sentence.split()) > 4 and 
                sentence.endswith('.') and 
                not sentence.lower().startswith(('what', 'why', 'how', 'when', 'where', 'who', 'is', 'are', 'do', 'can'))):
                claims.append(sentence)
        
        # Fallback to all sentences if no claims found
        if not claims and sentences:
            return [s.strip() for s in sentences if len(s.strip().split()) > 3]

        return claims