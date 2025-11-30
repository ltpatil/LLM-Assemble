# LLMASSEMBLE: Multi-Agent LLM Response Aggregator

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)

**LLMASSEMBLE** is a robust system that tackles LLM hallucination by querying multiple AI models, verifying their responses against Wikipedia, and selecting the most reliable answer using a weighted scoring algorithm.

## Key Features

* **Multi-Agent Orchestration** - Queries multiple LLMs (Google Gemini, Llama 3 via Groq) in parallel
* **Evidence Verification** - Validates responses against Wikipedia using semantic similarity
* **Intelligent Scoring** - Ranks answers based on evidence support, consensus, and clarity
* **Modern UI** - Clean React + Chakra UI dashboard with query history
* **Persistent Storage** - SQLite database for audit trail and review

## Tech Stack

* **Backend:** Python 3.11, FastAPI, SQLModel, Uvicorn
* **AI/ML:** Google Generative AI, Groq API, HuggingFace Transformers, Sentence-Transformers, NLTK
* **Frontend:** React, Vite, Chakra UI, Axios

## Project Structure

```
llm_Assemble/
├── app/                    # Backend application code
│   ├── analysis/           # Evaluation & evidence logic
│   ├── providers/          # LLM API integrations
│   ├── utils/              # Helper functions (embeddings)
│   ├── main.py             # FastAPI entry point
│   ├── models.py           # Database models
│   └── schemas.py          # Pydantic schemas
├── frontend/               # React frontend
│   ├── src/                # Source code
│   └── public/             # Static assets
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
└── history.db              # SQLite database (generated)
```

## Quick Start

### Backend Setup

```bash
cd llm_Assemble

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run server
python app/main.py
```

Server runs at http://127.0.0.1:8000

### Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

Dashboard opens at http://localhost:5173

### Configuration

Create a `.env` file in the project root:

```bash
# Required
AGGREGATOR_TOKEN="your-secret-token-here"
GOOGLE_API_KEY="your-google-api-key"
GROQ_API_KEY="your-groq-api-key"

# Optional
OPENAI_API_KEY="your-openai-key"
ANTHROPIC_API_KEY="your-anthropic-key"

# Settings
DEBUG_MODE=False
ALLOWED_ORIGINS="http://localhost:5173"
```

Create `frontend/.env`:

```bash
VITE_API_TOKEN="your-secret-token-here"
```

## How It Works

1. User submits a question via the React frontend
2. Backend queries multiple LLM providers concurrently
3. Each response is evaluated on three metrics:
   - **Evidence Score** - Wikipedia verification via semantic similarity
   - **Consensus Score** - Agreement with other LLMs using embeddings
   - **Clarity Score** - Response quality and coherence
4. Weighted scores determine the winning answer
5. Results saved to SQLite for history tracking

## Architecture

```
User Query → FastAPI Backend → LLM Providers (async)
                ↓
         Evaluator Engine
                ↓
    ┌───────────┼───────────┐
Evidence    Consensus    Clarity
Retrieval   Analysis     Check
    └───────────┼───────────┘
                ↓
         Weighted Scoring
                ↓
    Database + Response to Frontend
```

## Scoring Algorithm

```python
final_score = (
    evidence_score * 0.5 +
    consensus_score * 0.3 +
    clarity_score * 0.2
)
```

Adjust weights in `config.py` to tune behavior.

## API Endpoints

* `GET /` - Health check
* `POST /api/aggregate` - Submit query and get aggregated response
* `GET /api/history` - Retrieve query history
* `DELETE /api/history/{id}` - Delete history item

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
