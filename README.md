# 🎓 BDU Chatbot RAG - Hệ thống Tư vấn Tuyển sinh Thông minh

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Đồ án tốt nghiệp** - Sinh viên: Nguyễn Bá Trưởng (18050082)  
> Trường Đại học Bình Dương

## 📋 Giới thiệu

Chatbot tư vấn tuyển sinh sử dụng kỹ thuật **Retrieval-Augmented Generation (RAG)** kết hợp với **CRAG (Corrective RAG)** để cung cấp thông tin tuyển sinh chính xác cho Trường Đại học Bình Dương.

### Điểm nổi bật
- 🔍 **CRAG Retriever**: Tự động đánh giá và sửa lỗi kết quả retrieval
- 🧠 **Multi-Query Expansion**: Mở rộng truy vấn để tìm kiếm toàn diện hơn
- ⚡ **Query Decomposition**: Phân tách câu hỏi phức tạp thành các câu đơn giản
- 🛡️ **Security Manager**: Chống prompt injection và rate limiting
- 📊 **Admin Dashboard**: Quản lý dữ liệu và theo dõi thống kê

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User Query    │────▶│  Query Expander  │────▶│  CRAG Retriever │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌──────────────────┐              │
                        │   Groq LLM       │◀─────────────┘
                        │ (llama-3.3-70b)  │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │    Response      │
                        └──────────────────┘
```

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|------------|-----------|
| **Frontend** | Streamlit |
| **LLM** | Groq API (LLaMA 3.3 70B) |
| **Embedding** | Google EmbeddingGemma-300M |
| **Vector DB** | Qdrant (Local) |
| **Database** | SQLite |

## 📁 Cấu trúc thư mục

```
Chatbot_Crag/
├── app/
│   ├── streamlit_app.py      # Giao diện chatbot
│   └── admin_page.py         # Trang quản trị
├── src/
│   ├── pipeline.py           # RAG Pipeline chính
│   ├── retrieval/
│   │   ├── crag_retriever.py # CRAG implementation
│   │   └── multi_query_retriever.py
│   ├── generation/
│   │   └── groq_llm.py       # LLM wrapper
│   └── Advanced_Query/
│       ├── query_expander.py
│       └── query_decomposer.py
├── data/
│   └── chunks.jsonl          # Dữ liệu đã chunk
├── qdrant_data/              # Vector database
├── requirements.txt
└── README.md
```

## 🚀 Hướng dẫn cài đặt

### Yêu cầu hệ thống
- Python 3.10+
- RAM: 8GB+
- Disk: ~5GB

### Cài đặt

```bash
# 1. Clone repository
git clone https://github.com/galabo101/Chatbot_Crag.git
cd Chatbot_Crag

# 2. Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Cài đặt dependencies
pip install -r requirements.txt

# 4. Đăng nhập Hugging Face (để tải model)
huggingface-cli login

# 5. Cấu hình API keys trong file .env
# GROQ_API_KEY=your_key_here
```

### Chạy ứng dụng

```bash
streamlit run app/streamlit_app.py
```

Truy cập: `http://localhost:8501`

## 📊 Kết quả Benchmark

| Nhóm câu hỏi | Accuracy |
|--------------|----------|
| Đơn giản | 89.50% |
| Phức tạp | 91.20% |
| Noisy Input | 78.67% |
| **Tổng thể** | **86.50%** |

## 📝 Tính năng chính

### 1. Chatbot Interface
- Trả lời câu hỏi về tuyển sinh
- Hỗ trợ tiếng Việt có dấu và không dấu
- Trích dẫn nguồn cho mỗi câu trả lời

### 2. Admin Dashboard
- Thống kê lượt chat theo thời gian
- Phân tích từ khóa trending
- Upload và quản lý dữ liệu
- Đồng bộ dữ liệu Qdrant ↔ SQLite

## 👨‍💻 Tác giả

**Nguyễn Bá Trưởng**  
- MSSV: 18050082  
- Email: 18050082@student.bdu.edu.vn  
- Trường Đại học Bình Dương

## 📄 License

MIT License - Xem file [LICENSE](LICENSE) để biết thêm chi tiết.
