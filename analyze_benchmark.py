"""
Benchmark Analysis Script
Phân tích chi tiết kết quả benchmark của RAG Chatbot
"""
import json
import sys
import io
from pathlib import Path

# Fix Unicode encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load benchmark results
results_dir = Path("evaluation/results")
latest_file = sorted(results_dir.glob("e2e_evaluation_*.json"))[-1]

with open(latest_file, encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("📊 BÁO CÁO PHÂN TÍCH BENCHMARK RAG CHATBOT")
print("=" * 70)

# Summary
summary = data.get('summary', {})
print(f"\n📅 Ngày đánh giá: {data.get('evaluation_date', 'N/A')}")
print(f"📝 Tổng số câu hỏi: {data.get('total_questions', 0)}")
print(f"\n🎯 ĐIỂM TỔNG THỂ: {summary.get('overall_score', 0) * 100:.1f}%")
print(f"⏱️  Thời gian phản hồi trung bình: {summary.get('avg_response_time', 0):.2f}s")
print(f"✅ Nhóm tốt nhất: {summary.get('best_group', 'N/A')}")
print(f"⚠️  Nhóm cần cải thiện: {summary.get('worst_group', 'N/A')}")
print(f"💡 Khuyến nghị: {summary.get('recommendation', 'N/A')}")

# Category breakdown
print("\n" + "=" * 70)
print("📈 PHÂN TÍCH THEO DANH MỤC")
print("=" * 70)

results = data.get('detailed_results', [])
categories = {}

for r in results:
    cat = r.get('category', 'unknown')
    metrics = r.get('metrics', {})
    if cat not in categories:
        categories[cat] = {'scores': [], 'kw_coverage': [], 'questions': []}
    
    categories[cat]['scores'].append(metrics.get('overall_score', 0))
    categories[cat]['kw_coverage'].append(metrics.get('keyword_coverage', 0))
    categories[cat]['questions'].append({
        'q': r.get('question', ''),
        'score': metrics.get('overall_score', 0),
        'kw': metrics.get('keyword_coverage', 0)
    })

# Sort by average score
sorted_cats = sorted(categories.items(), key=lambda x: sum(x[1]['scores'])/len(x[1]['scores']))

print("\n🔴 DANH MỤC CẦN CẢI THIỆN (Score < 0.6):")
print("-" * 70)
for cat, stats in sorted_cats:
    avg = sum(stats['scores']) / len(stats['scores'])
    if avg < 0.6:
        avg_kw = sum(stats['kw_coverage']) / len(stats['kw_coverage'])
        print(f"  ❌ {cat.upper()}")
        print(f"     Score: {avg:.2f} | Keyword Coverage: {avg_kw:.2f} | Questions: {len(stats['scores'])}")
        for q in stats['questions']:
            print(f"       • \"{q['q'][:60]}...\" → {q['score']:.2f}")
        print()

print("\n🟢 DANH MỤC HOẠT ĐỘNG TỐT (Score >= 0.8):")
print("-" * 70)
for cat, stats in sorted_cats[::-1]:
    avg = sum(stats['scores']) / len(stats['scores'])
    if avg >= 0.8:
        print(f"  ✅ {cat.upper()}: {avg:.2f} ({len(stats['scores'])} questions)")

# Low score questions
print("\n" + "=" * 70)
print("🔍 CÂU HỎI CÓ ĐIỂM THẤP (Score <= 0.5)")
print("=" * 70)

low_score = [r for r in results if r.get('metrics', {}).get('overall_score', 0) <= 0.5]
print(f"\nTổng: {len(low_score)} câu hỏi cần cải thiện\n")

for r in low_score:
    print(f"  📌 Category: {r.get('category', 'N/A')}")
    print(f"     Question: {r.get('question', 'N/A')}")
    print(f"     Score: {r.get('metrics', {}).get('overall_score', 0):.2f}")
    print(f"     Keyword Coverage: {r.get('metrics', {}).get('keyword_coverage', 0):.2f}")
    print()

# Analysis and Recommendations
print("=" * 70)
print("💡 PHÂN TÍCH VÀ KHUYẾN NGHỊ")
print("=" * 70)

low_cats = [cat for cat, stats in categories.items() 
            if sum(stats['scores'])/len(stats['scores']) < 0.6]

print("\n1. VẤN ĐỀ VỀ DỮ LIỆU:")
print("-" * 40)
for cat in low_cats:
    print(f"   • Thiếu dữ liệu về: {cat}")

print("\n2. VẤN ĐỀ VỀ RETRIEVAL:")
print("-" * 40)
low_kw = [(cat, sum(stats['kw_coverage'])/len(stats['kw_coverage'])) 
          for cat, stats in categories.items() 
          if sum(stats['kw_coverage'])/len(stats['kw_coverage']) < 0.5]
if low_kw:
    print("   • Keyword coverage thấp ở các categories:")
    for cat, kw in low_kw:
        print(f"     - {cat}: {kw:.2f}")
else:
    print("   • Keyword coverage tốt ở tất cả categories")

print("\n3. ĐỀ XUẤT CẢI THIỆN:")
print("-" * 40)
print("   a) Bổ sung dữ liệu cho các chủ đề:")
for cat in low_cats:
    print(f"      - {cat}")
print("   b) Tối ưu thời gian phản hồi (hiện tại khá chậm)")
print("   c) Cải thiện query expansion cho các câu hỏi phức tạp")
print("   d) Thêm web search fallback cho câu hỏi ngoài phạm vi")

print("\n" + "=" * 70)
print("✅ PHÂN TÍCH HOÀN TẤT")
print("=" * 70)
