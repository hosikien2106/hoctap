import streamlit as st
import numpy as np
import time
import pandas as pd
from collections import deque
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def run_iot_simulator():
    """
    HÀM CHẠY MÔ PHỎNG IOT - Được tích hợp vào Menu Hệ thống chính
    """
    # CSS tạo các block thẻ thông tin bo góc tươi mát
    st.markdown("""
        <style>
        .simulator-card {
            background-color: #f0f7f4;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #2ec4b6;
            margin-bottom: 15px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🌡️ Mô phỏng IoT Dashboard - Cảm biến & Điều khiển")
    st.markdown("Dữ liệu cảm biến thay đổi trực quan theo thời gian thực. Bạn có thể tương tác bật/tắt thiết bị chấp hành bên dưới.")

    # ------------------ Khởi tạo session state ------------------
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'temp_data' not in st.session_state:
        st.session_state.temp_data = deque(maxlen=60)
        st.session_state.humid_data = deque(maxlen=60)
        st.session_state.light_data = deque(maxlen=60)
        st.session_state.time_data = deque(maxlen=60)
    if 'last_time' not in st.session_state:
        st.session_state.last_time = time.time()
    if 'light_on' not in st.session_state:
        st.session_state.light_on = False
    if 'fan_on' not in st.session_state:
        st.session_state.fan_on = False

    # ------------------ Giao diện điều khiển ------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="simulator-card">', unsafe_allow_html=True)
        st.subheader("⚙️ Tiến trình")
        if st.session_state.running:
            if st.button("🔴 Dừng mô phỏng", type="primary", use_container_width=True):
                st.session_state.running = False
                st.rerun()
        else:
            if st.button("🟢 Kích hoạt", type="primary", use_container_width=True):
                st.session_state.running = True
                st.session_state.last_time = time.time()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="simulator-card">', unsafe_allow_html=True)
        st.subheader("💡 Đèn Lưới")
        if st.session_state.light_on:
            st.markdown("Trạng thái: <span style='color:#e76f51; font-weight:bold;'>💡 ĐANG BẬT</span>", unsafe_allow_html=True)
            if st.button("Tắt Đèn", key="btn_light", use_container_width=True):
                st.session_state.light_on = False
                st.rerun()
        else:
            st.markdown("Trạng thái: <span style='color:#6c757d;'>⚫ ĐANG TẮT</span>", unsafe_allow_html=True)
            if st.button("Bật Đèn", key="btn_light", use_container_width=True):
                st.session_state.light_on = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="simulator-card">', unsafe_allow_html=True)
        st.subheader("💨 Quạt Gió")
        if st.session_state.fan_on:
            st.markdown("Trạng thái: <span style='color:#0077b6; font-weight:bold;'>🌀 ĐANG BẬT</span>", unsafe_allow_html=True)
            if st.button("Tắt Quạt", key="btn_fan", use_container_width=True):
                st.session_state.fan_on = False
                st.rerun()
        else:
            st.markdown("Trạng thái: <span style='color:#6c757d;'>White⚪ ĐANG TẮT</span>", unsafe_allow_html=True)
            if st.button("Bật Quạt", key="btn_fan", use_container_width=True):
                st.session_state.fan_on = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ------------------ Xử lý đồ thị ------------------
    placeholder = st.empty()
    alert_placeholder = st.empty()
    plot_bg_color = "#f8f9fa"
    
    if st.session_state.running:
        current_time = time.time()
        if current_time - st.session_state.last_time >= 1.0:
            st.session_state.last_time = current_time
            
            last_temp = st.session_state.temp_data[-1] if len(st.session_state.temp_data) > 0 else 25.0
            last_humid = st.session_state.humid_data[-1] if len(st.session_state.humid_data) > 0 else 60.0
            
            temp_delta = (0.5 if st.session_state.light_on else 0) - (0.4 if st.session_state.fan_on else 0) + np.random.uniform(-0.3, 0.3)
            new_temp = np.clip(last_temp + temp_delta, 15.0, 45.0)
            
            humid_delta = (-0.6 if st.session_state.fan_on else 0) + np.random.uniform(-0.5, 0.5)
            new_humid = np.clip(last_humid + humid_delta, 30.0, 95.0)
            
            t_str = time.strftime("%H:%M:%S", time.localtime(current_time))
            st.session_state.time_data.append(t_str)
            st.session_state.temp_data.append(new_temp)
            st.session_state.humid_data.append(new_humid)

        if len(st.session_state.time_data) > 0:
            times = list(st.session_state.time_data)
            temps = list(st.session_state.temp_data)
            humids = list(st.session_state.humid_data)
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                subplot_titles=("Đồ thị Nhiệt độ (°C)", "Đồ thị Độ ẩm (%)"))
            fig.add_trace(go.Scatter(x=times, y=temps, mode='lines+markers', name='Nhiệt độ', line=dict(color='#e76f51', width=3)), row=1, col=1)
            fig.add_trace(go.Scatter(x=times, y=humids, mode='lines+markers', name='Độ ẩm', line=dict(color='#2a9d8f', width=3)), row=2, col=1)
            
            fig.update_layout(height=460, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor=plot_bg_color, plot_bgcolor=plot_bg_color)
            
            with placeholder.container():
                st.plotly_chart(fig, use_container_width=True)
                c_m1, c_m2 = st.columns(2)
                c_m1.metric("Nhiệt độ hiện tại", f"{temps[-1]:.2f} °C")
                c_m2.metric("Độ ẩm hiện tại", f"{humids[-1]:.2f} %")
                
            if temps[-1] > 38.0:
                alert_placeholder.error("⚠️ CẢNH BÁO: Nhiệt độ hệ thống vượt ngưỡng! Quạt gió nên được kích hoạt tự động.")
        else:
            placeholder.info("Đang đợi đồng bộ dữ liệu cảm biến...")
        
        time.sleep(0.8)
        st.rerun()
    else:
        if len(st.session_state.time_data) > 0:
            times = list(st.session_state.time_data)
            temps = list(st.session_state.temp_data)
            humids = list(st.session_state.humid_data)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Nhiệt độ (°C)", "Độ ẩm (%)"))
            fig.add_trace(go.Scatter(x=times, y=temps, mode='lines', name='Nhiệt độ', line=dict(color='#e76f51')), row=1, col=1)
            fig.add_trace(go.Scatter(x=times, y=humids, mode='lines', name='Độ ẩm', line=dict(color='#2a9d8f')), row=2, col=1)
            fig.update_layout(height=460, paper_bgcolor=plot_bg_color, plot_bgcolor=plot_bg_color)
            placeholder.plotly_chart(fig, use_container_width=True)
        else:
            placeholder.info("Nhấn nút 'Kích hoạt' phía trên để bắt đầu vẽ luồng dữ liệu IoT.")
        alert_placeholder.empty()