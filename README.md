# BDU Chatbot RAG — Intelligent Admission Consulting System

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC382D?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Graduation Project** — Nguyễn Bá Trưởng · Binh Duong University

Production-ready AI chatbot built with **Corrective RAG (CRAG)** architecture — automatically evaluates, corrects, and refines retrieval results before generating LLM responses. Features multi-model failover, query decomposition, and REST API for external integration.

---

## Demo

<!-- Thêm ảnh demo vào thư mục docs/ rồi bỏ comment dòng dưới -->
<!-- ![Chat Demo](docs/demo_chat.png) -->
<!-- ![Admin Dashboard](docs/demo_admin.png) -->
<!-- ![Swagger UI](docs/demo_swagger.png) -->

---

## System Architecture

<!-- Render PlantUML diagram thành PNG rồi thêm vào đây -->
<!-- ![Architecture](docs/architecture.png) -->

---

## Key Technical Highlights

| Capability | Implementation |
|---|---|
| **RAG Backend** | End-to-end pipeline: Chunking → Embedding → Vector Store → Retrieval → Generation |
| **CRAG (Corrective RAG)** | LLM-based relevance grading with 3-tier correction: Knowledge Refinement / Hybrid / Web Search |
| **LLM Integration** | Groq API (LLaMA 3.3 70B) with multi-model failover pool & response caching |
| **Prompt Engineering** | Task-specific prompts for generation, evaluation, decomposition, and expansion |
| **Embedding + Vector DB** | Google EmbeddingGemma-300M + Qdrant with cosine similarity search |
| **Data Pipeline** | Multi-modal ingestion with 3 specialized processors: Text (RecursiveChunker), Image (Gemini OCR), Table (JSON→Text+Summary) |
| **REST API (FastAPI)** | 3 endpoints (`/chat`, `/search`, `/health`) with Pydantic schemas & CORS |
| **Query Processing** | Decomposition (complex → sub-queries) + Expansion (paraphrase generation + filtering) |
| **Security** | Prompt injection detection, rate limiting, file validation, input sanitization |
| **Evaluation** | Automated benchmark system (100 questions, 82% accuracy, PASS/FAIL metrics) |
| **Logging** | Centralized structured logging with `RotatingFileHandler` |

---

## Features

| Feature | Description |
|---|---|
| **CRAG Retriever** | Auto-evaluates & self-corrects retrieval quality via LLM grading |
| **Lazy Query Expansion** | Parallel expansion triggered only when initial results are insufficient |
| **Query Decomposition** | Splits complex multi-intent questions into independent sub-queries |
| **Security Manager** | Blocks prompt injection, enforces rate limits per user |
| **Admin Dashboard** | Data management, upload documents, chat analytics |
| **REST API** | FastAPI endpoints: `/chat`, `/search`, `/health` |
| **Response Cache** | MD5-based LLM response caching to reduce latency |
| **LLM Failover** | Automatic fallback across model pool on failure |

---

## CRAG Pipeline Flow

```mermaid
flowchart LR
    A["Query"] --> B["Embed & Search\n(Qdrant)"]
    B --> C["LLM Grading\n(Confidence Score)"]
    C --> D{"Action?"}
    D -- "≥2 CORRECT" --> E["Knowledge\nRefinement"]
    D -- "Mixed results" --> F["Hybrid\n(DB + Web)"]
    D -- "All INCORRECT" --> G["Web Search\nFallback"]
    E & F & G --> H["LLM Generate\n(Failover Pool)"]
    H --> I["Response\n+ Sources"]
```

---

## Configuration & Optimization

Các tham số được tinh chỉnh qua benchmark 100 câu hỏi:

**Chunking** (custom `RecursiveChunker` — Vietnamese-optimized):

