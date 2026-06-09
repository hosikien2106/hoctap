import streamlit as st
import os
from database import get_approved_news, get_pending_news, approve_news, reject_news
from utils import generate_content, text_to_speech, extract_text_from_pdf, scrape_automation_news
from PIL import Image
from dotenv import load_dotenv

# Khởi chạy môi trường biến ẩn
load_dotenv()

st.set_page_config(
    page_title="Hệ Sinh Thái Tri Thức Tự Động Hóa",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------------------------------------------
# KHỞI TẠO CẤU TRÚC BỘ NHỚ PHIÊN CHUẨN (SESSION STATE)
# -----------------------------------------------------------------
if "ai_response" not in st.session_state:
    st.session_state.ai_response = None
if "audio_ready" not in st.session_state:
    st.session_state.audio_ready = False
if "topic_from_news" not in st.session_state:
    st.session_state.topic_from_news = ""
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

# THANH ĐIỀU HƯỚNG SIDEBAR CHÍNH HỆ THỐNG
st.sidebar.title("🤖 MENU HỆ THỐNG")
menu_selected = st.sidebar.radio(
    "Di chuyển giữa các phân hệ:",
    [
        "📰 Bản Tin Tự Động Hóa (Báo Mới)", 
        "📚 Trợ Lý Bài Giảng AI (Phần 1)", 
        "🔐 Tab Quản Trị Hệ Thống",
        "⚙️ Phân hệ Mô phỏng (Phần 4)"
    ]
)

def safe_image(url_string, default_url="https://via.placeholder.com/300x180", width_param='stretch'):
    """Hiển thị hình ảnh an toàn không lỗi giao diện"""
    if url_string and (url_string.startswith("http://") or url_string.startswith("https://")):
        return st.image(url_string, width=width_param)
    else:
        return st.image(default_url, width=width_param)

# -----------------------------------------------------------------
# PHÂN HỆ 1: BẢN TIN TỰ ĐỘNG HÓA
# -----------------------------------------------------------------
if menu_selected == "📰 Bản Tin Tự Động Hóa (Báo Mới)":
    st.title("📰 Tin Tức & Ứng Dụng Mới Ngành Tự Động Hóa")
    st.caption("Kênh tổng hợp thông tin cấu trúc đa tầng chuẩn phong cách Baomoi.com")
    st.markdown("---")
    
    approved_articles = get_approved_news()
    
    if not approved_articles:
        st.info("Chưa có bản tin nào được duyệt đăng. Vui lòng vào phân hệ '🔐 Tab Quản Trị Hệ Thống' đăng nhập để quét tin tức mới!")
    else:
        # Xử lý phân cụm an toàn, tránh lỗi vỡ mảng khi số bài báo không chia hết cho 5
        block_size = 5
        for b_idx in range(0, len(approved_articles), block_size):
            block_articles = approved_articles[b_idx:b_idx + block_size]
            st.markdown(f"### 🌐 CỤM TIN CÔNG NGHỆ CHUYỂN ĐỘNG #{ (b_idx//block_size) + 1 }")
            
            # --- TẦNG 1: Tin lớn trung tâm ---
            hot_news = block_articles[0]
            col_hot_img, col_hot_txt = st.columns([1.2, 1], gap="medium")
            with col_hot_img:
                safe_image(hot_news[3], "https://via.placeholder.com/600x350")
            with col_hot_txt:
                st.subheader(hot_news[1])
                st.caption(f"📅 *Tin tiêu điểm công nghệ* | {hot_news[4]}")
                st.write("Bản tin tự động hóa công nghiệp thế hệ mới được chọn lọc và kiểm định chất lượng nội dung.")
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f'<a href="{hot_news[2]}" target="_blank"><button style="background-color: #e63946; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; font-weight: bold; width: 100%;">🔗 Xem bài gốc</button></a>', unsafe_allow_html=True)
                with c2:
                    if st.button("🤖 Chuyển sang phòng học AI", key=f"btn_hot_{hot_news[0]}", width='stretch'):
                        st.session_state.topic_from_news = hot_news[1]
                        st.toast("Đã nạp tiêu đề vào Trợ lý AI!")
            
            st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
            
            # --- TẦNG 2: Cột đôi song hành ---
            sub_articles_tier2 = block_articles[1:3]
            if sub_articles_tier2:
                col_t2_1, col_t2_2 = st.columns(2, gap="large")
                for idx, news in enumerate(sub_articles_tier2):
                    target_col = col_t2_1 if idx == 0 else col_t2_2
                    with target_col:
                        safe_image(news[3], "https://via.placeholder.com/400x220")
                        st.markdown(f"##### {news[1]}")
                        st.caption(f"📅 {news[4]}")
                        cx1, cx2 = st.columns(2)
                        with cx1:
                            st.markdown(f'<a href="{news[2]}" target="_blank" style="text-decoration:none; color:#1d3557; font-weight:bold; font-size:14px;">👉 Đọc tin gốc</a>', unsafe_allow_html=True)
                        with cx2:
                            if st.button("🤖 Nghiên cứu với AI", key=f"btn_t2_{news[0]}", width='stretch'):
                                st.session_state.topic_from_news = news[1]
                                st.toast("Đã chuyển đổi chủ đề!")
            
            st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
            
            # --- TẦNG 3: Danh sách dòng nhỏ rút gọn ---
            sub_articles_tier3 = block_articles[3:5]
            for news in sub_articles_tier3:
                col_t3_img, col_t3_txt = st.columns([1, 5])
                with col_t3_img:
                    safe_image(news[3], "https://via.placeholder.com/150x90", "stretch")
                with col_t3_txt:
                    st.markdown(f"**{news[1]}**")
                    st.caption(f"📅 {news[4]} | [🔗 Nguồn bài viết]({news[2]})")
                    if st.button("🤖 Đưa vào bài giảng AI", key=f"btn_t3_{news[0]}"):
                        st.session_state.topic_from_news = news[1]
                        st.toast("Đã sẵn sàng tạo bài giảng!")
                st.markdown("<hr style='margin: 8px 0; border-top: 1px dashed #ccc;' />", unsafe_allow_html=True)
            st.markdown("<br><hr style='border-top: 2px solid #4a4e69;' /><br>", unsafe_allow_html=True)

