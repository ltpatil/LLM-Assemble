import os
import sys
# Add the project root to sys.path so 'app' and 'config' can be found when run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from transformers import pipeline, logging as transformers_logging
from typing import Dict, Any, List
import config

# Suppress unnecessary warnings from transformers
transformers_logging.set_verbosity_error()

class SentimentAnalyzer:
    _pipeline = None # Class variable to hold the loaded pipeline

    @classmethod
    def _load_pipeline(cls):
        """Loads the sentiment analysis model if it hasn't been loaded yet."""
        if cls._pipeline is None:
            if config.DEBUG_MODE:
                print("[SENTIMENT DEBUG] Initializing SentimentAnalyzer pipeline...")
            # Use a pre-trained sentiment analysis model
            cls._pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            if config.DEBUG_MODE:
                print("[SENTIMENT DEBUG] SentimentAnalyzer pipeline initialized.")
    
    @classmethod
    def analyze_sentiment(cls, text: str) -> Dict[str, Any]:
        """
        Analyzes the sentiment of a given text.
        Returns:
            A dictionary with 'label' ('POSITIVE', 'NEGATIVE') and 'score' (0.0 to 1.0).
        """
        cls._load_pipeline() # Ensure the pipeline is loaded

        if not text or not text.strip():
            return {"label": "NEUTRAL", "score": 0.5} # Handle empty/whitespace text
        
        try:
            # Truncate text to avoid warnings/errors with very long inputs
            truncated_text = text[:512] 
            result = cls._pipeline(truncated_text)[0]
            result['score'] = float(result['score'])
            if config.DEBUG_MODE:
                print(f"[SENTIMENT DEBUG] Analyzed sentiment for '{text[:50]}...': {result['label']} (Score: {result['score']:.3f})")
            return result
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"[SENTIMENT DEBUG] Error during sentiment analysis for '{text[:50]}...': {e}")
            return {"label": "ERROR", "score": 0.0}

# Example usage (for testing)
if __name__ == "__main__":
    print("Running SentimentAnalyzer test...")
    if 'config' not in sys.modules:
        import config

    test_texts = [
        "I love this product! It's amazing.",
        "This is a terrible experience, I'm very disappointed.",
        "The cat sat on the mat.", # Should be fairly neutral, but model must pick one
        "" # Empty text
    ]

    for i, text in enumerate(test_texts):
        print(f"\n--- Analyzing text {i+1}: '{text[:70]}...' ---")
        sentiment_result = SentimentAnalyzer.analyze_sentiment(text)
        print(f"Sentiment: {sentiment_result['label']}, Score: {sentiment_result['score']:.3f}")