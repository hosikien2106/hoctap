import os
import re
import time
import requests
import feedparser
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv
from database import add_pending_news

# Tải cấu hình bảo mật từ file .env
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")

if gemini_key:
    client = genai.Client(api_key=gemini_key)
else:
    client = None

def clean_markdown_for_tts(text):
    if "Lỗi" in text or "NOT_FOUND" in text or "⚠️" in text:
        return "Hệ thống đang xử lý dữ liệu, vui lòng thử lại."
    if "---" in text:
        text = text.split("---")[0]
    clean_text = re.sub(r'[\#\*\_\[\]\-\-\-\:\d\.]', ' ', text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def extract_text_from_pdf(uploaded_file):
    """Trích xuất văn bản từ file PDF tải lên"""
    try:
        import pypdf
        reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"[Không thể bóc tách file PDF: {str(e)}]"

def generate_content(topic, level, attached_image=None):
    """Gọi Gemini API biên soạn giáo trình, Xử lý lỗi 503 Quá tải bằng Exponential Backoff"""
    if not client:
        return "Lỗi: Chưa cấu hình API Key trong file .env."
        
    prompt = f"""
    Bạn là một Giáo sư chuyên ngành Tự động hóa. Hãy biên soạn bài giảng về chủ đề: "{topic}".
    BẮT BUỘC tuân thủ mức độ nhận thức: {level}. 
    - Nếu là 'Dễ hiểu': Dùng từ ngữ phổ thông, ví dụ thực tế đời sống, tránh toán học phức tạp.
    - Nếu là 'Trung bình': Cân bằng nguyên lý và thực hành.
    - Nếu là 'Chuyên sâu': Đi sâu vào học thuật, toán học, cấu trúc kỹ thuật phức tạp.
    
    BẮT BUỘC TRÌNH BÀY ĐÚNG CẤU TRÚC SAU (Không thêm bớt):
    
    # BÀI GIẢNG CHI TIẾT
    [Viết nội dung bài giảng bám sát mức độ {level} ở đây]
    
    ---
    # BỘ CÂU HỎI TRẮC NGHIỆM ĐÁNH GIÁ
    [Tạo 5 câu hỏi, bắt buộc các đáp án A, B, C, D phải nằm trên các dòng riêng biệt. Dùng đúng format sau]:
    
    Câu 1: [Nội dung câu hỏi]
    A. [Đáp án A]
    B. [Đáp án B]
    C. [Đáp án C]
    D. [Đáp án D]
    Đáp án đúng: A
    Giải thích: [Lý do ngắn gọn]
    
    Câu 2: [Nội dung câu hỏi]
    A. [Đáp án A]
    B. [Đáp án B]
    C. [Đáp án C]
    D. [Đáp án D]
    Đáp án đúng: B
    Giải thích: [Lý do ngắn gọn]
    
    Câu 3: [Nội dung câu hỏi]
    A. [Đáp án A]
    B. [Đáp án B]
    C. [Đáp án C]
    D. [Đáp án D]
    Đáp án đúng: C
    Giải thích: [Lý do ngắn gọn]
    
    Câu 4: [Nội dung câu hỏi]
    A. [Đáp án A]
    B. [Đáp án B]
    C. [Đáp án C]
    D. [Đáp án D]
    Đáp án đúng: D
    Giải thích: [Lý do ngắn gọn]
    
    Câu 5: [Nội dung câu hỏi]
    A. [Đáp án A]
    B. [Đáp án B]
    C. [Đáp án C]
    D. [Đáp án D]
    Đáp án đúng: A
    Giải thích: [Lý do ngắn gọn]
    """
    
    contents = [prompt]
    if attached_image:
        contents.append(attached_image)

    # Nâng cấp lên 5 lần thử lại, thời gian chờ bắt đầu từ 3 giây -> 6s -> 12s...
    max_retries = 5 
    delay = 3
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=contents)
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2  # Tăng gấp đôi thời gian chờ cho lần thử sau
                    continue
            # Đổi câu báo lỗi khô khan thành lời nhắn thân thiện
            return f"⚠️ **Hệ thống Google Gemini hiện đang quá tải do nhu cầu cao (Lỗi 503).**\n\nHệ thống của chúng ta đã thử kết nối lại {max_retries} lần nhưng chưa thành công. Vui lòng đợi khoảng 1-2 phút và nhấn nút 'Bắt đầu biên soạn' một lần nữa nhé!"

def text_to_speech(text):
    try:
        from gtts import gTTS
        clean_txt = clean_markdown_for_tts(text)
        if not clean_txt or "⚠️" in clean_txt:
            return None
        tts = gTTS(text=clean_txt[:1000], lang='vi')
        output_path = "lecture_voice.mp3"
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"Lỗi TTS: {e}")
        return None

def scrape_automation_news():
    rss_urls = [
        "https://vnexpress.net/rss/tin-cong-nghe.rss",
        "https://tiasang.com.vn/rss",
        "https://vnexpress.net/rss/khoa-hoc.rss",
        "https://vnexpress.net/rss/so-hoa.rss",
        "https://vnexpress.net/rss",
        "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss",
        "https://vnexpress.net/rss/tin-moi-nhat.rss",
        "https://tuoitre.vn/rss/cong-nghe.rss",
        "https://dantri.com.vn/rss/cong-nghe.rss",
        "https://www.wired.com/feed/rss",
        "https://spectrum.ieee.org/feed/rss",
        "https://www.deepmind.com/blog/rss",
        "https://openai.com/blog/rss/",        
        "https://ai.googleblog.com/feeds/posts/default",
        "https://techcrunch.com/feed/",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.technologyreview.com/feed/",
        "https://www.sciencedaily.com/rss/all.xml"
    ]
    keywords = ["tự động hóa", "automation", "robot", "scada", "plc", "ai", "iot", "điều khiển", "cảm biến", "cnc", "nhà máy"]
    count = 0
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in rss_urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200: continue
            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                title = entry.get('title', '')
                link = entry.get('link', '')
                pub_date = entry.get('published', entry.get('pubDate', ''))
                
                if any(kw in title.lower() for kw in keywords):
                    image_url = "https://via.placeholder.com/300x180"
                    summary = entry.get('summary', '')
                    if summary:
                        soup = BeautifulSoup(summary, "lxml")
                        img_tag = soup.find('img')
                        if img_tag and img_tag.get('src'): image_url = img_tag['src']
                    
                    add_pending_news(title, link, image_url, pub_date)
                    count += 1
        except Exception: continue
    return count
