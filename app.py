from gtts import gTTS
import streamlit as st
import json
import re
import os
import asyncio
from docx import Document
import edge_tts

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
    # Sắp xếp từ khóa dài trước, ngắn sau để tránh lỗi đè từ
    sorted_keywords = sorted(dictionary.keys(), key=len, reverse=True)
    for kw in sorted_keywords:
        # Dùng Regex với biên từ \b để thay thế chính xác cụm từ độc lập
        pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
        text = pattern.sub(dictionary[kw], text)
    return text

# 3. Hàm trích xuất toàn bộ văn bản từ file Word (.docx)
def extract_text_from_docx(file_bytes):
    doc = Document(file_bytes)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

# 4. Hàm gọi AI Engine để chuyển text thành file âm thanh MP3
def generate_audio_sync(text, output_path):
    if not text.strip():
        raise ValueError("Văn bản bị trống!")
    
    # Sử dụng Google TTS, ngôn ngữ tiếng Việt ('vi')
    tts = gTTS(text=text, lang='vi', slow=False)
    tts.save(output_path)

# --- GIAO DIỆN KHÔNG GIAN LÀM VIỆC ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống tự động chuyển đổi báo cáo Word chuyên ngành thành file âm thanh MP3.")

# Chọn giọng đọc ở thanh bên cạnh (Sidebar)
st.sidebar.header("Cấu hình Giọng đọc AI")
voice_option = st.sidebar.selectbox(
    "Chọn giọng đọc:",
    options=["vi-VN-HoaiAnNeural (Nữ miền Nam)", "vi-VN-NamMinhNeural (Nam miền Bắc)"],
    index=0
)
selected_voice = voice_option.split(" ")[0]

# Khởi tạo từ điển
aviation_dict = load_dictionary()
with st.sidebar.expander("📝 Từ điển viết tắt đang áp dụng"):
    st.json(aviation_dict)

# Khu vực Upload file Word từ máy tính
uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Đã tải file lên thành công. Đang xử lý cấu trúc...")
    
    # Đọc text gốc từ file Word
    raw_text = extract_text_from_docx(uploaded_file)
    
    # Tiến hành dịch các thuật ngữ viết tắt theo từ điển
    clean_text = normalize_text(raw_text, aviation_dict)
    
    # Hiển thị khu vực xem trước kết quả dịch chữ trước khi đọc
    st.subheader("Xem trước văn bản xử lý")
    st.text_area("Văn bản AI sẽ đọc thực tế (Đã bung từ viết tắt):", value=clean_text, height=200)
        
    # Nút bấm kích hoạt chuyển đổi
    if st.button("🚀 Xuất file MP3", type="primary"):
        output_filename = f"converted_{uploaded_file.name.split('.')[0]}.mp3"
        
        with st.spinner("🤖 Bot đang xử lý giọng đọc... Vui lòng đợi."):
            # Chạy tác vụ Async tạo file âm thanh
            generate_audio_sync(clean_text, output_filename)
            
        if os.path.exists(output_filename):
            st.balloons()
            st.success("🎉 Đã tạo xong file âm thanh!")
            
            # Trình phát nhạc nghe thử trực tiếp trên Web
            with open(output_filename, "rb") as audio_file:
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3")
                
                # Nút tải file MP3 về máy tính của bạn
                st.download_button(
                    label="📥 Tải file MP3 về máy",
                    data=audio_bytes,
                    file_name=output_filename,
                    mime="audio/mp3"
                )
            
            # Dọn dẹp file tạm trên máy sau khi xử lý xong
            os.remove(output_filename)