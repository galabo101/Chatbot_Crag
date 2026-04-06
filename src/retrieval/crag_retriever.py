from typing import List, Dict, Any
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from groq import Groq
import os
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from logger import setup_logger

logger = setup_logger("crag_retriever")

from .relevance_evaluator import RelevanceEvaluator 
from .web_search_corrector import WebSearchCorrector
from Advanced_Query.query_expander import QueryExpander
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Config: Boost score cho chunks có chunk_id chứa keywords đặc biệt
BOOST_KEYWORDS = ["lien-he", "dia-chi", "hotline", "contact", "lien-lac"]
BOOST_SCORE_AMOUNT = 0.15

# Config: Keyword-based fallback - inject chunk cụ thể khi query chứa keywords
# Bao gồm CẢ có dấu và không dấu để đảm bảo match
KEYWORD_CHUNK_INJECT = {
    "thong-tin-lien-he-cua-truong": [       
        "lien he", "dia chi", "hotline", "dien thoai", "email", "so dt", "zalo",        
        "liên hệ", "địa chỉ", "điện thoại", "số điện thoại", "thông tin liên hệ"
    ],
    "ho-so-xet-tuyen-dai-hoc-chinh-quy-2023_chunk_1": [        
        "ho so", "ho so xet tuyen", "giay to", "can chuan bi gi", "nop ho so",       
        "hồ sơ", "hồ sơ xét tuyển", "giấy tờ", "cần chuẩn bị gì", "nộp hồ sơ"
    ]
}


