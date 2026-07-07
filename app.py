import streamlit as st
import os
import time
from docx import Document
from gtts import gTTS

# Cấu hình giao diện Web
st.set_page_config(page_title="Aviation TTS Bot", page_icon="✈️", layout="centered")

# 1. Hàm trích xuất văn bản từ file Word (.docx)
def extract_text_from_docx(file_bytes):
    doc = Document(file_bytes)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

# 2. Hàm gọi Engine gTTS chuyển text thành file âm thanh MP3
def save_audio_gtts(text, output_path):
    if not text.strip():
        raise ValueError("Văn bản bị trống!")
    # Sử dụng ngôn ngữ tiếng Việt mặc định của Google
    tts = gTTS(text=text, lang='vi', slow=False)
    tts.save(output_path)


# --- GIAO DIỆN CHÍNH ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống chuyển đổi báo cáo Word thành file âm thanh MP3 (Bản gTTS ổn định vĩnh viễn).")

# Khu vực Upload file
uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Đã tải file lên thành công.")
    
    # Đọc văn bản thô từ file Word
    raw_text = extract_text_from_docx(uploaded_file)
    
    st.subheader("Xem trước văn bản xử lý")
    clean_text = st.text_area("Nội dung AI sẽ đọc:", value=raw_text, height=200)
        
    if st.button("🚀 Xuất file MP3", type="primary"):
        # Tạo tên file duy nhất bằng timestamp để tránh trùng bộ nhớ đệm
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{timestamp}.mp3"
        
        with st.spinner("🤖 Google TTS đang xử lý giọng đọc..."):
            try:
                # Gọi hàm đồng bộ đơn giản của Google
                save_audio_gtts(clean_text, output_filename)
                
                if os.path.exists(output_filename):
                    st.balloons()
                    st.success("🎉 Đã tạo xong file âm thanh!")
                    
                    # Phát và cho tải file trực tiếp trên trình duyệt
                    with open(output_filename, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            label="📥 Tải file MP3 về máy",
                            data=audio_bytes,
                            file_name=f"report_{timestamp}.mp3",
                            mime="audio/mp3"
                        )
                    
                    # Xóa file tạm để giải phóng RAM cho server
                    os.remove(output_filename)
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {e}")
