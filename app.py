import streamlit as st
import streamlit.components.v1 as components
import os
import re
from database import get_approved_news, get_pending_news, approve_news, reject_news
from utils import generate_content, text_to_speech, extract_text_from_pdf, scrape_automation_news
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Hệ Sinh Thái Tri Thức Tự Động Hóa", page_icon="🤖", layout="wide")

# =================================================================
# 🌟 CSS INJECTION (CHỈNH ẢNH NHỎ LẠI, CHỮ TIN TỨC TO HƠN)
# =================================================================
st.markdown("""
    <style>
    .stApp { background-color: #f7f9f9; color: #2b2d42; }
    [data-testid="stSidebar"] { background-color: #e6f3f0; border-right: 2px solid #ccece6; }
    [data-testid="stSidebar"] * { color: #1d3557 !important; }
    h1, h2, h3 { color: #1d3557 !important; font-family: 'Segoe UI', sans-serif; }
    
    /* Box tin tức */
    .news-block-container { background-color: #ffffff; padding: 22px; border-radius: 12px; border: 1px solid #e1e8ed; margin-bottom: 25px; }
    
    /* Chỉnh chữ trong tin tức to và rõ hơn */
    .news-title { font-size: 22px !important; font-weight: 700; color: #1d3557; margin-bottom: 10px; line-height: 1.4; }
    .news-desc { font-size: 16px !important; color: #4a4e69; margin-bottom: 15px; }
    
    div.stButton > button { background-color: #2ec4b6 !important; color: white !important; border-radius: 6px !important; border: none !important; }
    div.stButton > button:hover { background-color: #209f93 !important; transform: translateY(-1px); }
    </style>
""", unsafe_allow_html=True)

# Khởi tạo Session State
if "ai_response" not in st.session_state: st.session_state.ai_response = None
if "audio_ready" not in st.session_state: st.session_state.audio_ready = False
if "topic_from_news" not in st.session_state: st.session_state.topic_from_news = ""
if "admin_logged_in" not in st.session_state: st.session_state.admin_logged_in = False
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "quiz_submitted" not in st.session_state: st.session_state.quiz_submitted = False
if "user_answers" not in st.session_state: st.session_state.user_answers = {}

st.sidebar.markdown(
    """
    <div style="text-align: center;">
        <h2 style="margin-bottom: 0; padding-bottom: 0; font-size: 22px;">
            🤖 HỆ SINH THÁI TRI THỨC
        </h2>
        <h4 style="color: #FF4B4B; margin-top: -5px; font-weight: bold; font-size: 16px;">
            TỰ ĐỘNG HÓA
        </h4>
    </div>
    """, 
    unsafe_allow_html=True
)
menu_selected = st.sidebar.radio("Di chuyển giữa các phân hệ:", [
    "📰 Bản Tin Tự Động Hóa", 
    "📚 Trợ Lý Bài Giảng AI", 
    "🔐 Quản Trị Hệ Thống",
    "⚙️ Phân hệ Mô phỏng (Phần 4)"
])

def safe_image(url_string, default_url="https://via.placeholder.com/300x180", width_param='stretch'):
    if url_string and (url_string.startswith("http://") or url_string.startswith("https://")):
        return st.image(url_string, width=width_param)
    return st.image(default_url, width=width_param)