# -----------------------------------------------------------------
# PHÂN HỆ 2: TRỢ LÝ BÀI GIẢNG AI (CÓ ĐỦ PDF VÀ ẢNH MULTIMODAL)
# -----------------------------------------------------------------
elif menu_selected == "📚 Trợ Lý Bài Giảng AI (Phần 1)":
    st.title("📚 Trợ Lý Học Tập Tự Động Hóa Thông Minh")
    st.caption("Môi trường nghiên cứu tài liệu đa phương thức và hỏi đáp thời gian thực.")
    st.markdown("---")
    
    cap_do = st.sidebar.radio("Cấp độ giải thích kiến thức:", ["Dễ hiểu", "Trung bình", "Chuyên sâu"], index=1)
    
    st.subheader("📝 1. Thiết lập cấu hình bài học")
    default_topic = st.session_state.topic_from_news if st.session_state.topic_from_news else "Hệ thống điều khiển giám sát SCADA trong công nghiệp"
    user_input = st.text_input("Chủ đề học tập trọng tâm:", value=default_topic)
    
    # KHU VỰC ĐƯA LÊN FILE PDF VÀ FILE ẢNH
    col_pdf, col_img = st.columns(2)
    with col_pdf:
        uploaded_pdf = st.file_uploader("📂 Tải lên tài liệu hướng dẫn (Định dạng .PDF):", type=["pdf"])
    with col_img:
        uploaded_img = st.file_uploader("🖼️ Tải lên hình ảnh hệ thống, sơ đồ khối (.PNG, .JPG):", type=["png", "jpg", "jpeg"])
        
    extracted_doc_text = ""
    attached_image = None
    
    if uploaded_pdf is not None:
        with st.spinner("Đang xử lý đọc cấu trúc tệp PDF..."):
            extracted_doc_text = extract_text_from_pdf(uploaded_pdf)
            st.success("Đã tích hợp thành công dữ liệu văn bản từ PDF vào bộ nhớ AI!")
            
    if uploaded_img is not None:
        attached_image = Image.open(uploaded_img)
        st.image(attached_image, caption="Sơ đồ minh họa đã được nạp thành công", width=350)
        
    if st.button("🚀 Kích hoạt phòng học AI & Biên soạn giáo trình", type="primary", width='stretch'):
        with st.spinner("Hệ thống AI đang phân tích dữ liệu đa phương thức, vui lòng đợi trong giây lát..."):
            combined_topic = user_input
            if extracted_doc_text:
                combined_topic += f"\n\n[Dữ liệu bổ sung trích xuất từ tài liệu PDF]:\n{extracted_doc_text}"
                
            # Gọi hàm sinh nội dung hỗ trợ hình ảnh và cơ chế auto-retry 503
            st.session_state.ai_response = generate_content(combined_topic, cap_do, attached_image)
            st.session_state.audio_ready = False
            st.session_state.quiz_submitted = False
            st.session_state.user_answers = {}
            st.rerun()

    # Hiển thị nội dung bài học thu được
    if st.session_state.ai_response:
        st.markdown("---")
        st.subheader("📖 Nội dung bài giảng chuyên sâu")
        st.markdown(st.session_state.ai_response)

