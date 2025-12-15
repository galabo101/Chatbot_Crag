from typing import List, Dict, Tuple
from sentence_transformers import CrossEncoder
import numpy as np


class CrossEncoderReranker:    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        preloaded_model: CrossEncoder = None
    ):
        if preloaded_model:
            print("✅ Using preloaded Cross-Encoder model")
            self.model = preloaded_model
        else:
            print(f"🔧 Loading Cross-Encoder: {model_name}")
            self.model = CrossEncoder(model_name)
            print("✅ Cross-Encoder ready")
        
        self.high_threshold = 0.5 
        self.low_threshold = 0.2  
    
    def get_scores(self, query: str, documents: List[Dict]) -> List[float]:
        if not documents:
            return []
        pairs = []
        for doc in documents:
            content = doc.get("full_content") or doc.get("content", "")
            content = content[:1000] if len(content) > 1000 else content
            pairs.append([query, content])        
        # Tính điểm
        scores = self.model.predict(pairs)
        normalized_scores = 1 / (1 + np.exp(-np.array(scores)))        
        return normalized_scores.tolist()
    
    def rerank(
        self, 
        query: str, 
        documents: List[Dict], 
        top_k: int = None
    ) -> List[Dict]:
        if not documents:
            return []        
        scores = self.get_scores(query, documents)
        
        # Gắn score vào documents
        for doc, score in zip(documents, scores):
            doc["rerank_score"] = score
        
        # Sắp xếp theo điểm giảm dần
        sorted_docs = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
        
        if top_k:
            sorted_docs = sorted_docs[:top_k]
        
        return sorted_docs
    
    def grade_documents(
        self, 
        query: str, 
        documents: List[Dict]
    ) -> Dict[str, List[Dict]]:
        if not documents:
            return {"correct": [], "ambiguous": [], "incorrect": []}
        
        scores = self.get_scores(query, documents)
        
        graded = {
            "correct": [],
            "ambiguous": [],
            "incorrect": []
        }
        
        for doc, score in zip(documents, scores):
            doc["rerank_score"] = score
            
            if score >= self.high_threshold:
                graded["correct"].append(doc)
            elif score >= self.low_threshold:
                graded["ambiguous"].append(doc)
            else:
                graded["incorrect"].append(doc)
        
        # Log kết quả
        print(f"[CrossEncoder] Grading results:")
        print(f"   ✅ CORRECT: {len(graded['correct'])}")
        print(f"   ⚠️  AMBIGUOUS: {len(graded['ambiguous'])}")
        print(f"   ❌ INCORRECT: {len(graded['incorrect'])}")
        
        return graded


# Singleton để preload model
_reranker_instance = None

def get_reranker(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> CrossEncoderReranker:

    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = CrossEncoderReranker(model_name=model_name)
    return _reranker_instance
