import streamlit as st
import plotly.graph_objects as go
import re

def run_cnc_3d_simulator():
    """HÀM CHẠY MÔ PHỎNG CNC 3D - FRESH THEME"""
    st.title("🧱 Mô phỏng Cơ Khí Phay CNC 3D Đa Trục")
    st.markdown("Không gian tọa độ 3D lập thể hiển thị rõ ràng độ sâu cắt gọt vật liệu.")

    default_3d = "G00 X0 Y0 Z5\nG01 X20 Y20 Z-2\nG01 X80 Y20 Z-2\nG01 X80 Y80 Z-5\nG00 X0 Y0 Z5"
    
    col_in, col_v3d = st.columns([5, 7], gap="large")
    
    with col_in:
        gcode_3d_text = st.text_area("✍️ Nhập chuỗi lệnh G-Code 3D (X, Y, Z):", value=default_3d, height=250, key="cnc3d_text")
        execute_btn = st.button("🧱 Mô phỏng không gian 3D", use_container_width=True, key="cnc3d_btn")
        
    with col_v3d:
        if execute_btn or gcode_3d_text:
            lines = gcode_3d_text.split('\n')
            xs, ys, zs = [0.0], [0.0], [0.0]
            cx, cy, cz = 0.0, 0.0, 0.0
            
            for line in lines:
                line = line.strip().upper()
                parts = re.findall(r'([XYZG])([+-]?\d*\.?\d*)', line)
                cmd = {letter: float(val) for letter, val in parts if val != ''}
                if 'G' in cmd:
                    cx = cmd.get('X', cx)
                    cy = cmd.get('Y', cy)
                    cz = cmd.get('Z', cz)
                    xs.append(cx); ys.append(cy); zs.append(cz)

            fig = go.Figure()
            fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode='lines+markers', name='Mũi dao CNC', line=dict(color='#e76f51', width=5), marker=dict(size=4, color='#2ec4b6')))
            
            fig.update_layout(
                height=400, paper_bgcolor="#f8f9fa",
                scene=dict(
                    xaxis=dict(title='Trục X', range=[-10, 110]),
                    yaxis=dict(title='Trục Y', range=[-10, 110]),
                    zaxis=dict(title='Trục Z (Độ sâu)', range=[-15, 15])
                )
            )
            st.plotly_chart(fig, use_container_width=True)