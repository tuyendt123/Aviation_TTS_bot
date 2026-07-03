import streamlit as st
import json
import re
import os
import time
from docx import Document
from gtts import gTTS
from pydub import AudioSegment  # THÊM THƯ VIỆN NÀY ĐỂ TĂNG TỐC FILE THẬT

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

# 4. Hàm xử lý tăng tốc độ file âm thanh thực tế bằng Pydub
def generate_audio_with_speed(text, output_path, speed_rate=1.0):
    if not text.strip():
        raise ValueError("Văn bản bị trống!")
    
    # Tạo file gốc 1.0 từ Google
    temp_raw_path = "temp_raw_voice.mp3"
    tts = gTTS(text=text, lang='vi', slow=False)
    tts.save(temp_raw_path)
    
    # Đọc file gốc vào bộ xử lý âm thanh
    audio = AudioSegment.from_file(temp_raw_path, format="mp3")
    
    # Nếu người dùng chỉnh tốc độ khác 1.0, tiến hành ép tăng tốc trực tiếp vào file
    if speed_rate != 1.0:
        audio = audio.speedup(playback_speed=speed_rate)
        
    # Xuất thành file MP3 mới đã được tăng tốc thực sự
    audio.export(output_path, format="mp3")
    
    # Xóa file nháp 1.0 đi
    if os.path.exists(temp_raw_path):
        os.remove(temp_raw_path)

# --- GIAO DIỆN KHÔNG GIAN LÀM VIỆC ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống tự động chuyển đổi báo cáo Word chuyên ngành thành file âm thanh MP3.")

# Cấu hình Giọng đọc và Tốc độ ở thanh bên cạnh (Sidebar)
st.sidebar.header("Cấu hình Giọng đọc AI")

# Thanh trượt chỉnh tốc độ thật cho file tải về (Mặc định để sẵn 1.5 theo ý bạn)
speed = st.sidebar.slider("Tốc độ đọc (Speed Rate):", min_value=1.0, max_value=1.8, value=1.5, step=0.05)

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
        # Thêm timestamp chống dính cache bộ nhớ trình duyệt
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{uploaded_file.name.split('.')[0]}_{timestamp}.mp3"
        
        with st.spinner(f"🤖 Bot đang ghi âm với tốc độ x{speed}... Vui lòng đợi."):
            # Gọi hàm xử lý tốc độ mới
            generate_audio_with_speed(clean_text, output_filename, speed_rate=speed)
            
        if os.path.exists(output_filename):
            st.balloons()
            st.success("🎉 Đã tạo xong file âm thanh!")
            
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
