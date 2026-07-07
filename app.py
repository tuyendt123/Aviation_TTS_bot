import streamlit as st
import json
import re
import os
import time
import asyncio
from docx import Document
import edge_tts

# Cấu hình giao diện Web
st.set_page_config(page_title="Aviation TTS Bot", page_icon="✈️", layout="centered")

# FILE_PATH lưu từ điển
DICT_FILE = "aviation_dict.json"

# 1. Hàm đọc file từ điển JSON
def load_dictionary(file_path=DICT_FILE):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

# 2. Hàm lưu từ điển mới (Dùng khi thêm từ trực tiếp trên Web)
def save_dictionary(dictionary, file_path=DICT_FILE):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=2)

# 3. Hàm chuẩn hóa văn bản
def normalize_text(text, dictionary):
    if not text:
        return ""
    sorted_keywords = sorted(dictionary.keys(), key=len, reverse=True)
    for kw in sorted_keywords:
        pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
        text = pattern.sub(dictionary[kw], text)
    return text

# 4. Hàm trích xuất toàn bộ văn bản từ file Word (.docx)
def extract_text_from_docx(file_bytes):
    doc = Document(file_bytes)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

# 5. Hàm Async gọi AI Edge-TTS Engine xuất file âm thanh chất lượng cao
async def generate_audio_async(text, output_path, voice, speed_rate):
    if not text.strip():
        raise ValueError("Văn bản bị trống!")
    speed_string = f"{speed_rate:.2f}x"
    communicate = edge_tts.Communicate(text, voice, rate=speed_string)
    await communicate.save(output_path)

# --- KHỞI TẠO DỮ LIỆU TỪ ĐIỂN ---
if 'aviation_dict' not in st.session_state:
    st.session_state.aviation_dict = load_dictionary()

# --- GIAO DIỆN THANH BÊN (SIDEBAR) ---
st.sidebar.header("Cấu hình Giọng đọc AI")

voice_option = st.sidebar.selectbox(
    "Chọn giọng đọc:",
    options=["vi-VN-HoaiAnNeural (Nữ miền Nam)", "vi-VN-NamMinhNeural (Nam miền Bắc)"],
    index=0
)
selected_voice = voice_option.split(" ")[0]
speed = st.sidebar.slider("Tốc độ đọc (Speed Rate):", min_value=1.0, max_value=1.5, value=1.15, step=0.05)

st.sidebar.markdown("---")

# ✨ KHU VỰC BỔ SUNG TỪ VIẾT TẮT TRỰC TIẾP
st.sidebar.subheader("➕ Thêm từ viết tắt nhanh")
new_key = st.sidebar.text_input("Từ viết tắt (Ví dụ: MEL):").strip()
new_value = st.sidebar.text_input("Cách đọc hoàn chỉnh (Ví dụ: Minimum Equipment List):").strip()

if st.sidebar.button("Thêm vào từ điển", use_container_width=True):
    if new_key and new_value:
        # Cập nhật vào bộ nhớ tạm session_state và lưu thẳng vào file JSON trên server
        st.session_state.aviation_dict[new_key] = new_value
        save_dictionary(st.session_state.aviation_dict)
        st.sidebar.success(f"🎉 Đã thêm thành công từ: {new_key}")
        time.sleep(1)
        st.rerun() # Tải lại trang để cập nhật từ điển ngay lập tức
    else:
        st.sidebar.error("Vui lòng nhập đầy đủ cả 2 ô!")

# Hiển thị bảng từ điển hiện tại
with st.sidebar.expander("📝 Từ điển viết tắt đang áp dụng", expanded=False):
    st.json(st.session_state.aviation_dict)


# --- GIAO DIỆN KHÔNG GIAN LÀM VIỆC CHÍNH ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống tự động chuyển đổi báo cáo Word chuyên ngành thành file âm thanh MP3 AI Neural.")

# Khu vực Upload file Word từ máy tính
uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Đã tải file lên thành công. Đang xử lý cấu trúc...")
    
    raw_text = extract_text_from_docx(uploaded_file)
    # Dùng từ điển cập nhật mới nhất để dịch
    clean_text = normalize_text(raw_text, st.session_state.aviation_dict)
    
    st.subheader("Xem trước văn bản xử lý")
    st.text_area("Văn bản AI sẽ đọc thực tế (Đã bung từ viết tắt):", value=clean_text, height=200)
        
    if st.button("🚀 Xuất file MP3", type="primary"):
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{uploaded_file.name.split('.')[0]}_{timestamp}.mp3"
        
        with st.spinner("🤖 Bot AI Neural đang xử lý giọng đọc... Vui lòng đợi."):
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
