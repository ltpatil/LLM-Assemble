import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Security: API token for authentication
AGGREGATOR_TOKEN = os.getenv("AGGREGATOR_TOKEN")
if not AGGREGATOR_TOKEN:
    print("ERROR: AGGREGATOR_TOKEN not set in environment variables")
    sys.exit(1)

# LLM API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# LLM Model Configuration
OPENAI_MODEL = "gpt-4-turbo"
ANTHROPIC_MODEL = "claude-3-opus-20240229"
GOOGLE_MODEL = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"

# Embedding Configuration
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
SIMILARITY_THRESHOLD = 0.60

# Scoring Weights - adjust these to tune the aggregation algorithm
WEIGHT_EVIDENCE = 0.5
WEIGHT_CONSENSUS = 0.3
WEIGHT_CLARITY = 0.2

# Wikipedia Settings
WIKIPEDIA_LANGUAGE = 'en'
WIKIPEDIA_SUGGESTIONS = 3
WIKIPEDIA_SENTENCES = 5

# General Settings
MIN_CLAIMS_FOR_EVIDENCE = 1
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# CORS Settings
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")