import streamlit as st
import os
import time
import asyncio
from docx import Document
import edge_tts

# Cấu hình giao diện Web
st.set_page_config(page_title="Aviation TTS Bot", page_icon="✈️", layout="centered")

# 1. Hàm trích xuất văn bản từ file Word (.docx)
def extract_text_from_docx(file_bytes):
    doc = Document(file_bytes)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

# 2. Hàm Async tối giản để gọi Edge-TTS tải file âm thanh về
async def save_audio(text, output_path, voice, speed_string):
    communicate = edge_tts.Communicate(text, voice, rate=speed_string)
    await communicate.save(output_path)


# --- GIAO DIỆN CHÍNH ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống chuyển đổi báo cáo Word thành file âm thanh MP3 AI Neural (Bản tối giản).")

# Thanh bên cấu hình
st.sidebar.header("Cấu hình Giọng đọc")
voice_option = st.sidebar.selectbox(
    "Chọn giọng đọc:",
    options=["vi-VN-HoaiAnNeural (Nữ miền Nam)", "vi-VN-NamMinhNeural (Nam miền Bắc)"],
    index=0
)
selected_voice = voice_option.split(" ")[0]

# Thanh chọn tốc độ dạng Phần trăm chuẩn của Edge-TTS
speed_percent = st.sidebar.slider("Tốc độ tăng thêm (%):", min_value=0, max_value=50, value=15, step=5)
speed_param = f"+{speed_percent}%"

# Khu vực Upload file
uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Đã tải file lên thành công.")
    
    # Đọc văn bản thô
    raw_text = extract_text_from_docx(uploaded_file)
    
    st.subheader("Xem trước văn bản xử lý")
    clean_text = st.text_area("Nội dung AI sẽ đọc:", value=raw_text, height=200)
        
    if st.button("🚀 Xuất file MP3", type="primary"):
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{timestamp}.mp3"
        
        with st.spinner("🤖 Đang xử lý giọng đọc..."):
            try:
                # Chạy luồng tải âm thanh trực tiếp và đóng luồng ngay sau khi xong
                asyncio.run(save_audio(clean_text, output_filename, selected_voice, speed_param))
                
                if os.path.exists(output_filename):
                    st.balloons()
                    st.success("🎉 Đã tạo xong file âm thanh!")
                    
                    # Phát và cho tải file
                    with open(output_filename, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            label="📥 Tải file MP3 về máy",
                            data=audio_bytes,
                            file_name=f"report_{timestamp}.mp3",
                            mime="audio/mp3"
                        )
                    
                    # Xóa file tạm
                    os.remove(output_filename)
            except Exception as e:
                st.error(f"Có lỗi xảy ra trong quá trình kết nối AI: {e}")
