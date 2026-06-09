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
    if "Lỗi" in text or "NOT_FOUND" in text:
        return "Hệ thống đang xử lý dữ liệu."
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
    """Gọi Gemini API biên soạn giáo trình với cơ chế tự động thử lại khi gặp lỗi 503"""
    if not client:
        return "Lỗi: Chưa cấu hình API Key trong file .env."
        
    prompt = f"""
    Bạn là một Giáo sư Đầu ngành kiêm Giảng viên cao cấp chuyên ngành Tự động hóa.
    Hãy biên soạn một bài giảng cực kỳ chi tiết, phong phú và đầy đủ kiến thức về chủ đề hoặc bài viết sau: "{topic}".
    Yêu cầu trình độ giải thích bám sát mức độ nhận thức: {level}.
    
    Hãy cấu trúc nội dung trả về CHÍNH XÁC theo form sau:
    
    # BÀI GIẢNG CHI TIẾT
    [Viết bài giảng chuyên sâu từ 800 - 1000 từ. Phải bao gồm: Tổng quan, Cấu trúc hệ thống, Nguyên lý vận hành và Ứng dụng thực tế mới nhất].
    
    ---
    # BỘ CÂU HỎI TRẮC NGHIỆM ĐÁNH GIÁ
    [Tạo đúng 5 câu hỏi trắc nghiệm chuyên sâu, viết theo định dạng cấu trúc chính xác dưới đây]:
    
    Câu 1: Nội dung câu hỏi 1
    A. Đáp án A
    B. Đáp án B
    C. Đáp án C
    D. Đáp án D
    Đáp án đúng: A
    
    Câu 2: Nội dung câu hỏi 2
    A. Đáp án A
    B. Đáp án B
    C. Đáp án C
    D. Đáp án D
    Đáp án đúng: B
    
    Câu 3: Nội dung câu hỏi 3
    A. Đáp án A
    B. Đáp án B
    C. Đáp án C
    D. Đáp án D
    Đáp án đúng: C
    
    Câu 4: Nội dung câu hỏi 4
    A. Đáp án A
    B. Đáp án B
    C. Đáp án C
    D. Đáp án D
    Đáp án đúng: D
    
    Câu 5: Nội dung câu hỏi 5
    A. Đáp án A
    B. Đáp án B
    C. Đáp án C
    D. Đáp án D
    Đáp án đúng: A
    """
    
    # Chuẩn bị nội dung gửi đi (Hỗ trợ Multimodal đầu vào nếu có ảnh)
    contents = [prompt]
    if attached_image:
        contents.append(attached_image)

    # Thêm cơ chế Auto-Retry giải quyết triệt để lỗi 503 quá tải máy chủ
    max_retries = 3
    delay = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model='gemini-2.5-flash', contents=contents)
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2  # Tăng thời gian chờ cho lượt sau
                    continue
            return f"Lỗi khi gọi Gemini API: {error_msg}"

def text_to_speech(text):
    """Chuyển đổi văn bản thành âm thanh bài giảng"""
    try:
        from gtts import gTTS
        clean_txt = clean_markdown_for_tts(text)
        if not clean_txt:
            clean_txt = "Nội dung bài học sẵn sàng."
        tts = gTTS(text=clean_txt[:1000], lang='vi')
        output_path = "lecture_voice.mp3"
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"Lỗi TTS: {e}")
        return None

def scrape_automation_news():
    """Hàm cào dữ liệu RSS thông minh, chống lỗi bảo mật, lọc từ khóa tự động hóa"""
    rss_urls = [
        "https://vnexpress.net/rss/tin-cong-nghe.rss",
        "https://tiasang.com.vn/rss",
        "https://www.sciencedaily.com/rss/all.xml"
    ]
    
    keywords = ["tự động hóa", "automation", "robot", "scada", "plc", "ai", "iot", "điều khiển", "cảm biến", "cnc", "nhà máy"]
    count = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for url in rss_urls:
        try:
            # Tải nội dung thô bằng requests để vượt qua tầng chặn của báo chí
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                continue
                
            # Sử dụng feedparser phân tích chuỗi dữ liệu an toàn tránh lỗi 'not well-formed'
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                title = entry.get('title', '')
                link = entry.get('link', '')
                pub_date = entry.get('published', entry.get('pubDate', ''))
                
                if any(kw in title.lower() for kw in keywords):
                    # Tìm ảnh đại diện đại diện an toàn từ thẻ summary hoặc nội dung bài viết
                    image_url = "https://via.placeholder.com/300x180"
                    summary = entry.get('summary', '')
                    if summary:
                        soup = BeautifulSoup(summary, "lxml")
                        img_tag = soup.find('img')
                        if img_tag and img_tag.get('src'):
                            image_url = img_tag['src']
                    
                    add_pending_news(title, link, image_url, pub_date)
                    count += 1
        except Exception as e:
            print(f"Bỏ qua lỗi nguồn {url}: {e}")
            continue
            
    return count