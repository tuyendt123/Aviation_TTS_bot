import streamlit as st
import json
import re
import os
import time
import asyncio
from docx import Document
import edge_tts  # Sử dụng Edge-TTS bản vá lỗi mới nhất

# Cấu hình giao diện Web
st.set_page_config(page_title="Aviation TTS Bot", page_icon="✈️", layout="centered")

# 1. Hàm đọc file từ điển JSON
def load_dictionary(file_path="aviation_dict.json"):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 2. Hàm chuẩn hóa văn bản (Thay thế từ viết tắt bằng từ hoàn chỉnh)
def normalize_text(text, dictionary):
    if not text:
        return ""
    sorted_keywords = sorted(dictionary.keys(), key=len, reverse=True)
    for kw in sorted_keywords:
        pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
        text = pattern.sub(dictionary[kw], text)
    return text

# 3. Hàm trích xuất toàn bộ văn bản từ file Word (.docx)
def extract_text_from_docx(file_bytes):
    doc = Document(file_bytes)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

# 4. Hàm Async gọi AI Edge-TTS Engine xuất file âm thanh chất lượng cao
async def generate_audio_async(text, output_path, voice, speed_rate):
    if not text.strip():
        raise ValueError("Văn bản bị trống!")
    
    # Định dạng tốc độ theo chuẩn Edge-TTS (Ví dụ: +15% hoặc +20%)
    # Mặc định tốc độ 1.15 sẽ thành +15%, 1.20 thành +20%
    percentage = int((speed_rate - 1.0) * 100)
    speed_string = f"+{percentage}%" if percentage >= 0 else f"{percentage}%"
    
    # Khởi tạo tiến trình kết nối an toàn đến máy chủ Microsoft
    communicate = edge_tts.Communicate(text, voice, rate=speed_string)
    await communicate.save(output_path)

# --- GIAO DIỆN KHÔNG GIAN LÀM VIỆC ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống tự động chuyển đổi báo cáo Word chuyên ngành thành file âm thanh MP3 AI Neural.")

# Cấu hình Giọng đọc và Tốc độ ở thanh bên cạnh (Sidebar)
st.sidebar.header("Cấu hình Giọng đọc AI")

voice_option = st.sidebar.selectbox(
    "Chọn giọng đọc:",
    options=["vi-VN-HoaiAnNeural (Nữ miền Nam)", "vi-VN-NamMinhNeural (Nam miền Bắc)"],
    index=0
)
# Trích xuất chính xác ID giọng đọc của Microsoft
selected_voice = voice_option.split(" ")[0]

# Thanh trượt cấu hình tốc độ mặc định 1.15 theo yêu cầu của bạn
speed = st.sidebar.slider("Tốc độ đọc (Speed Rate):", min_value=1.0, max_value=1.5, value=1.15, step=0.05)

# Khởi tạo từ điển
aviation_dict = load_dictionary()
with st.sidebar.expander("📝 Từ điển viết tắt đang áp dụng"):
    st.json(aviation_dict)

# Khu vực Upload file Word từ máy tính
uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Đã tải file lên thành công. Đang xử lý cấu trúc...")
    
    raw_text = extract_text_from_docx(uploaded_file)
    clean_text = normalize_text(raw_text, aviation_dict)
    
    st.subheader("Xem trước văn bản xử lý")
    st.text_area("Văn bản AI sẽ đọc thực tế (Đã bung từ viết tắt):", value=clean_text, height=200)
        
    if st.button("🚀 Xuất file MP3", type="primary"):
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{uploaded_file.name.split('.')[0]}_{timestamp}.mp3"
        
        with st.spinner("🤖 Bot AI Neural đang xử lý giọng đọc... Vui lòng đợi."):
            # Chạy luồng Async an toàn trên môi trường Streamlit
            asyncio.run(generate_audio_async(clean_text, output_filename, selected_voice, speed))
            
        if os.path.exists(output_filename):
            st.balloons()
            st.success("🎉 Đã tạo xong file âm thanh chất lượng cao!")
            
            with open(output_filename, "rb") as audio_file:
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3")
                
                st.download_button(
                    label="📥 Tải file MP3 về máy",
                    data=audio_bytes,
                    file_name=output_filename,
                    mime="audio/mp3"
                )
            
            os.remove(output_filename)