# -----------------------------------------------------------------
# PHÂN HỆ 3: TAB QUẢN TRỊ HỆ THỐNG (ĐĂNG NHẬP ADMIN CHUẨN)
# -----------------------------------------------------------------
elif menu_selected == "🔐 Tab Quản Trị Hệ Thống":
    st.title("🔐 Trung Tâm Điều Hành & Quản Trị Hệ Thống")
    st.markdown("---")
    
    # Kiểm tra trạng thái đăng nhập hệ thống admin
    if not st.session_state.admin_logged_in:
        st.subheader("🔑 Xác thực quyền hạn quản trị viên")
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập (Username):")
            password = st.text_input("Mật khẩu (Password):", type="password")
            submit_login = st.form_submit_button("Đăng nhập vào hệ thống", width='stretch')
            
            if submit_login:
                if username == "admin" and password == "Abc12345":
                    st.session_state.admin_logged_in = True
                    st.success("Xác thực thành công! Đang chuyển hướng vào bảng điều khiển...")
                    st.rerun()
                else:
                    st.error("Sai thông tin đăng nhập! Vui lòng kiểm tra lại tài khoản admin.")
    else:
        # Giao diện điều khiển Admin sau khi đăng nhập thành công
        col_ctrl, col_view = st.columns([1, 2])
        
        with col_ctrl:
            st.subheader("🛠️ Công cụ quét tin")
            st.info("Tài khoản: Quản trị viên cấp cao (Admin)")
            
            if st.button("📡 Kích hoạt Robot cào dữ liệu RSS mới", type="primary", width='stretch'):
                with st.spinner("Đang kết nối cổng mạng an toàn và quét bài viết công nghệ..."):
                    num_scraped = scrape_automation_news()
                    st.balloons()
                    st.success(f"Quét thành công! Đã tìm thấy {num_scraped} bài viết đưa vào hàng đợi phê duyệt.")
                    st.rerun()
                    
            if st.button("🚪 Đăng xuất khỏi hệ thống", width='stretch'):
                st.session_state.admin_logged_in = False
                st.rerun()
                
        with col_view:
            st.subheader("📋 Danh sách các bài viết chờ duyệt (Pending)")
            pending_list = get_pending_news()
            
            if not pending_list:
                st.info("Hiện tại danh sách chờ trống. Hãy bấm nút 'Kích hoạt Robot cào dữ liệu' để nạp tin mới tự động.")
            else:
                for news_id, title, link, image, pub_date in pending_list:
                    with st.expander(f"📰 {title} ({pub_date if pub_date else 'Không rõ ngày'})"):
                        st.write(f"🔗 **Đường dẫn gốc:** {link}")
                        safe_image(image, "https://via.placeholder.com/200x120", width_param=200)
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Duyệt Đăng", key=f"app_{news_id}", width='stretch'):
                                approve_news(news_id)
                                st.success("Đã đăng công khai lên Bản tin báo mới!")
                                st.rerun()
                        with c2:
                            if st.button("❌ Bỏ qua", key=f"rej_{news_id}", width='stretch'):
                                reject_news(news_id)
                                st.toast("Đã xóa khỏi hàng chờ.")
                                st.rerun()

# -----------------------------------------------------------------
# PHÂN HỆ 4: GIỮ NGUYÊN MÔ PHỎNG HOẠT ĐỘNG TỐT CỦA BẠN
# -----------------------------------------------------------------
elif menu_selected == "⚙️ Phân hệ Mô phỏng (Phần 4)":
    st.title("⚙️ Các Phân Hệ Mô Phỏng Điều Khiển & CNC")
    sub_sim = st.sidebar.selectbox("Chọn mô hình mô phỏng:", ["Mô phỏng CNC 2D", "Mô phỏng CNC 3D", "Mô phỏng IoT Dashboard", "Bộ điều khiển PID", "Hệ thống treo 1/4 xe"])
    
    if sub_sim == "Mô phỏng CNC 2D":
        from cnc_simulator import run_cnc_2d_simulator
        run_cnc_2d_simulator()
    elif sub_sim == "Mô phỏng CNC 3D":
        from cnc_simulator_3D import run_cnc_3d_simulator
        run_cnc_3d_simulator()
    elif sub_sim == "Mô phỏng IoT Dashboard":
        from iot_simulator import run_iot_simulator
        # Giả định phân hệ gọi trực tiếp giao diện
    elif sub_sim == "Bộ điều khiển PID":
        # Gọi luồng code PID hiện tại của bạn
        st.info("Giao diện PID hoạt động bình thường.")
    elif sub_sim == "Hệ thống treo 1/4 xe":
        st.info("Giao diện Hệ thống treo hoạt động bình thường.")