| Parameter | Value | Description |
|---|---|---|
| `target_tokens` | 150 | Target chunk size (words, not chars) |
| `max_tokens` | 200 | Maximum chunk size |
| `min_tokens` | 50 | Minimum size — smaller chunks get merged |
| `overlap_tokens` | 30 | Word-based overlap between chunks |
| Split strategy | paragraph → sentence → token | Recursive hierarchical splitting |
| Sentence split | Vietnamese Unicode regex | Handles diacritics (À-ỹ) |

**Retrieval** (CRAG pipeline):

| Parameter | Value | Location | Description |
|---|---|---|---|
| `TOP_K_INITIAL` | 4 | `config.py` | Số chunks ban đầu từ Qdrant |
| `TOP_K_FINAL` | 2 | `config.py` | Số chunks cuối cùng đưa vào LLM |
| `RELEVANCE_THRESHOLD` | 0.5 | `config.py` | Ngưỡng cosine similarity |
| `confidence_threshold` | 0.7 | `relevance_evaluator.py` | Confidence để CORRECT không bị hạ xuống AMBIGUOUS |
| `min_correct_threshold` | 2 | `crag_retriever.py` | Số CORRECT tối thiểu trước khi trigger expansion |
| `num_variations` | 2 | `crag_retriever.py` | Số query variations khi expansion |

**Generation** (LLM):

| Parameter | Value | Location | Description |
|---|---|---|---|
| `max_failures` | 3 | `groq_llm.py` | Số lần fail trước khi bỏ qua model trong pool |
| `cache_max_size` | 50 | `groq_llm.py` | Số response tối đa trong cache |

---

## Tech Stack

| Component | Technology |
|---|---|
| **API Server** | FastAPI + Uvicorn |
| **Frontend** | Streamlit |
| **LLM** | Groq API (LLaMA 3.3 70B, GPT-OSS 120B) |
| **Embedding** | Google EmbeddingGemma-300M (768 dims) |
| **Vector DB** | Qdrant (embedded mode, Cosine similarity) |
| **Text Splitting** | LangChain `RecursiveCharacterTextSplitter` |
| **Document Parsing** | PyMuPDF (PDF), python-docx, Pandas (Excel) |
| **Database** | SQLite (chat history, document management) |
| **Security** | Custom SecurityManager (regex-based injection detection) |
| **Logging** | Python `logging` + `RotatingFileHandler` |

---

## Project Structure

```
Chatbot_Crag/
├── api/                              # REST API layer (FastAPI)
│   ├── __init__.py
│   ├── main.py                       # App factory, lifespan, CORS, 3 endpoints
│   └── schemas.py                    # Pydantic request/response models
├── app/                              # Frontend
│   ├── streamlit_app.py              # Chat UI with session management
│   └── admin_page.py                 # Admin dashboard (stats, upload, manage)
├── src/                              # Core logic
│   ├── pipeline.py                   # Main RAG pipeline orchestrator
│   ├── config.py                     # Centralized configuration
│   ├── database.py                   # SQLite data layer
│   ├── logger.py                     # Structured logging setup
│   ├── admin_backend.py              # Admin operations backend
│   ├── retrieval/
│   │   ├── crag_retriever.py         # CRAG: retrieve → evaluate → correct
│   │   ├── relevance_evaluator.py    # LLM-based relevance grading
│   │   ├── multi_query_retriever.py  # Multi-query merge & dedup
│   │   ├── cross_encoder_reranker.py # Cross-encoder reranking
│   │   └── web_search_corrector.py   # Google CSE fallback
│   ├── generation/
│   │   └── groq_llm.py              # LLM wrapper (failover + cache)
│   ├── embedding/
│   │   ├── indexer.py               # Qdrant vector indexer
│   │   ├── recursive_chunker.py     # Text chunker (Vietnamese-optimized)
│   │   ├── image_ocr.py             # Image OCR via Gemini Vision
│   │   └── table_chunker.py         # Table JSON → Text + Summary
│   ├── Advanced_Query/
│   │   ├── query_decomposer.py      # Multi-intent decomposition
│   │   └── query_expander.py        # Paraphrase expansion + filtering
│   └── security/
│       └── security.py              # Injection detection & rate limiting
├── data/
│   ├── chunks.jsonl                  # Pre-chunked knowledge base
│   └── vietnamese-stopwords.txt      # Vietnamese NLP stopwords
├── logs/                             # Auto-generated log files
├── qdrant_data/                      # Vector database storage
├── benchmark_simple.py               # Automated evaluation script (PASS/FAIL)
├── benchmark_questions.txt           # 100 test questions
├── qdrant_setup.py                   # Vector DB initialization script
├── .env.example                      # Environment variables template
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- RAM: 8GB+

### 1. Clone & Setup

```bash
git clone https://github.com/galabo101/Chatbot_Crag.git
cd Chatbot_Crag

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