class CRAGRetriever:
    def __init__(
        self,
        qdrant_path: str = "./qdrant_data",
        collection_name: str = "bdu_chunks_gemma",
        embedding_model: str = "google/embeddinggemma-300m",
        relevance_threshold: float = 0.6,
        min_correct_threshold: int = 2,
        preloaded_model: SentenceTransformer = None
    ):
        self.collection_name = collection_name
        self.relevance_threshold = relevance_threshold
        self.min_correct_threshold = min_correct_threshold
        
        logger.info(f"Connecting to Qdrant: {qdrant_path}")
        self.client = QdrantClient(path=qdrant_path)
        
        if preloaded_model:
            logger.info("Using preloaded embedding model")
            self.model = preloaded_model
        else:
            logger.info(f"Loading embedding model: {embedding_model}")
            try:
                self.model = SentenceTransformer(embedding_model)
            except Exception as e:
                logger.warning(f"Connection failed ({str(e)[:50]}...). Trying offline mode...")
                # Thử load offline từ cache
                self.model = SentenceTransformer(embedding_model, local_files_only=True)
        
        # Initialize Components
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY required for CRAG")
        llm_client = Groq(api_key=groq_api_key)
        self.evaluator = RelevanceEvaluator(llm_client)
        self.web_corrector = WebSearchCorrector()
        self.expander = QueryExpander(
            groq_api_key=groq_api_key,
            embedding_model=self.model  # Dùng chung model
        )
        
        logger.info("CRAG Retriever ready (Optimized Lazy Expansion mode)")
    
    def embed_query(self, query: str) -> np.ndarray:
        # Embed query with normalization
        normalized_query = query.strip().lower()
        
        # Chuẩn hóa thời gian
        time_replacements = {
            "năm nay": "năm 2025",
            "hiện nay": "năm 2025", 
            "hiện tại": "năm 2025"
        }
        
        for old, new in time_replacements.items():
            pattern = rf'\b{re.escape(old)}\b'
            normalized_query = re.sub(pattern, new, normalized_query, flags=re.IGNORECASE)
        
        return self.model.encode(normalized_query, convert_to_numpy=True)
    
    def semantic_search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Dict]:
        #Semantic search in Qdrant
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        
        candidates = []
        for hit in results:
            content = hit.payload.get("content", "")  
            title = hit.payload.get("title")
            if not title:
                # Fallback 1: Lấy từ chunk_id
                title = hit.payload.get("chunk_id", "").replace("-", " ").title()            
            if not title:
                title = "Tài liệu tuyển sinh"            
            candidates.append({
                "id": hit.id,
                "score": hit.score,
                "chunk_id": hit.payload.get("chunk_id"),
                "content": content,
                "full_content": hit.payload.get("full_content"),
                "url": hit.payload.get("url"),
                "type": hit.payload.get("type"),
                "title": title,
                "order": hit.payload.get("order"),
                "source": "database"
            })
        
        # Boost score cho chunks có chunk_id đặc biệt
        for candidate in candidates:
            chunk_id = candidate.get("chunk_id", "").lower()
            if any(kw in chunk_id for kw in BOOST_KEYWORDS):
                candidate["score"] += BOOST_SCORE_AMOUNT
                candidate["boosted"] = True
        
        # Re-sort theo score mới
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        return candidates
    
    def evaluate_relevance(self, query: str, candidates: List[Dict]) -> Dict[str, List[Dict]]:
        logger.info(f"Evaluating {len(candidates)} candidates...")
        
        labels = self.evaluator.evaluate_batch(query, candidates)
        
        graded = {
            "correct": [],
            "incorrect": [],
            "ambiguous": []
        }
        
        for doc, label in zip(candidates, labels):
            graded[label.lower()].append(doc)
        
        logger.info(
            f"Evaluation: correct={len(graded['correct'])}, "
            f"ambiguous={len(graded['ambiguous'])}, "
            f"incorrect={len(graded['incorrect'])}"
        )
        
        return graded
    
    def needs_expansion(self, graded: Dict[str, List[Dict]]) -> bool:  #Quyết định có cần Query Expansion không
        correct_count = len(graded["correct"])
        return correct_count < self.min_correct_threshold
    
    def decide_action(self, graded: Dict[str, List[Dict]]) -> str:
        correct_count = len(graded["correct"])
        ambiguous_count = len(graded["ambiguous"])
        
        if correct_count == 0 and ambiguous_count == 0:
            return "WEB_SEARCH"
        
        if correct_count >= 2:
            return "KNOWLEDGE_REFINEMENT"
        
        return "HYBRID"
    
    def apply_correction(
        self, 
        query: str,
        graded: Dict[str, List[Dict]],
        action: str
    ) -> List[Dict]:
        logger.info(f"Action: {action}")
        
        if action == "WEB_SEARCH":
            web_results = self.web_corrector.search(query, max_results=3)
            logger.info(f"Using {len(web_results)} web search results")
            return web_results
        
        elif action == "KNOWLEDGE_REFINEMENT":
            refined = graded["correct"][:5]
            logger.info(f"Using {len(refined)} correct documents")
            return refined
        
        else:  # HYBRID
            internal = graded["correct"] + graded["ambiguous"]
            internal = sorted(internal, key=lambda x: x["score"], reverse=True)[:3]
            
            web_results = self.web_corrector.search(query, max_results=2)
            
            combined = internal + web_results
            logger.info(f"Hybrid: {len(internal)} internal + {len(web_results)} web")
            return combined
    
    def retrieve(
        self, 
        query: str, 
        top_k_initial: int = 4,
        top_k_final: int = 2
    ) -> Dict[str, Any]:

        # INITIAL RETRIEVAL 
        logger.info("Phase 1: Initial retrieval...")        
        query_vector = self.embed_query(query)
        initial_candidates = self.semantic_search(query_vector, top_k=top_k_initial)
        
        if len(initial_candidates) == 0:
            logger.warning("No candidates found")
            return {
                "query": query,
                "refined_chunks": [],
                "graded_stats": {"correct": 0, "incorrect": 0, "ambiguous": 0},
                "action_taken": "NONE",
                "expansion_triggered": False
            }        
        # EVALUATE INITIAL RESULTS 
        graded = self.evaluate_relevance(query, initial_candidates)
        
        # OPTIMIZED LAZY EXPANSION
        expansion_triggered = False
        
        if self.needs_expansion(graded):
            logger.warning(f"Insufficient CORRECT chunks ({len(graded['correct'])} < {self.min_correct_threshold}), triggering expansion...")
            
            expansion_triggered = True
            
            # Chỉ lấy variations
            expanded_queries = self.expander.expand(
                query, 
                num_variations=2,
                include_original=False 
            )            
            # Track chunks đã có để tránh duplicate
            expansion_candidates = []
            seen_ids = set(c["chunk_id"] for c in initial_candidates)
            
            # Embed và search song song cho các expanded queries
            def search_expanded_query(exp_q: str) -> List[Dict]:
                """Thread-safe function để xử lý một expanded query"""
                exp_vector = self.embed_query(exp_q)
                return self.semantic_search(exp_vector, top_k=top_k_initial)
            
            logger.info(f"Parallel expansion with {len(expanded_queries)} queries...")
            with ThreadPoolExecutor(max_workers=max(1, min(len(expanded_queries), 3))) as executor:           
                future_to_query = {
                    executor.submit(search_expanded_query, eq): eq 
                    for eq in expanded_queries
                }               
                for future in as_completed(future_to_query):
                    exp_q = future_to_query[future]
                    try:
                        exp_results = future.result()
                        logger.debug(f"Expanded: {exp_q[:50]}... ({len(exp_results)} results)")                        
                        # Only add new chunks
                        for cand in exp_results:
                            cand_id = cand.get("chunk_id")
                            if cand_id and cand_id not in seen_ids:
                                seen_ids.add(cand_id)
                                expansion_candidates.append(cand)
                    except Exception as e:
                        logger.error(f"Expansion error for '{exp_q[:30]}...': {e}")
            
            logger.info(f"Found {len(expansion_candidates)} new chunks via parallel expansion")            
            
            all_candidates = initial_candidates + expansion_candidates
            graded = self.evaluate_relevance(query, all_candidates)
        
        else:
            logger.info(f"Sufficient CORRECT chunks ({len(graded['correct'])}), no expansion needed")
        
        # DECIDE ACTION & REFINE 
        action = self.decide_action(graded)
        refined_chunks = self.apply_correction(query, graded, action)
        refined_chunks = refined_chunks[:top_k_final]
        
        # KEYWORD-BASED FALLBACK: Inject chunk đặc biệt nếu query chứa keywords
        refined_chunks = self._apply_keyword_fallback(query, refined_chunks)
        
        return {
            "query": query,
            "refined_chunks": refined_chunks,
            "graded_stats": {
                "correct": len(graded["correct"]),
                "incorrect": len(graded["incorrect"]),
                "ambiguous": len(graded["ambiguous"])
            },
            "action_taken": action,
            "expansion_triggered": expansion_triggered
        }
    
    def _apply_keyword_fallback(self, query: str, refined_chunks: List[Dict]) -> List[Dict]:
        """Inject chunk đặc biệt nếu query chứa keywords và chunk chưa có trong kết quả"""
        query_lower = query.lower()
        existing_chunk_ids = {c.get("chunk_id", "").lower() for c in refined_chunks}
        
        for target_chunk_id, keywords in KEYWORD_CHUNK_INJECT.items():
            # Kiểm tra query có chứa keyword nào không
            if any(kw in query_lower for kw in keywords):
                # Kiểm tra chunk đã có trong kết quả chưa
                if target_chunk_id.lower() not in existing_chunk_ids:
                    # Fetch chunk từ Qdrant
                    injected = self._fetch_chunk_by_id(target_chunk_id)
                    if injected:
                        injected["injected_fallback"] = True
                        refined_chunks.insert(0, injected)  # Thêm vào đầu
                        logger.info(f"Injected fallback chunk: {target_chunk_id}")
        
        return refined_chunks
    
    def _fetch_chunk_by_id(self, chunk_id: str) -> Dict:
        """Fetch một chunk cụ thể từ Qdrant theo chunk_id"""
        try:
            results, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="chunk_id",
                            match=MatchValue(value=chunk_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            if results:
                record = results[0]
                return {
                    "id": record.id,
                    "score": 1.0,  # Score cao vì được inject
                    "chunk_id": record.payload.get("chunk_id"),
                    "content": record.payload.get("content", ""),
                    "full_content": record.payload.get("full_content"),
                    "url": record.payload.get("url"),
                    "type": record.payload.get("type"),
                    "title": record.payload.get("title", "Thông tin liên hệ"),
                    "source": "fallback_inject"
                }
        except Exception as e:
            logger.error(f"Fallback fetch error: {e}")
        
        return None
    
    def close(self):
        """Close Qdrant connection."""
        if hasattr(self.client, 'close'):
            self.client.close()