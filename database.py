import sqlite3
from datetime import datetime

DB_NAME = "automation_news.db"

def init_db():
    """Khởi tạo cấu trúc bảng lưu trữ bài viết nếu chưa tồn tại"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            image TEXT,
            published_date TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

def add_pending_news(title, link, image, published_date=None):
    """Thêm một bài báo mới tìm được ở trạng thái Chờ duyệt (Pending)"""
    if not published_date:
        published_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Sử dụng INSERT OR IGNORE để tránh trùng lặp link bài viết
        cursor.execute(
            "INSERT OR IGNORE INTO news (title, link, image, published_date, status) VALUES (?, ?, ?, ?, 'pending')",
            (title, link, image, published_date)
        )
        conn.commit()
    except Exception as e:
        print(f"Lỗi khi lưu bài viết vào DB: {e}")
    finally:
        conn.close()

def approve_news(news_id):
    """Admin duyệt bài - Đăng lên trang chủ công khai"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE news SET status = 'approved' WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()

def reject_news(news_id):
    """Admin từ chối bài - Ẩn đi và không bao giờ xuất hiện lại"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE news SET status = 'rejected' WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()

def get_approved_news():
    """Lấy danh sách các bài viết đã duyệt để hiển thị ở trang 'Báo Mới', bài mới nhất lên đầu"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, link, image, published_date FROM news WHERE status = 'approved' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_pending_news():
    """Lấy danh sách các bài viết chờ duyệt cho Tab Quản trị"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, link, image, published_date FROM news WHERE status = 'pending' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_approved_news(news_id):
    """Xóa một tin tức đã được phê duyệt khỏi cơ sở dữ liệu dựa trên ID"""
    import sqlite3
    # Kết nối tới database (hãy đảm bảo tên file .db trùng với file bạn đang dùng)
    conn = sqlite3.connect("automation_news.db") 
    cursor = conn.cursor()
    try:
        # Tiến hành xóa dòng dữ liệu có ID tương ứng
        cursor.execute("DELETE FROM news WHERE id = ?", (news_id,))
        conn.commit()
    except Exception as e:
        print(f"Lỗi khi xóa tin tức: {e}")
    finally:
        conn.close()
        
# Chạy khởi tạo database ngay khi file này được import
init_db()