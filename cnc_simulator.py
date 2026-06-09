import streamlit as st
import plotly.graph_objects as go
import re
import math

# ------------------ Hàm parse G-code ------------------
def parse_gcode(code_lines):
    """
    Parse danh sách các dòng G-code, trả về danh sách các dict lệnh.
    Mỗi lệnh có dạng: {'cmd': 'G00', 'x': float, 'y': float, 'i': float, 'j': float}
    """
    commands = []
    current_x = 0.0
    current_y = 0.0
    for line in code_lines:
        line = line.strip().upper()
        if not line or line.startswith(('(', ';')):
            continue
        # Tách từ khóa và số
        parts = re.findall(r'([A-Z])([+-]?\d*\.?\d*)', line)
        cmd_dict = {}
        for letter, value in parts:
            if value == '':
                continue
            cmd_dict[letter] = float(value) if '.' in value or value.isdigit() else value
        if 'G' not in cmd_dict:
            continue
        g_code = int(cmd_dict['G'])
        # Xử lý G90/G91 (bỏ qua, coi như luôn G90)
        if g_code == 90:
            continue  # chế độ tuyệt đối, mặc định
        if g_code == 91:
            st.warning("Chế độ tương đối (G91) chưa hỗ trợ, vẫn dùng tuyệt đối.")
            continue
        # Lấy tọa độ (nếu có)
        x = cmd_dict.get('X', current_x)
        y = cmd_dict.get('Y', current_y)
        i = cmd_dict.get('I', 0.0)
        j = cmd_dict.get('J', 0.0)
        
        if g_code == 0:   # G00: di chuyển nhanh (vẽ đường thẳng)
            commands.append({'cmd': 'G00', 'x': x, 'y': y})
            current_x, current_y = x, y
        elif g_code == 1: # G01: cắt thẳng
            commands.append({'cmd': 'G01', 'x': x, 'y': y})
            current_x, current_y = x, y
        elif g_code == 2 or g_code == 3: # G02/G03: cung tròn
            commands.append({'cmd': f'G0{g_code}', 'x': x, 'y': y, 'i': i, 'j': j})
            current_x, current_y = x, y
        else:
            st.warning(f"Lệnh G{g_code} chưa được hỗ trợ, bỏ qua.")
    return commands

def generate_points(commands, limit_x=(0,100), limit_y=(0,100)):
    """
    Sinh danh sách các điểm (x,y) từ danh sách lệnh.
    """
    points = [(0.0, 0.0)]  # điểm bắt đầu
    x, y = 0.0, 0.0
    errors = []
    for cmd in commands:
        if cmd['cmd'] in ['G00', 'G01']:
            new_x, new_y = cmd['x'], cmd['y']
            # Kiểm tra giới hạn
            if not (limit_x[0] <= new_x <= limit_x[1] and limit_y[0] <= new_y <= limit_y[1]):
                errors.append(f"Lệnh {cmd['cmd']} đi đến ({new_x},{new_y}) ngoài giới hạn [{limit_x[0]},{limit_x[1]}]x[{limit_y[0]},{limit_y[1]}]")
                continue
            points.append((new_x, new_y))
            x, y = new_x, new_y
        elif cmd['cmd'] in ['G02', 'G03']:
            # Vẽ cung tròn
            x0, y0 = x, y
            x1, y1 = cmd['x'], cmd['y']
            i, j = cmd.get('i', 0), cmd.get('j', 0)
            # Tính tâm
            cx = x0 + i
            cy = y0 + j
            # Bán kính
            r = math.hypot(i, j)
            # Góc bắt đầu và kết thúc
            start_angle = math.atan2(y0 - cy, x0 - cx)
            end_angle = math.atan2(y1 - cy, x1 - cx)
            # G02: theo chiều kim đồng hồ (giảm góc), G03: ngược chiều (tăng góc)
            if cmd['cmd'] == 'G02':
                if end_angle > start_angle:
                    end_angle -= 2*math.pi
                angle_step = -0.05
            else:
                if end_angle < start_angle:
                    end_angle += 2*math.pi
                angle_step = 0.05
            # Sinh các điểm trên cung
            angles = []
            ang = start_angle
            if cmd['cmd'] == 'G02':
                while ang > end_angle:
                    angles.append(ang)
                    ang += angle_step
                angles.append(end_angle)
            else:
                while ang < end_angle:
                    angles.append(ang)
                    ang += angle_step
                angles.append(end_angle)
            for ang in angles:
                px = cx + r * math.cos(ang)
                py = cy + r * math.sin(ang)
                points.append((px, py))
            points.append((x1, y1))  # điểm cuối
            x, y = x1, y1
    return points, errors

