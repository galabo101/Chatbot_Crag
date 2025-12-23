# Hướng dẫn Setup Môi trường - BDU Chatbot RAG

## Yêu cầu hệ thống

- **Python**: 3.10 hoặc cao hơn (khuyến nghị 3.10.x)
- **OS**: Windows, Linux, hoặc macOS
- **RAM**: Tối thiểu 8GB (khuyến nghị 8GB+)
- **Disk**: ~5GB cho dependencies và models

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

### Bước 3: Cài đặt Dependencies

```bash
# Cài đặt dependencies chính
pip install -r requirements.txt

### Bước 4: Đăng nhập Hugging Face
huggingface-cli login

Enter your token (input will not be visible):

### Bước 5: Cấu hình Environment Variables

```env
# Groq API Key (Bắt buộc)
GROQ_API_KEY=your_groq_api_key_here

# Google Custom Search API (Tùy chọn - cho web search)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_cse_id_here
```

**Lưu ý**: 
- Groq API key là **bắt buộc** để hệ thống hoạt động

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


# Xóa và cài lại
pip uninstall -r requirements.txt -y
pip install -r requirements.txt


## Phiên bản Python
Hệ thống đã được test và chạy ổn định với:
- Python 3.10.0 

## Nếu gặp vấn đề, vui lòng liên hệ:

email: 18050082@student.bdu.edu.vn
