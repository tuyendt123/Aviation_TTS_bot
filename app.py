from gtts import gTTS
import streamlit as st
import json
import re
import os
import asyncio
from docx import Document
import gtts

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

# 3. Hàm lọc thông minh: Ưu tiên từ điển tuyệt đối -> Tách chữ/số tách biệt -> Ép chữ cái đọc tiếng Anh
def normalize_text(text, dictionary):
    if not text:
        return ""
    
    # Bước a: Bung từ viết tắt từ JSON trước (Ưu tiên số 1 - giữ nguyên khối để dịch chuẩn)
    sorted_keywords = sorted(dictionary.keys(), key=len, reverse=True)
    for kw in sorted_keywords:
        # Thay thế ranh giới \b bằng regex linh hoạt để ăn khớp cả ký tự đặc biệt (/, -)
        pattern = re.compile(r'(?<![A-Za-z0-9])' + re.escape(kw) + r'(?![A-Za-z0-9])', re.IGNORECASE)
        text = pattern.sub(dictionary[kw], text)
        
    # Bước b: Thay thế các cụm từ tiếng Anh nguyên bản thông dụng (Ưu tiên số 2)
    for word, pronunciation in COMMON_ENGLISH_WORDS.items():
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        text = pattern.sub(pronunciation, text)

    # 🔥 Bước c: TỰ ĐỘNG HÓA TÁCH CHỮ VÀ SỐ (Ví dụ: VN1039 -> VN 1 0 3 9, A320 -> A 3 2 0)
    # Thêm khoảng trắng giữa Chữ và Số
    text = re.sub(r'([A-Za-z])(?=\d)', r'\1 ', text)
    text = re.sub(r'(\d)(?=[A-Za-z])', r'\1 ', text)
    # Rã rời các chữ số dính liền nhau thành từng số đơn lẻ
    text = re.sub(r'(?<=\d)(?=\d)', ' ', text)
        
    # Bước d: Ép đọc tiếng Anh cho từng ký tự viết hoa không phải tiếng Việt
    words = text.split()
    for i, word in enumerate(words):
        # Chỉ rã chữ đọc tiếng Anh cho các từ thuần ký tự Latinh/số không chứa dấu tiếng Việt
        if re.match(r'^[A-Za-z0-9\-_/]+$', word):
            phonetic_word = ""
            for char in word:
                upper_char = char.upper()
                if upper_char in ENGLISH_LETTERS:
                    phonetic_word += ENGLISH_LETTERS[upper_char]
                else:
                    phonetic_word += char
            words[i] = phonetic_word
            
    text = " ".join(words)
    
    # Bước e: Thu gọn khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 4. Hàm trích xuất toàn bộ văn bản từ file Word (.docx) - ĐÃ SỬA LỖI TRÔI CON TRỎ FILE
def extract_text_from_docx(file_bytes):
    try:
        # Ép con trỏ đọc file quay về vị trí 0 (đầu file) để tránh bị đọc chuỗi rỗng khi rerun
        file_bytes.seek(0)
        
        file_stream = io.BytesIO(file_bytes.read())
        doc = Document(file_stream)
    except AttributeError:
        doc = Document(file_bytes)
        
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

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