# -----------------------------------------------------------------
# PHẦN 1: BẢN TIN
# -----------------------------------------------------------------
if menu_selected == "📰 Bản Tin Tự Động Hóa":
    st.title("📰 Tin Tức & Ứng Dụng Ngành Tự Động Hóa")
    st.markdown("---")
    approved_articles = get_approved_news()
    
    if not approved_articles:
        st.info("Chưa có tin tức. Vào mục Quản Trị để quét tin!")
    else:
        block_size = 5
        for b_idx in range(0, len(approved_articles), block_size):
            block_articles = approved_articles[b_idx:b_idx + block_size]
            
            hot_news = block_articles[0]
            col_hot_img, col_hot_txt = st.columns([1, 1.8], gap="large")
            with col_hot_img:
                safe_image(hot_news[3], "https://via.placeholder.com/600x350")
            with col_hot_txt:
                st.markdown(f"<div class='news-title'>{hot_news[1]}</div>", unsafe_allow_html=True)
                st.caption(f"📅 *Tin tiêu điểm* | {hot_news[4]}")
                st.markdown("<div class='news-desc'>Bản tin chuyên sâu ngành Tự động hóa mới nhất được chọn lọc tự động từ các nguồn uy tín.</div>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1: st.markdown(f'<a href="{hot_news[2]}" target="_blank"><button style="width:100%;">🔗 Xem nguồn</button></a>', unsafe_allow_html=True)
                with c2:
                    if st.button("🤖 Đưa vào phòng học AI", key=f"hot_{hot_news[0]}", width='stretch'):
                        st.session_state.topic_from_news = hot_news[1]
                        st.success("Đã ghi nhớ!")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            sub_articles = block_articles[1:5]
            for news in sub_articles:
                c_img, c_txt = st.columns([1, 3])
                with c_img: safe_image(news[3], width_param=150)
                with c_txt:
                    st.markdown(f"**{news[1]}**")
                    st.caption(f"📅 {news[4]} | [🔗 Nguồn]({news[2]})")
                    if st.button("🤖 Đưa vào phòng học AI", key=f"sub_{news[0]}"):
                        st.session_state.topic_from_news = news[1]
                        st.success("Đã ghi nhớ!")
                st.markdown("<hr style='margin: 10px 0;'/>", unsafe_allow_html=True)
            st.markdown("<br><hr style='border-top: 3px solid #ccc;'/><br>", unsafe_allow_html=True)

# -----------------------------------------------------------------
# PHẦN 2: TRỢ LÝ AI
# -----------------------------------------------------------------
elif menu_selected == "📚 Trợ Lý Bài Giảng AI":
    st.title("📚 Trợ Lý Học Tập Thông Minh")
    st.markdown("---")
    
    cap_do = st.sidebar.radio("Cấp độ giải thích:", ["Dễ hiểu", "Trung bình", "Chuyên sâu"], index=1)
    default_topic = st.session_state.topic_from_news if st.session_state.topic_from_news else "Hệ thống SCADA"
    user_input = st.text_input("Chủ đề học tập:", value=default_topic)
    
    col_pdf, col_img = st.columns(2)
    with col_pdf: uploaded_pdf = st.file_uploader("📂 Tải file PDF:", type=["pdf"])
    with col_img: uploaded_img = st.file_uploader("🖼️ Tải Hình ảnh sơ đồ:", type=["png", "jpg", "jpeg"])
        
    extracted_doc_text, attached_image = "", None
    if uploaded_pdf:
        with st.spinner("Đang đọc PDF..."): extracted_doc_text = extract_text_from_pdf(uploaded_pdf)
    if uploaded_img:
        attached_image = Image.open(uploaded_img)
        st.image(attached_image, width=200)

    if st.button("🚀 Bắt đầu biên soạn", type="primary", width='stretch'):
        with st.spinner(f"Hệ thống AI đang biên soạn theo cấp độ '{cap_do}'..."):
            combined_topic = user_input
            if extracted_doc_text: combined_topic += f"\n\n[PDF Data]:\n{extracted_doc_text}"
            
            res = generate_content(combined_topic, cap_do, attached_image)
            st.session_state.ai_response = res
            st.session_state.chat_history = []
            st.session_state.quiz_submitted = False
            st.session_state.user_answers = {}
            
            # Chỉ tạo audio nếu không có thông báo lỗi 503
            if "⚠️" not in res:
                audio_path = "lesson_audio.mp3"
                if os.path.exists(audio_path):
                    try: os.remove(audio_path)
                    except: pass
                st.session_state.audio_ready = text_to_speech(res.split("---")[0])
            else:
                st.session_state.audio_ready = False
                
            st.rerun()

    if st.session_state.ai_response:
        # Nếu có lỗi 503, in ra thẳng thông báo và dừng lại
        if "⚠️" in st.session_state.ai_response:
            st.error(st.session_state.ai_response)
        else:
            parts = st.session_state.ai_response.split("---")
            bai_giang = parts[0]
            trac_nghiem = parts[1] if len(parts) > 1 else ""
            
            tab_bg, tab_tn = st.tabs(["📖 BÀI GIẢNG & HỎI ĐÁP", "✍️ PHIẾU TRẮC NGHIỆM ĐÁNH GIÁ"])
            
            with tab_bg:
                col_lec, col_chat = st.columns([7, 5], gap="large")
                with col_lec:
                    st.markdown("### 📚 Nội dung bài học")
                    if st.session_state.audio_ready and os.path.exists("lesson_audio.mp3"):
                        st.audio("lesson_audio.mp3", format="audio/mp3")
                    st.markdown(bai_giang)
                with col_chat:
                    st.markdown("### 💬 Cửa sổ Hỏi đáp")
                    st.caption("Dán thuật ngữ khó hiểu vào đây để AI giải thích nhanh:")
                    chat_box = st.container(height=400)
                    for chat in st.session_state.chat_history:
                        with chat_box.chat_message(chat["role"]): st.write(chat["text"])
                            
                    ask_in = st.text_input("Hỏi AI:", key="ask_ai")
                    if st.button("Gửi câu hỏi", width='stretch'):
                        if ask_in.strip():
                            st.session_state.chat_history.append({"role": "user", "text": ask_in})
                            from google import genai
                            try:
                                client_chat = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                                resp = client_chat.models.generate_content(model='gemini-2.5-flash', contents=f"Dựa trên bài học:\n{bai_giang}\nHãy giải thích: {ask_in}")
                                st.session_state.chat_history.append({"role": "assistant", "text": resp.text})
                            except Exception as e:
                                st.session_state.chat_history.append({"role": "assistant", "text": f"Lỗi: {e}"})
                            st.rerun()

            with tab_tn:
                st.markdown("### ✍️ Phiếu đánh giá kiến thức")
                if not trac_nghiem.strip():
                    st.info("Bài học này không có trắc nghiệm.")
                else:
                    q_blocks = re.findall(r'(Câu \d+:.*?)(?=Câu \d+:|Đáp án đúng:|$)', trac_nghiem, re.DOTALL)
                    ans_keys = re.findall(r'Đáp án đúng:\s*([A-D])', trac_nghiem)
                    exps = re.findall(r'Giải thích:\s*(.*?)(?=Câu \d+:|Đáp án đúng:|$)', trac_nghiem, re.DOTALL)
                    
                    if len(q_blocks) < 5:
                        st.markdown(trac_nghiem)
                    else:
                        for i in range(5):
                            lines = [l.strip() for l in q_blocks[i].split("\n") if l.strip()]
                            q_title = lines[0]
                            options = [l for l in lines[1:] if l.startswith(('A.', 'B.', 'C.', 'D.'))]
                            
                            st.markdown(f"**{q_title}**")
                            if len(options) >= 4:
                                choice = st.radio("Chọn:", options, key=f"q_{i}", index=None, label_visibility="collapsed")
                                if choice: st.session_state.user_answers[i] = choice[0]
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                        st.markdown("---")
                        if st.button("🎯 NỘP BÀI & XEM ĐÁP ÁN", type="primary", width='stretch'):
                            st.session_state.quiz_submitted = True
                            
                        if st.session_state.quiz_submitted:
                            st.markdown("### 📊 KẾT QUẢ CỦA BẠN")
                            score = 0
                            for i in range(5):
                                c_ans = ans_keys[i].strip() if i < len(ans_keys) else "A"
                                u_ans = st.session_state.user_answers.get(i, "Chưa chọn")
                                exp_txt = exps[i].strip() if i < len(exps) else "Không có giải thích."
                                
                                if u_ans == c_ans:
                                    score += 1
                                    st.success(f"✔️ **Câu {i+1}: Chọn [{u_ans}] - CHÍNH XÁC!**")
                                else:
                                    st.error(f"❌ **Câu {i+1}: Chọn [{u_ans}] - SAI. Đáp án là [{c_ans}]**")
                                st.caption(f"💡 *Giải thích:* {exp_txt}")
                            st.metric("TỔNG ĐIỂM", f"{score} / 5")

# -----------------------------------------------------------------
# PHẦN 3: QUẢN TRỊ
# -----------------------------------------------------------------
elif menu_selected == "🔐 Quản Trị Hệ Thống":
    st.title("🔐 Bảng Điều Khiển Quản Trị")
    st.markdown("---")
    if not st.session_state.admin_logged_in:
        with st.form("login"):
            usr = st.text_input("Username:")
            pwd = st.text_input("Password:", type="password")
            if st.form_submit_button("Đăng nhập", width='stretch'):
                if usr == "admin" and pwd == "Abc12345":
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else: st.error("Sai thông tin!")
    else:
        c_act, c_view = st.columns([1, 2])
        with c_act:
            if st.button("🔍 Quét tin tức", type="primary", width='stretch'):
                with st.spinner("Đang quét..."):
                    scrape_automation_news()
                    st.rerun()
            if st.button("🚪 Đăng xuất", width='stretch'):
                st.session_state.admin_logged_in = False
                st.rerun()
        with c_view:
            st.subheader("📋 Hàng đợi phê duyệt")
            p_list = get_pending_news()
            for nid, title, link, img, date in p_list:
                with st.expander(f"📰 {title}"):
                    st.write(link)
                    safe_image(img, width_param=150)
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ Duyệt", key=f"ok_{nid}"): approve_news(nid); st.rerun()
                    with c2:
                        if st.button("❌ Bỏ", key=f"no_{nid}"): reject_news(nid); st.rerun()

# -----------------------------------------------------------------
# PHẦN 4: THÍ NGHIỆM MÔ PHỎNG (ĐÃ BỔ SUNG NHÚNG FILE HTML)
# -----------------------------------------------------------------
elif menu_selected == "⚙️ Phân hệ Mô phỏng (Phần 4)":
    st.title("⚙️ Phòng Thí Nghiệm Ảo")
    
    # Đã thêm "Mô phỏng Mạch điện (HTML)" vào danh sách thả xuống
    sub_sim = st.sidebar.selectbox("Chọn thiết bị:", [
        "Mô phỏng Mạch điện (HTML)", 
        "Mô phỏng CNC 2D", 
        "Mô phỏng CNC 3D", 
        "Mô phỏng IoT Dashboard", 
        "Bộ điều khiển PID", 
        "Hệ thống treo 1/4 xe"
    ])
    
    if sub_sim == "Mô phỏng Mạch điện (HTML)":
        # Sử dụng thư viện components.html để nhúng nguyên vẹn file c.html vào Streamlit
        try:
            with open("c.html", "r", encoding="utf-8") as f:
                html_data = f.read()
            # Mở một iFrame có chiều cao 800px để hiển thị file web html
            components.html(html_data, height=800, scrolling=True)
        except Exception as e:
            st.error(f"⚠️ Hệ thống không tìm thấy file 'c.html'. Vui lòng đảm bảo bạn đã đặt file c.html nằm cùng chung thư mục với file app.py! Chi tiết lỗi: {e}")
            
    elif sub_sim == "Mô phỏng CNC 2D":
        from cnc_simulator import run_cnc_2d_simulator
        run_cnc_2d_simulator()
    elif sub_sim == "Mô phỏng CNC 3D":
        from cnc_simulator_3D import run_cnc_3d_simulator
        run_cnc_3d_simulator()
    elif sub_sim == "Mô phỏng IoT Dashboard":
        from iot_simulator import run_iot_simulator
        run_iot_simulator()
    elif sub_sim == "Bộ điều khiển PID":
        from pid_simulator import run_pid_simulator
        run_pid_simulator()
    elif sub_sim == "Hệ thống treo 1/4 xe":
        from suspension_simulator import run_suspension_simulator
        run_suspension_simulator()
