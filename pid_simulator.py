import streamlit as st
import numpy as np
from scipy.integrate import odeint
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def pid_system(y, t, Kp, Ki, Kd, setpoint=1.0):
    x1, x2, integral_error = y
    error = setpoint - x1
    d_integral_error = error
    u = Kp * error + Ki * integral_error + Kd * (0 - x2)
    dx1 = x2
    dx2 = -2*x2 - x1 + u
    return [dx1, dx2, d_integral_error]

def simulate_pid(Kp, Ki, Kd, t_end=5.0):
    t = np.linspace(0, t_end, 500)
    y0 = [0.0, 0.0, 0.0]
    sol = odeint(pid_system, y0, t, args=(Kp, Ki, Kd))
    return t, sol[:, 0]

def compute_metrics(t, y):
    ymax = np.max(y)
    overshoot = max(0.0, (ymax - 1.0) * 100)
    y_final = y[-1]
    settling_time = t[-1]
    for i in range(len(y)-1, -1, -1):
        if abs(y[i] - y_final) > 0.02 * y_final:
            settling_time = t[i]
            break
    return overshoot, settling_time

def run_pid_simulator():
    """HÀM CHẠY MÔ PHỎNG PID - FRESH THEME"""
    st.title("🎛️ Mô phỏng Bộ Điều Khiển PID (Phương Pháp Số)")
    st.markdown("Thay đổi các tham số $K_p$, $K_i$, $K_d$ để quan sát đáp ứng quá độ của đối tượng bậc 2.")

    # CSS Card điều khiển
    st.markdown("""
        <style>
        .pid-card { background-color: #f0f7f4; padding: 18px; border-radius: 10px; border-left: 5px solid #2ec4b6; margin-bottom: 15px; }
        </style>
    """, unsafe_allow_html=True)

    col_ctrl, col_plot = st.columns([4, 8], gap="large")

    with col_ctrl:
        st.markdown('<div class="pid-card">', unsafe_allow_html=True)
        st.subheader("⚙️ Tham Số Khối PID")
        
        Kp = st.slider("Khếch đại tỷ lệ (Kp)", 0.0, 20.0, 1.0, 0.1)
        Ki = st.slider("Tích phân (Ki)", 0.0, 10.0, 0.5, 0.05)
        Kd = st.slider("Vi phân (Kd)", 0.0, 5.0, 0.2, 0.05)

        if st.button("🔄 Reset về mặc định", use_container_width=True):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_plot:
        t, y = simulate_pid(Kp, Ki, Kd, t_end=5.0)
        overshoot, settling_time = compute_metrics(t, y)

        c_m1, c_m2 = st.columns(2)
        c_m1.metric("📊 Độ vọt lố (Overshoot)", f"{overshoot:.1f} %")
        c_m2.metric("⏱️ Thời gian xác lập (2%)", f"{settling_time:.2f} s")

        # Vẽ đồ thị phối màu tươi mát
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t, y=y, mode='lines', name='Đáp ứng hệ thống', line=dict(color='#2ec4b6', width=3)))
        fig.add_hline(y=1.0, line_dash="dash", line_color="#e76f51", annotation_text="Setpoint (Đường đặt)")
        
        fig.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="#f8f9fa",
            plot_bgcolor="#f8f9fa",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)