from dotenv import load_dotenv
load_dotenv()
import sys
from pathlib import Path
import time
from typing import Dict, Any

sys.path.append(str(Path(__file__).parent))

from logger import setup_logger

logger = setup_logger("pipeline")

from retrieval.crag_retriever import CRAGRetriever
from retrieval.multi_query_retriever import MultiQueryRetriever
from Advanced_Query.query_decomposer import QueryDecomposer
from generation.groq_llm import GroqLLM 
from sentence_transformers import SentenceTransformer
from config import (
    EMBEDDING_MODELS, 
    QDRANT_PATH, 
    TOP_K_INITIAL, 
    TOP_K_FINAL, 
    RELEVANCE_THRESHOLD
)
from security.security import SecurityManager


class RAGPipeline:
    def __init__(
        self, 
        model_type: str = "gemma", 
        verbose: bool = True,       
        preloaded_model: SentenceTransformer = None 
    ):
        self.model_type = model_type
        self.verbose = verbose
        model_config = EMBEDDING_MODELS[model_type]
        
        if self.verbose:
            logger.info(f"Initializing Pipeline ({model_type})...")

        # Khởi tạo Retriever với model đã load sẵn
        self.retriever = CRAGRetriever(
            qdrant_path=QDRANT_PATH,
            collection_name=model_config["collection_name"],
            embedding_model=model_config["name"],
            relevance_threshold=RELEVANCE_THRESHOLD,
            # Truyền model vào
            preloaded_model=preloaded_model
        )
        self.security = SecurityManager(
            max_length=500,
            max_requests=10,
            window_seconds=60
        )
        
        self.llm = GroqLLM()
        self.decomposer = QueryDecomposer()
        self.multi_retriever = MultiQueryRetriever(self.retriever)
        
        if self.verbose:
            logger.info("Pipeline ready")
    
    def run(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        is_valid, error_msg = self.security.validate_and_limit(user_id, query)
        if not is_valid:
            return {
                "error": error_msg,
                "answer": f"❌ {error_msg}",
                "sources": [],
                "num_sources": 0
            }
        start_time = time.time()
        
        if self.verbose:
            logger.info(f"Query: {query}")
        
        # Query Decomposition
        decompose_start = time.time()
        sub_queries = self.decomposer.decompose(query)
        decompose_time = time.time() - decompose_start
        
        # Xử lý câu hỏi quá phức tạp
        if sub_queries == ["TOO_COMPLEX"]:
            return {
                "query": query,
                "sub_queries": [],
                "answer": "Xin lỗi, câu hỏi của bạn có quá nhiều ý. Để tôi có thể trả lời chính xác hơn, bạn vui lòng chia thành các câu hỏi nhỏ hơn nhé! 😊",
                "sources": [],
                "num_sources": 0,
                "retrieved_chunks": 0,
                "graded_stats": {},
                "timing": {"decomposition": decompose_time, "retrieval": 0, "generation": 0, "total": decompose_time},
                "model_type": self.model_type,
                "too_complex": True
            }
        
        # Retrieval
        retrieval_start = time.time()
        refined_chunks, graded_stats = self._retrieve(sub_queries)
        retrieval_time = time.time() - retrieval_start
        
        if self.verbose:
            logger.info(f"Retrieval time: {retrieval_time:.3f}s")
        
        # Generation
        generation_start = time.time()
        generation_result = self._generate(query, sub_queries, refined_chunks)
        generation_time = time.time() - generation_start
        
        total_time = time.time() - start_time
        
        if self.verbose:
            logger.info(
                f"Answer generated | sources={generation_result['num_sources']} | "
                f"total={total_time:.3f}s (decomp={decompose_time:.3f}s, "
                f"retrieval={retrieval_time:.3f}s, generation={generation_time:.3f}s)"
            )
        
        return {
            "query": query,
            "sub_queries": sub_queries,
            "answer": generation_result["answer"],
            "sources": generation_result["sources"],
            "num_sources": generation_result["num_sources"],
            "retrieved_chunks": len(refined_chunks),
            "graded_stats": graded_stats,
            "timing": {
                "decomposition": decompose_time,
                "retrieval": retrieval_time,
                "generation": generation_time,
                "total": total_time
            },
            "model_type": self.model_type
        }
    
    def _retrieve(self, sub_queries: list) -> tuple:       
        if len(sub_queries) == 1:
            # Single query retrieval
            if self.verbose:
                logger.info("Single-Query Retrieval")
            
            result = self.retriever.retrieve(
                sub_queries[0],
                top_k_initial=TOP_K_INITIAL,
                top_k_final=TOP_K_FINAL
            )
            
            refined_chunks = result["refined_chunks"]
            graded_stats = result["graded_stats"]
            
            if self.verbose:
                logger.info(
                    f"Grading: correct={graded_stats['correct']}, "
                    f"ambiguous={graded_stats['ambiguous']}, "
                    f"incorrect={graded_stats['incorrect']} | "
                    f"retrieved={len(refined_chunks)} chunks"
                )
        
        else:
            # Multi-query retrieval
            result = self.multi_retriever.retrieve_multi(
                sub_queries,
                top_k_per_query=3
            )
            
            refined_chunks = result["merged_chunks"]
            graded_stats = result["stats"]
        
        return refined_chunks, graded_stats
    
    def _generate(self, query: str, sub_queries: list, chunks: list) -> dict:        
        if len(sub_queries) == 1:
            return self.llm.generate(query, chunks)
        else:
            return self.llm.generate_multi_intent(query, sub_queries, chunks)