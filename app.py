import streamlit as st
import os
import time
import re
from docx import Document
from gtts import gTTS

# Cấu hình giao diện Web
st.set_page_config(page_title="Aviation TTS Bot", page_icon="✈️", layout="centered")

# Bảng tra cứu phiên âm các chữ cái viết hoa sang tiếng Anh để gTTS đọc chuẩn
ENGLISH_LETTERS = {
    'A': ' ây ', 'B': ' bi ', 'C': ' xi ', 'D': ' di ', 'E': ' i ', 
    'F': ' ép ', 'G': ' ji ', 'H': ' ét chơ ', 'I': ' ai ', 'J': ' jê ', 
    'K': ' cây ', 'L': ' eo ', 'M': ' em ', 'N': ' en ', 'O': ' ô ', 
    'P': ' pi ', 'Q': ' qui ', 'R': ' a ', 'S': ' ét ', 'T': ' ti ', 
    'U': ' u ', 'V': ' vi ', 'W': ' dáp liu ', 'X': ' ích ', 'Y': ' guai ', 'Z': ' jét '
}

# Danh sách từ tiếng Anh thông dụng nguyên cụm giữ nguyên cách đọc (Không bị tách chữ cái)
COMMON_ENGLISH_WORDS = {
    'CHECK': 'check',
    'NO GO': 'nô gâu',
    'GO': 'gâu'
}

# 1. Hàm trích xuất văn bản từ file Word (.docx)
def extract_text_from_docx(file_bytes):
    doc = Document(file_bytes)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

# 2. Hàm lọc thông minh: Giữ từ tiếng Anh thông dụng, ép các chữ in hoa đơn lẻ đọc theo tiếng Anh
def clean_and_normalize(text):
    if not text:
        return ""
    
    # Bước a: Thay thế các cụm từ tiếng Anh nguyên bản thông dụng trước (Ưu tiên số 1)
    for word, pronunciation in COMMON_ENGLISH_WORDS.items():
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        text = pattern.sub(pronunciation, text)
        
    # Bước b: Quét tất cả chữ cái viết hoa (A-Z) đơn lẻ còn lại để ép đọc theo tiếng Anh (Ví dụ: GPM, L, R)
    def replace_upper_char(match):
        char = match.group(0)
        return ENGLISH_LETTERS.get(char, char)
        
    text = re.sub(r'[A-Z]', replace_upper_char, text)
    
    # Bước c: Thu gọn khoảng trắng thừa để chuỗi văn bản mạch lạc
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 3. Hàm gọi Engine gTTS chuyển text thành file âm thanh MP3
def save_audio_gtts(text, output_path):
    if not text.strip():
        raise ValueError("Văn bản bị trống!")
    tts = gTTS(text=text, lang='vi', slow=False)
    tts.save(output_path)


# --- GIAO DIỆN CHÍNH ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống chuyển đổi báo cáo Word thành file âm thanh MP3 (Bản gTTS tối giản thông minh).")

uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Đã tải file lên thành công.")
    
    # Đọc văn bản thô
    raw_text = extract_text_from_docx(uploaded_file)
    
    # Xử lý ngôn ngữ thông minh
    processed_text = clean_and_normalize(raw_text)
    
    st.subheader("Xem trước văn bản xử lý")
    clean_text = st.text_area("Nội dung AI sẽ đọc thực tế:", value=processed_text, height=200)
        
    if st.button("🚀 Xuất file MP3", type="primary"):
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{timestamp}.mp3"
        
        with st.spinner("🤖 Google TTS đang xử lý giọng đọc..."):
            try:
                save_audio_gtts(clean_text, output_filename)
                
                if os.path.exists(output_filename):
                    st.balloons()
                    st.success("🎉 Đã tạo xong file âm thanh!")
                    
                    with open(output_filename, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            label="📥 Tải file MP3 về máy",
                            data=audio_bytes,
                            file_name=f"report_{timestamp}.mp3",
                            mime="audio/mp3"
                        )
                    
                    os.remove(output_filename)
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {e}")
