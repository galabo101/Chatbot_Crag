"""
Script debug để kiểm tra:
1. Chunk nào được retrieve khi hỏi về địa chỉ/liên hệ
2. Prompt gửi đến LLM chứa những gì
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.retrieval.crag_retriever import CRAGRetriever
from src.config import QDRANT_PATH, EMBEDDING_MODELS

# Query test
TEST_QUERY = "dia chi va thong tin lien he voi truong"

print("Loading retriever...")

# Khởi tạo retriever
model_config = EMBEDDING_MODELS["gemma"]
retriever = CRAGRetriever(
    qdrant_path=QDRANT_PATH,
    collection_name=model_config["collection_name"],
    embedding_model=model_config["name"],
    relevance_threshold=0.6
)

# Test 1: Semantic search thuần (không qua CRAG evaluation)
print("Running semantic search...")
query_vector = retriever.embed_query(TEST_QUERY)
candidates = retriever.semantic_search(query_vector, top_k=10)

results = {
    "query": TEST_QUERY,
    "semantic_search_top10": [],
    "crag_result": {}
}

for i, c in enumerate(candidates, 1):
    results["semantic_search_top10"].append({
        "rank": i,
        "chunk_id": c.get("chunk_id", "N/A"),
        "score": float(c.get("score", 0)),
        "content_preview": c.get("content", "")[:200]
    })

# Kiểm tra chunk liên hệ có trong top 10 không
lien_he_found = any("lien-he" in c.get("chunk_id", "").lower() for c in candidates)
results["lien_he_in_top10"] = lien_he_found

# Test 2: Full CRAG retrieval
print("Running full CRAG retrieval...")
crag_result = retriever.retrieve(TEST_QUERY, top_k_initial=10, top_k_final=5)

results["crag_result"] = {
    "action_taken": crag_result['action_taken'],
    "expansion_triggered": crag_result['expansion_triggered'],
    "graded_stats": crag_result['graded_stats'],
    "refined_chunks": []
}

for c in crag_result['refined_chunks']:
    results["crag_result"]["refined_chunks"].append({
        "chunk_id": c.get("chunk_id", "N/A"),
        "content_preview": c.get("content", "")[:300]
    })

lien_he_in_final = any("lien-he" in c.get("chunk_id", "").lower() for c in crag_result['refined_chunks'])
results["lien_he_in_final"] = lien_he_in_final

# Save to JSON
with open("debug_output.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Done! Results saved to debug_output.json")

