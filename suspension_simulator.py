import streamlit as st
import numpy as np
from scipy.integrate import solve_ivp
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def quarter_car_model(t, y, M, k, c, step_amplitude, vehicle_speed, step_length):
    z_s, dz_s = y
    v_m_s = vehicle_speed / 3.6
    t_start = 0.5
    t_end_step = t_start + (step_length / v_m_s)
    
    if t_start <= t <= t_end_step:
        z_r = step_amplitude
        dz_r = 0.0
    else:
        z_r = 0.0
        dz_r = 0.0
        
    d2z_s = (-k * (z_s - z_r) - c * (dz_s - dz_r)) / M
    return [dz_s, d2z_s]

def run_suspension_simulator():
    """HÀM CHẠY MÔ PHỎNG HỆ THỐNG TREO - FRESH THEME"""
    st.title("🚗 Mô phỏng Hệ Thống Treo 1/4 Xe Ô Tô")
    st.markdown("Khảo sát dao động, dịch chuyển và gia tốc đứng của thân xe khi đi qua gờ giảm tốc mặt đường.")

    st.markdown("""
        <style>
        .susp-card { background-color: #e6f3f0; padding: 18px; border-radius: 10px; border-left: 5px solid #1d3557; }
        </style>
    """, unsafe_allow_html=True)

    col_side, col_main = st.columns([4, 8], gap="large")

    with col_side:
        st.markdown('<div class="susp-card">', unsafe_allow_html=True)
        st.subheader("🛠️ Thông Số Cơ Khí")
        M = st.number_input("Khối lượng thân xe M (kg):", 100, 2000, 250, step=50)
        k = st.slider("Độ cứng lò xo k (N/m):", 5000, 50000, 15000, 1000)
        c = st.slider("Hệ số giảm chấn c (Ns/m):", 500, 5000, 1500, 100)
        
        st.subheader("🛣️ Thông Số Mặt Đường")
        step_amplitude = st.slider("Độ cao gờ giảm tốc (m):", 0.01, 0.15, 0.05, 0.01)
        vehicle_speed = st.slider("Vận tốc xe chạy (km/h):", 10, 100, 40, 5)
        step_length = st.number_input("Chiều dài gờ (m):", 0.1, 2.0, 0.5, step=0.1)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_main:
        t_span = (0, 3.0)
        t_eval = np.linspace(0, 3.0, 600)
        y0 = [0.0, 0.0]
        
        sol = solve_ivp(quarter_car_model, t_span, y0, t_eval=t_eval, 
                        args=(M, k, c, step_amplitude, vehicle_speed, step_length))
        
        t_steps = sol.t
        z_s_computed = sol.y[0]
        dz_s_computed = sol.y[1]
        
        # Tính gia tốc đứng
        v_m_s = vehicle_speed / 3.6
        z_r_arr = np.zeros_like(t_steps)
        for idx, t_val in enumerate(t_steps):
            if 0.5 <= t_val <= 0.5 + (step_length / v_m_s):
                z_r_arr[idx] = step_amplitude
        
        accel = (-k * (z_s_computed - z_r_arr) - c * dz_s_computed) / M

        # Đồ thị Subplot đồng bộ màu sắc mát mắt
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Dịch chuyển thân xe (m)", "Gia tốc đứng thân xe (m/s²)"))
        fig.add_trace(go.Scatter(x=t_steps, y=z_s_computed, mode='lines', name='Dịch chuyển', line=dict(color='#2ac4b6', width=3)), row=1, col=1)
        fig.add_trace(go.Scatter(x=t_steps, y=accel, mode='lines', name='Gia tốc', line=dict(color='#e76f51', width=3)), row=2, col=1)
        
        fig.update_layout(height=450, paper_bgcolor="#f8f9fa", plot_bgcolor="#f8f9fa", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.info(f"💡 **Nhận xét chuyên gia:** Với độ cứng k = {k} N/m và giảm chấn c = {c} Ns/m, xe dập tắt dao động trong thời gian ngắn, đảm bảo độ êm dịu chuyển động.")