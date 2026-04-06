
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ========================
# REQUEST SCHEMAS
# ========================

class ChatRequest(BaseModel):
    """Request body cho /chat endpoint."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Câu hỏi của người dùng",
        examples=["Học phí ngành Công nghệ thông tin là bao nhiêu?"]
    )
    user_id: str = Field(
        default="anonymous",
        description="ID định danh người dùng"
    )


class HealthCheckRequest(BaseModel):
    """Request cho health check (không cần body)."""
    pass


# ========================
# RESPONSE SCHEMAS
# ========================

class SourceInfo(BaseModel):
    """Thông tin nguồn tham khảo."""
    chunk_id: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    score: Optional[float] = None
    type: str = Field(default="text", description="Loại nguồn: text, table, etc.")


class TimingInfo(BaseModel):
    """Thông tin thời gian xử lý pipeline."""
    decomposition: float = Field(description="Thời gian phân tách câu hỏi (s)")
    retrieval: float = Field(description="Thời gian truy xuất (s)")
    generation: float = Field(description="Thời gian sinh câu trả lời (s)")
    total: float = Field(description="Tổng thời gian xử lý (s)")


class GradedStats(BaseModel):
    """Thống kê đánh giá relevance của chunks."""
    correct: int = 0
    incorrect: int = 0
    ambiguous: int = 0


class ChatResponse(BaseModel):
    """Response body cho /chat endpoint."""
    query: str = Field(description="Câu hỏi gốc")
    answer: str = Field(description="Câu trả lời từ hệ thống")
    sources: List[SourceInfo] = Field(default_factory=list, description="Danh sách nguồn tham khảo")
    num_sources: int = Field(default=0, description="Số lượng nguồn")
    sub_queries: List[str] = Field(default_factory=list, description="Các câu hỏi con (nếu query phức tạp)")
    retrieved_chunks: int = Field(default=0, description="Số chunks đã truy xuất")
    graded_stats: Optional[GradedStats] = None
    timing: Optional[TimingInfo] = None
    model_type: str = Field(default="gemma", description="Embedding model sử dụng")
    too_complex: bool = Field(default=False, description="Query quá phức tạp?")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Học phí ngành CNTT?",
                "answer": "Học phí ngành Công nghệ Thông tin tại BDU là...",
                "sources": [
                    {
                        "chunk_id": "hoc-phi-2025_chunk_1",
                        "url": "https://bdu.edu.vn/hoc-phi",
                        "title": "Học phí năm 2025",
                        "score": 0.92,
                        "type": "text"
                    }
                ],
                "num_sources": 1,
                "sub_queries": [],
                "retrieved_chunks": 2,
                "timing": {
                    "decomposition": 0.15,
                    "retrieval": 1.23,
                    "generation": 2.45,
                    "total": 3.83
                },
                "model_type": "gemma"
            }
        }


class ErrorResponse(BaseModel):
    """Response khi có lỗi."""
    error: str = Field(description="Mô tả lỗi")
    detail: Optional[str] = Field(default=None, description="Chi tiết lỗi (debug)")


class HealthResponse(BaseModel):
    """Response cho health check."""
    status: str = Field(description="Trạng thái hệ thống")
    version: str = Field(description="Phiên bản API")
    components: Dict[str, str] = Field(
        description="Trạng thái từng component",
        default_factory=dict
    )
    uptime_seconds: Optional[float] = None


class SearchRequest(BaseModel):
    """Request body cho /search endpoint (chỉ retrieval, không generation)."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Câu truy vấn tìm kiếm",
        examples=["Học phí ngành CNTT"]
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Số lượng kết quả trả về (1-20)"
    )


class SearchResult(BaseModel):
    """Một kết quả tìm kiếm."""
    chunk_id: Optional[str] = None
    content: str = Field(description="Nội dung chunk")
    score: float = Field(description="Cosine similarity score")
    title: Optional[str] = None
    url: Optional[str] = None
    type: str = "text"


class SearchResponse(BaseModel):
    """Response body cho /search endpoint."""
    query: str
    results: List[SearchResult] = Field(default_factory=list)
    total: int = 0
    search_time: float = Field(description="Thời gian tìm kiếm (seconds)")