# ------------------ Hàm chính nhúng vào app.py ------------------
def run_cnc_2d_simulator():
    """
    HÀM CHẠY MÔ PHỎNG CNC 2D - Đã được bọc và chuẩn hóa theo giao diện hệ thống
    """
    st.title("🛠️ Mô phỏng máy CNC 2D - G-code đơn giản")
    st.markdown("Hỗ trợ các lệnh: **G00**, **G01**, **G02**, **G03** (cung tròn), **G90** (tuyệt đối – mặc định).")

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.subheader("✍️ Nhập G-code")
        default_code = """G00 X10 Y10\nG01 X20 Y30\nG02 X30 Y20 I10 J0\nG01 X40 Y10\nG00 X0 Y0"""
        gcode_input = st.text_area("Các dòng lệnh (mỗi lệnh trên một dòng)", value=default_code, height=200, key="cnc_2d_input_area")
        run_button = st.button("🚀 Chạy mô phỏng", type="primary", key="btn_run_cnc_2d")
        st.caption("Tọa độ tuyệt đối. Giới hạn bàn máy: X[0-100], Y[0-100]")

        # Thiết lập session state riêng biệt cho phân hệ tránh xung đột
        if 'cnc2d_points' not in st.session_state:
            st.session_state['cnc2d_points'] = [(0.0, 0.0)]
        if 'cnc2d_errors' not in st.session_state:
            st.session_state['cnc2d_errors'] = []

        if run_button:
            lines = gcode_input.split('\n')
            commands = parse_gcode(lines)
            if not commands:
                st.warning("Không có lệnh hợp lệ nào!")
            else:
                points, errors = generate_points(commands)
                st.session_state['cnc2d_points'] = points
                st.session_state['cnc2d_errors'] = errors

        # Hiển thị lỗi nếu có
        if st.session_state['cnc2d_errors']:
            for err in st.session_state['cnc2d_errors']:
                st.error(err)

        # Hiển thị bảng tọa độ các điểm then chốt
        if len(st.session_state['cnc2d_points']) > 1:
            st.subheader("📊 Danh sách tọa độ")
            df_points = [{"x": round(p[0], 2), "y": round(p[1], 2)} for p in st.session_state['cnc2d_points']]
            st.dataframe(df_points, width='stretch', height=200)

    with col2:
        st.subheader("📈 Quỹ đạo chạy dao")
        fig = go.Figure()
        points = st.session_state['cnc2d_points']
        
        if points and len(points) > 1:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            
            # Vẽ đường chạy dao phối màu theo phong cách Fresh
            fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines+markers', name='Đường chạy dao',
                                     marker=dict(size=4, color='#e76f51'), line=dict(width=2, color='#1d3557')))
            # Điểm bắt đầu
            fig.add_trace(go.Scatter(x=[xs[0]], y=[ys[0]], mode='markers', name='Điểm bắt đầu',
                                     marker=dict(size=10, color='green', symbol='circle')))
            # Điểm kết thúc
            fig.add_trace(go.Scatter(x=[xs[-1]], y=[ys[-1]], mode='markers', name='Điểm kết thúc',
                                     marker=dict(size=10, color='black', symbol='x')))
            # Giới hạn bàn máy
            fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100,
                          line=dict(color="gray", width=1, dash="dash"), fillcolor="rgba(0,0,0,0)")
            
            fig.update_xaxes(title="X", range=[-10, 110])
            fig.update_yaxes(title="Y", range=[-10, 110], scaleanchor="x", scaleratio=1)
            fig.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10),
                              paper_bgcolor="#f8f9fa", plot_bgcolor="#f8f9fa",
                              hovermode='closest', showlegend=True)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Nhấn 'Chạy mô phỏng' để hiển thị quỹ đạo chạy dao hình học.")

    # 📘 Hướng dẫn nhanh bên dưới
    st.markdown("---")
    st.markdown("### 📘 Hướng dẫn nhanh")
    st.markdown("""
    - **G00 X__ Y__** : Di chuyển nhanh đến tọa độ (đường thẳng nhanh, không cắt)
    - **G01 X__ Y__** : Cắt thẳng đến tọa độ đặt sẵn
    - **G02 X__ Y__ I__ J__** : Cung tròn cùng chiều kim đồng hồ (Tâm cách điểm hiện tại một khoảng I, J)
    - **G03 X__ Y__ I__ J__** : Cung tròn ngược chiều kim đồng hồ
    """)