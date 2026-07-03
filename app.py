import streamlit as st
import json
import re
import os
import time  # Thư viện xử lý thời gian chống cache âm thanh
from docx import Document
from gtts import gTTS

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

# 4. Hàm đồng bộ chuyển đổi text thành file âm thanh MP3 bằng gTTS
def generate_audio_sync(text, output_path):
    if not text.strip():
        raise ValueError("Văn bản bị trống!")
    tts = gTTS(text=text, lang='vi', slow=False)
    tts.save(output_path)

# --- GIAO DIỆN KHÔNG GIAN LÀM VIỆC ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống tự động dịch thuật ngữ viết tắt và xuất báo cáo Word sang file MP3.")

# Khởi tạo từ điển
aviation_dict = load_dictionary()
with st.sidebar.expander("📝 Từ điển viết tắt đang áp dụng", expanded=True):
    st.json(aviation_dict)

# Khu vực Upload file Word từ máy tính
uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.info("Đang xử lý cấu trúc file...")
    raw_text = extract_text_from_docx(uploaded_file)
    clean_text = normalize_text(raw_text, aviation_dict)
    
    st.subheader("Xem trước văn bản xử lý")
    st.text_area("Văn bản AI sẽ đọc thực tế (Đã bung từ viết tắt):", value=clean_text, height=200)
        
    if st.button("🚀 Xuất file MP3", type="primary"):
        # Tạo mã thời gian dạng GiờPhútGiây để tên file luôn luôn mới tinh khi bấm nút
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{uploaded_file.name.split('.')[0]}_{timestamp}.mp3"
        
        with st.spinner("🤖 Bot đang xử lý giọng đọc... Vui lòng đợi."):
            generate_audio_sync(clean_text, output_filename)
            
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
            # Xóa file tạm trên máy chủ sau khi xuất để bảo mật dữ liệu
            os.remove(output_filename)
