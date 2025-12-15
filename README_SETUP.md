# Hướng dẫn Setup Môi trường - BDU Chatbot RAG

## Yêu cầu hệ thống

- **Python**: 3.10 hoặc cao hơn (khuyến nghị 3.10.x)
- **OS**: Windows, Linux, hoặc macOS
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB+)
- **Disk**: ~2GB cho dependencies và models

## Cài đặt

### Bước 1: Clone repository

```bash
git clone https://github.com/galabo101/Chatbot_Crag.git
cd Chatbot_Crag
```

### Bước 2: Tạo Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt Dependencies

```bash
# Cài đặt dependencies chính
pip install -r requirements.txt

# (Tùy chọn) Cài đặt development tools
pip install -r requirements-dev.txt
```

### Bước 4: Cấu hình Environment Variables

Tạo file `.env` trong thư mục gốc:

```env
# Groq API Key (Bắt buộc)
GROQ_API_KEY=your_groq_api_key_here

# Google Custom Search API (Tùy chọn - cho web search)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_cse_id_here
```

**Lưu ý**: 
- Groq API key là **bắt buộc** để hệ thống hoạt động
- Google API keys chỉ cần nếu bạn muốn sử dụng tính năng web search fallback

### Bước 5: Khởi tạo Database

Database sẽ tự động được tạo khi chạy ứng dụng lần đầu. File `chat_history.db` sẽ được tạo trong thư mục gốc.

### Bước 6: Kiểm tra Qdrant Data

Đảm bảo thư mục `qdrant_data/` có dữ liệu đã được index. Nếu chưa có, bạn cần:

1. Chuẩn bị file `data/chunks.jsonl`
2. Chạy script indexing:
```bash
python src/embedding/indexer.py
```

## Chạy ứng dụng

### Chạy Streamlit App

```bash
streamlit run app/streamlit_app.py
```

Ứng dụng sẽ mở tại: `http://localhost:8501`

### Chạy Admin Dashboard

Admin dashboard có thể truy cập từ giao diện chính:
1. Mở sidebar
2. Nhấn vào "🔐 Quản trị viên"
3. Nhập mật khẩu: `admin123` (mặc định)

## Troubleshooting

### Lỗi: ModuleNotFoundError

**Nguyên nhân**: Thiếu dependencies

**Giải pháp**:
```bash
# Xóa và cài lại
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Lỗi: CUDA/GPU không hoạt động

**Nguyên nhân**: PyTorch không detect GPU

**Giải pháp**: 
- Kiểm tra CUDA version: `nvidia-smi`
- Cài đặt PyTorch với CUDA support:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```


## Phiên bản Python
Hệ thống đã được test và chạy ổn định với:
- Python 3.10.0 

## Nếu gặp vấn đề, vui lòng liên hệ:

email: 18050082@student.bdu.edu.vn
