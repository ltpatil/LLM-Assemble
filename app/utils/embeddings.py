import os
import sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sentence_transformers import SentenceTransformer
from typing import List
import config

logger = logging.getLogger(__name__)

class Embeddings:
    _model = None

    @classmethod
    def _load_model(cls):
        if cls._model is None:
            logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL_NAME}")
            os.environ["OMP_NUM_THREADS"] = "1"
            cls._model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
            logger.info("Embedding model loaded")

    @classmethod
    def get_sentence_embeddings(cls, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        cls._load_model()
        embeddings = cls._model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    @classmethod
    def get_embedding(cls, text: str) -> List[float]:
        if not text:
            return []
        
        cls._load_model()
        embedding = cls._model.encode(text, convert_to_tensor=False)
        return embedding.tolist()