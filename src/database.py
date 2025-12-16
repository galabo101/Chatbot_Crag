import sqlite3
import uuid
import json  
from datetime import datetime

DB_FILE = "chat_history.db"

def init_db():
    """Khởi tạo database với schema mới hỗ trợ sources"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS conversations
                 (id TEXT PRIMARY KEY, 
                  user_id TEXT, 
                  title TEXT, 
                  created_at DATETIME)''')
    
    # Bảng messages 
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  conversation_id TEXT, 
                  role TEXT, 
                  content TEXT, 
                  sources TEXT,
                  created_at DATETIME)''')
    
    # Thêm cột sources nếu chưa có
    try:
        c.execute("ALTER TABLE messages ADD COLUMN sources TEXT")
    except sqlite3.OperationalError:
        pass  # Cột đã tồn tại
    
    # Bảng documents để quản lý file upload
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  filename TEXT UNIQUE, 
                  upload_time DATETIME,
                  num_chunks INTEGER)''')
    
    conn.commit()
    conn.close()

# --- DOCUMENT MANAGEMENT FUNCTIONS ---

def add_document(filename, num_chunks):
    """Lưu thông tin file mới upload"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Upsert: Nếu file đã có thì update time và chunks
        c.execute("SELECT id FROM documents WHERE filename = ?", (filename,))
        row = c.fetchone()
        
        if row:
            c.execute("UPDATE documents SET upload_time = ?, num_chunks = ? WHERE filename = ?", 
                      (upload_time, num_chunks, filename))
        else:
            c.execute("INSERT INTO documents (filename, upload_time, num_chunks) VALUES (?, ?, ?)", 
                      (filename, upload_time, num_chunks))
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error add_doc: {e}")
        return False

def get_all_documents():
    """Lấy danh sách documents sắp xếp theo mới nhất"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT filename, upload_time, num_chunks FROM documents ORDER BY upload_time DESC")
        rows = c.fetchall()
        conn.close()
        
        docs = []
        for r in rows:
            docs.append({
                "filename": r[0],
                "upload_time": r[1],
                "num_chunks": r[2]
            })
        return docs
    except Exception as e:
        print(f"DB Error get_docs: {e}")
        return []

def delete_document_record(filename):
    """Xóa record khỏi DB"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM documents WHERE filename = ?", (filename,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error del_doc: {e}")


def save_message(conversation_id, role, content, sources=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Serialize sources thành JSON string
    sources_json = json.dumps(sources, ensure_ascii=False) if sources else None
    
    c.execute(
        "INSERT INTO messages (conversation_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?)", 
        (conversation_id, role, content, sources_json, created_at)
    )
    
    # Cập nhật tiêu đề nếu là tin nhắn user đầu tiên
    if role == "user":
        c.execute("SELECT count(*) FROM messages WHERE conversation_id = ?", (conversation_id,))
        if c.fetchone()[0] <= 1:
            new_title = content[:40] + "..." if len(content) > 40 else content
            c.execute("UPDATE conversations SET title = ? WHERE id = ?", (new_title, conversation_id))
    
    conn.commit()
    conn.close()


def get_messages(conversation_id):    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT role, content, sources FROM messages WHERE conversation_id = ? ORDER BY id", 
        (conversation_id,)
    )
    rows = c.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        msg = {
            "role": row[0], 
            "content": row[1]
        }
        # Deserialize sources từ JSON
        if row[2]:
            try:
                msg["sources"] = json.loads(row[2])
            except json.JSONDecodeError:
                msg["sources"] = []
        
        messages.append(msg)
    
    return messages

def create_conversation(user_id, first_message=None):
    """Tạo cuộc hội thoại mới"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    conv_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = "Cuộc trò chuyện mới"
    if first_message:
        title = first_message[:30] + "..."
    c.execute("INSERT INTO conversations VALUES (?, ?, ?, ?)", (conv_id, user_id, title, created_at))
    conn.commit()
    conn.close()
    return conv_id


def get_user_conversations(user_id):
    """Lấy danh sách chat của user"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title, created_at FROM conversations WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def delete_conversation(conversation_id):
    """Xóa cuộc hội thoại"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    c.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()


def delete_all_conversations(user_id):
    """Xóa tất cả"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM conversations WHERE user_id = ?", (user_id,))
    ids = [row[0] for row in c.fetchall()]
    for i in ids:
        c.execute("DELETE FROM messages WHERE conversation_id = ?", (i,))
    c.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