### 2. Configuration

```bash
cp .env.example .env
# Fill in your API keys
```

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | API key from [Groq Console](https://console.groq.com/) |
| `GOOGLE_API_KEY` | ❌ | For web search fallback |
| `GOOGLE_CSE_ID` | ❌ | Custom Search Engine ID |

### 3. Run

**Streamlit UI** (chat interface):
```bash
streamlit run app/streamlit_app.py
# → http://localhost:8501
```

**FastAPI** (REST API):
```bash
uvicorn api.main:app --reload --port 8000
# → http://localhost:8000/docs (Swagger UI)
```

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Gửi câu hỏi, trả về answer + sources (qua CRAG + LLM) |
| `POST` | `/search` | Semantic search trực tiếp (chỉ retrieval, không LLM) |
| `GET` | `/health` | Health check + component status |

### `POST /chat`

Full RAG pipeline: Security → Decompose → Retrieve (CRAG) → Generate (LLM).

**Request:**
```json
{
  "query": "Học phí ngành Công nghệ thông tin là bao nhiêu?",
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "query": "Học phí ngành Công nghệ thông tin là bao nhiêu?",
  "answer": "Học phí ngành CNTT tại BDU năm 2025 là...",
  "sources": [
    {
      "chunk_id": "hoc-phi-2025_chunk_1",
      "title": "Học phí năm 2025",
      "score": 0.92,
      "type": "text"
    }
  ],
  "num_sources": 1,
  "timing": {
    "decomposition": 0.15,
    "retrieval": 1.23,
    "generation": 2.45,
    "total": 3.83
  }
}
```

### `POST /search`

Semantic search trực tiếp — trả về chunks liên quan nhất mà không qua LLM. Dùng cho debug retrieval hoặc integration.

**Request:**
```json
{
  "query": "Học phí ngành CNTT",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "Học phí ngành CNTT",
  "results": [
    {
      "chunk_id": "hoc-phi-2025_chunk_1",
      "content": "Học phí ngành Công nghệ Thông tin năm 2025...",
      "score": 0.9234,
      "title": "Học phí năm 2025",
      "type": "text"
    }
  ],
  "total": 5,
  "search_time": 0.045
}
```

### `GET /health`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "pipeline": "ready",
    "qdrant": "connected",
    "llm": "available"
  },
  "uptime_seconds": 3600.5
}
```

> Full interactive docs at **Swagger UI**: `http://localhost:8000/docs`

---

## Benchmark Results

Automated evaluation on 100 real admission questions using LLM-as-judge:

| Result | Count | Rate |
|---|---|---|
| PASS | 82 | 82% |
| FAIL (Missing data) | 15 | 15% |
| FAIL (Wrong answer) | 3 | 3% |
| **Total** | **100** | **100%** |

**Accuracy: 82%** · True error rate: 3% · Avg response time: ~3.8s

---

## Author

**Nguyễn Bá Trưởng**
- Student ID: 18050082
- Email: 18050082@student.bdu.edu.vn
- Binh Duong University

## License

MIT License — See [LICENSE](LICENSE) for details.
