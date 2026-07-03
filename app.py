import streamlit as st
import json
import re
import os
import time
from docx import Document
from gtts import gTTS
from pydub import AudioSegment  # Thư viện xử lý tăng/giảm tốc độ âm thanh

# Cấu hình giao diện Web
st.set_page_config(page_title="Aviation TTS Bot", page_icon="✈️", layout="centered")

# 1. Hàm đọc file từ điển JSON
def load_dictionary(file_path="aviation_dict.json"):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 2. Hàm chuẩn hóa văn bản
def normalize_text(text, dictionary):
    if not text:
        return ""
    sorted_keywords = sorted(dictionary.keys(), key=len, reverse=True)
    for kw in sorted_keywords:
        pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
        text = pattern.sub(dictionary[kw], text)
    return text

# 3. Hàm trích xuất văn bản từ file Word
def extract_text_from_docx(file_bytes):
    doc = Document(file_bytes)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

# 4. Hàm chuyển đổi text thành MP3 kết hợp chỉnh tốc độ chính xác
def generate_audio_with_speed(text, output_path, speed_rate=1.0):
    if not text.strip():
        raise ValueError("Văn bản bị trống!")
    
    # Bước a: Sinh file MP3 gốc từ Google với tốc độ mặc định
    temp_raw_path = "temp_raw_voice.mp3"
    tts = gTTS(text=text, lang='vi', slow=False)
    tts.save(temp_raw_path)
    
    # Bước b: Dùng pydub để biến đổi tốc độ theo ý muốn
    audio = AudioSegment.from_file(temp_raw_path, format="mp3")
    
    if speed_rate != 1.0:
        # Tăng tốc độ nhưng giữ nguyên cao độ giọng hát/nói (không bị thé tiếng)
        audio = audio.speedup(playback_speed=speed_rate)
        
    audio.export(output_path, format="mp3")
    
    # Dọn dẹp file rác
    if os.path.exists(temp_raw_path):
        os.remove(temp_raw_path)

# --- GIAO DIỆN KHÔNG GIAN LÀM VIỆC ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống dịch thuật ngữ viết tắt và xuất báo cáo Word sang file MP3.")

# Khởi tạo từ điển
aviation_dict = load_dictionary()
with st.sidebar.expander("📝 Từ điển viết tắt đang áp dụng", expanded=True):
    st.json(aviation_dict)

# Khu vực điều chỉnh tốc độ ở thanh bên (Sidebar)
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Cấu hình giọng đọc")
# Cho phép trượt từ 1.0 đến 1.5, bước nhảy là 0.05. Mặc định bạn chọn là 1.1
speed = st.sidebar.slider("Tốc độ đọc (Speed Rate):", min_value=1.0, max_value=1.5, value=1.15, step=0.05)

# Khu vực Upload file Word từ máy tính
uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.info("Đang xử lý cấu trúc file...")
    raw_text = extract_text_from_docx(uploaded_file)
    clean_text = normalize_text(raw_text, aviation_dict)
    
    st.subheader("Xem trước văn bản xử lý")
    st.text_area("Văn bản AI sẽ đọc thực tế (Đã bung từ viết tắt):", value=clean_text, height=200)
        
    if st.button("🚀 Xuất file MP3", type="primary"):
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{uploaded_file.name.split('.')[0]}_{timestamp}.mp3"
        
        with st.spinner(f"🤖 Bot đang tăng tốc giọng đọc lên x{speed}... Vui lòng đợi."):
            generate_audio_with_speed(clean_text, output_filename, speed_rate=speed)
            
        if os.path.exists(output_filename):
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
