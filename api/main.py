

import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Setup path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from api.schemas import (
    ChatRequest, ChatResponse, ErrorResponse,
    HealthResponse, SourceInfo, TimingInfo, GradedStats
)
from src.logger import setup_logger
from src.pipeline import RAGPipeline

logger = setup_logger("api")

# ========================
# GLOBAL STATE
# ========================
_state = {
    "pipeline": None,
    "start_time": None,
}


# ========================
# LIFESPAN (startup/shutdown)
# ========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo pipeline khi start, cleanup khi shutdown."""
    logger.info("🚀 Starting BDU Chatbot API...")
    _state["start_time"] = time.time()

    try:
        from sentence_transformers import SentenceTransformer

        logger.info("📦 Loading embedding model...")
        embedding_model = SentenceTransformer("google/embeddinggemma-300m")

        logger.info("🔧 Initializing RAG Pipeline...")
        _state["pipeline"] = RAGPipeline(
            model_type="gemma",
            verbose=False,
            preloaded_model=embedding_model
        )
        logger.info("✅ Pipeline ready")
    except Exception as e:
        logger.error(f"❌ Failed to initialize pipeline: {e}")
        raise

    yield  # App đang chạy

    # Shutdown
    logger.info("🛑 Shutting down API...")
    if _state["pipeline"] and hasattr(_state["pipeline"], "retriever"):
        _state["pipeline"].retriever.close()
    logger.info("👋 Goodbye!")


# ========================
# APP FACTORY
# ========================
app = FastAPI(
    title="BDU Chatbot RAG API",
    description="REST API cho hệ thống Chatbot Tư vấn Tuyển sinh Đại học Bình Dương",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — cho phép frontend gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================
# ENDPOINTS
# ========================

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root → Swagger UI."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health Check"
)
async def health_check():
    """Kiểm tra trạng thái hệ thống và các component."""
    pipeline_status = "ready" if _state["pipeline"] else "not_loaded"
    uptime = time.time() - _state["start_time"] if _state["start_time"] else 0

    return HealthResponse(
        status="healthy" if pipeline_status == "ready" else "degraded",
        version="1.0.0",
        components={
            "pipeline": pipeline_status,
            "qdrant": "connected" if pipeline_status == "ready" else "disconnected",
            "llm": "available" if pipeline_status == "ready" else "unavailable",
        },
        uptime_seconds=round(uptime, 2),
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation Error"},
        503: {"model": ErrorResponse, "description": "Service Unavailable"},
    },
    tags=["Chat"],
    summary="Gửi câu hỏi tư vấn tuyển sinh"
)
async def chat(request: ChatRequest):
    """
    Xử lý câu hỏi tuyển sinh qua RAG pipeline.

    - **query**: Câu hỏi (1-500 ký tự)
    - **user_id**: ID người dùng (dùng cho rate-limiting)
    """
    if not _state["pipeline"]:
        raise HTTPException(
            status_code=503,
            detail="Pipeline chưa sẵn sàng. Vui lòng thử lại sau."
        )

    logger.info(f"📨 Query from [{request.user_id}]: {request.query[:80]}...")

    try:
        result = _state["pipeline"].run(
            query=request.query,
            user_id=request.user_id,
        )

        # Kiểm tra lỗi từ pipeline (security, rate-limit, etc.)
        if "error" in result:
            logger.warning(f"⚠️ Pipeline error: {result['error']}")
            raise HTTPException(status_code=422, detail=result["error"])

        # Build response
        sources = [
            SourceInfo(
                chunk_id=s.get("chunk_id"),
                url=s.get("url"),
                title=s.get("title"),
                score=s.get("score"),
                type=s.get("type", "text"),
            )
            for s in result.get("sources", [])
        ]

        timing_data = result.get("timing")
        timing = TimingInfo(**timing_data) if timing_data else None

        graded_data = result.get("graded_stats")
        graded = GradedStats(**graded_data) if graded_data and isinstance(graded_data, dict) else None

        response = ChatResponse(
            query=result.get("query", request.query),
            answer=result.get("answer", ""),
            sources=sources,
            num_sources=result.get("num_sources", 0),
            sub_queries=result.get("sub_queries", []),
            retrieved_chunks=result.get("retrieved_chunks", 0),
            graded_stats=graded,
            timing=timing,
            model_type=result.get("model_type", "gemma"),
            too_complex=result.get("too_complex", False),
        )

        timing_str = f"{response.timing.total:.2f}s" if response.timing else "no timing"
        logger.info(
            f"✅ Response: {len(response.answer)} chars, "
            f"{response.num_sources} sources, {timing_str}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Lỗi hệ thống. Vui lòng thử lại sau."
        )
