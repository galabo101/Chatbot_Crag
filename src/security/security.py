import re
import time
from collections import defaultdict, deque
from typing import Tuple, Dict
import os
import uuid

class SecurityManager:   
    def __init__(
        self,
        max_length: int = 500,
        max_requests: int = 10,
        window_seconds: int = 60,
        max_file_size_mb: int = 100,
        allowed_extensions: tuple = ('.pdf', '.docx', '.png', '.jpg', '.jpeg', '.json', '.xlsx', '.txt')
    ):
        self.max_length = max_length
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.allowed_extensions = allowed_extensions
        # Rate limiting
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Prompt injection patterns
        self.blacklist_patterns = [
            # Ignore instructions (flexible order)
            r'(ignore|bỏ qua|forget|quên).+(instruction|hướng dẫn)',
            r'(ignore|bỏ qua|forget).+(previous|trước|all|toàn bộ)',
            # Role playing
            r'(you are|bạn là|act as|đóng vai|giả sử|từ bây giờ).+(admin|god|developer|quản trị|hệ thống|trợ lý)',
            # Reveal secrets
            r'(show|reveal|hiển thị|in ra|cho xem|tiết lộ|cho.+biết).+(prompt|source code|api key|database|cấu hình|config)',
            r'api\s*key',
            # SQL/XSS
            r'(SELECT|INSERT|UPDATE|DELETE|DROP)\s+',
            r'<script|javascript:|<%|\$\{',
            # Direct requests
            r'(system prompt|system instruction|hướng dẫn hệ thống)',
            r'(toàn bộ prompt|full prompt|entire prompt)',
            r'(không bị ràng buộc|không giới hạn|unrestricted)',
        ]
        
        print(f"✅ SecurityManager ready ({max_requests} req/{window_seconds}s, max {max_length} chars)")
    
    def validate_and_limit(self, user_id: str, query: str) -> Tuple[bool, str]:
        """
        Combined validation and rate limiting
        
        Returns:
            (is_allowed, error_message)
        """
        # 1. Length check
        if len(query) > self.max_length:
            return False, f"Câu hỏi quá dài (tối đa {self.max_length} ký tự)"
        
        if len(query.strip()) < 3:
            return False, "Câu hỏi quá ngắn"
        
        # 2. Prompt injection check
        for pattern in self.blacklist_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Phát hiện nội dung không hợp lệ"
        
        # 3. Spam check
        if re.search(r'(.)\1{10,}', query):
            return False, "Phát hiện spam"
        
        # 4. Rate limiting
        current_time = time.time()
        history = self.request_history[user_id]
        
        # Clean old requests
        cutoff = current_time - self.window_seconds
        while history and history[0] < cutoff:
            history.popleft()
        
        if len(history) >= self.max_requests:
            return False, f"Vượt quá giới hạn {self.max_requests} câu hỏi/phút. Vui lòng chờ"
        
        # 5. Allow request
        history.append(current_time)
        return True, ""
    
    def get_remaining_requests(self, user_id: str) -> int:
        """Get remaining requests for user"""
        history = self.request_history[user_id]
        cutoff = time.time() - self.window_seconds
        while history and history[0] < cutoff:
            history.popleft()
        return max(0, self.max_requests - len(history))
    
    def validate_file(self, uploaded_file) -> Tuple[bool, str]:
        # 1. Kiểm tra kích thước (Size Limit)
        if uploaded_file.size > self.max_file_size_bytes:
            return False, f"File quá lớn ({uploaded_file.size / 1024 / 1024:.2f}MB). Giới hạn tối đa là {self.max_file_size_bytes / 1024 / 1024}MB."
        # 2. Kiểm tra đuôi file (Extension Whitelist)
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in self.allowed_extensions:
            return False, f"Định dạng file '{file_ext}' không được hỗ trợ. Chỉ chấp nhận: {', '.join(self.allowed_extensions)}"

        valid_mimes = [
            'application/pdf', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
            'text/plain',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
            'application/json', 
            'image/png', 'image/jpeg', 'image/jpg', 'image/webp' 
        ]
        
        
        if uploaded_file.type not in valid_mimes and uploaded_file.type != 'application/octet-stream':
             return False, f"MIME type không hợp lệ: {uploaded_file.type}"
        
        return True, ""
    
    def get_safe_filename(self, original_filename: str) -> str:
        file_ext = os.path.splitext(original_filename)[1].lower()
        # Luôn đổi tên thành UUID ngẫu nhiên
        return f"{uuid.uuid4()}{file_ext}"