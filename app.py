import streamlit as st
import json
import re
import os
import time
import asyncio  # Thư viện bắt buộc để chạy luồng mã hóa của edge-tts
from docx import Document
import edge_tts

# Cấu hình giao diện Web
st.set_page_config(page_title="Aviation TTS Bot", page_icon="✈️", layout="centered")

# Đường dẫn file lưu từ điển trên server
DICT_FILE = "aviation_dict.json"

# Bảng tra cứu phiên âm CHỈ DÀNH CHO CHỮ CÁI tiếng Anh (Số giữ nguyên để đọc tiếng Việt)
ENGLISH_LETTERS_PHONETICS = {
    'A': ' ây ', 'B': ' bi ', 'C': ' xi ', 'D': ' di ', 'E': ' i ', 
    'F': ' ép ', 'G': ' ji ', 'H': ' ét chơ ', 'I': ' ai ', 'J': ' jê ', 
    'K': ' cây ', 'L': ' eo ', 'M': ' em ', 'N': ' en ', 'O': ' ô ', 
    'P': ' pi ', 'Q': ' qui ', 'R': ' a ', 'S': ' ét ', 'T': ' ti ', 
    'U': ' u ', 'V': ' vi ', 'W': ' dáp liu ', 'X': ' ích ', 'Y': ' guai ', 'Z': ' jét '
}

# 1. Hàm đọc file từ điển JSON
def load_dictionary(file_path=DICT_FILE):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

# 2. Hàm lưu từ điển mới (Khi thêm từ trực tiếp trên Web)
def save_dictionary(dictionary, file_path=DICT_FILE):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=2)

# 3. Hàm chuẩn hóa văn bản (Chỉ bung từ điển viết tắt chuyên ngành)
def normalize_text(text, dictionary):
    if not text:
        return ""
        
    # Dịch các thuật ngữ viết tắt theo file từ điển JSON trước (Ưu tiên số 1)
    sorted_keywords = sorted(dictionary.keys(), key=len, reverse=True)
    for kw in sorted_keywords:
        pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
        text = pattern.sub(dictionary[kw], text)
    
    # Gom khoảng trắng thừa để chuỗi văn bản mạch lạc
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 4. Hàm trích xuất toàn bộ văn bản từ file Word (.docx)
def extract_text_from_docx(file_bytes):
    doc = Document(file_bytes)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

# 5. CẤU TRÚC HÀM ASYNC GỌI ENGINE EDGE-TTS ÔN ĐỊNH 100%
async def generate_audio_async(text, output_path, voice, speed_rate):
    if not text.strip():
        raise ValueError("Văn bản bị trống!")
    
    # Cấu hình tốc độ đọc chuẩn phần trăm
    percentage = int(round((speed_rate - 1.0) * 100))
    speed_string = f"+{percentage}%" if percentage >= 0 else f"{percentage}%"
    
    # Để tránh Microsoft từ chối các chuỗi ký tự kỹ thuật hàng không (như GPM 5L), 
    # chúng ta làm sạch triệt để các ký tự lạ hoặc xuống dòng lỗi trong văn bản gốc
    clean_content = text.replace('\n', ' ').replace('\r', ' ')
    
    # Khởi tạo tiến trình kết nối an toàn
    communicate = edge_tts.Communicate(clean_content, voice, rate=speed_string)
    await communicate.save(output_path)

# --- KHỞI TẠO BỘ NHỚ TẠM CHO TỪ ĐIỂN ---
if 'aviation_dict' not in st.session_state:
    st.session_state.aviation_dict = load_dictionary()

# --- GIAO DIỆN THANH BÊN (SIDEBAR) ---
st.sidebar.header("Cấu hình Giọng đọc AI")

# Lựa chọn giọng đọc AI Neural cao cấp chuẩn vùng miền của Microsoft
voice_option = st.sidebar.selectbox(
    "Chọn giọng đọc:",
    options=["vi-VN-HoaiAnNeural (Nữ miền Nam)", "vi-VN-NamMinhNeural (Nam miền Bắc)"],
    index=0
)
selected_voice = voice_option.split(" ")[0]

# Thanh trượt cấu hình tốc độ (Mặc định để sẵn mốc 1.15 theo yêu cầu của bạn)
speed = st.sidebar.slider("Tốc độ đọc (Speed Rate):", min_value=1.0, max_value=1.5, value=1.15, step=0.05)

st.sidebar.markdown("---")

# Khu vực bổ sung từ viết tắt nhanh trực tiếp trên giao diện Web
st.sidebar.subheader("➕ Thêm từ viết tắt nhanh")
new_key = st.sidebar.text_input("Từ viết tắt (Ví dụ: MEL):").strip()
new_value = st.sidebar.text_input("Cách đọc hoàn chỉnh (Ví dụ: Minimum Equipment List):").strip()

if st.sidebar.button("Thêm vào từ điển", use_container_width=True):
    if new_key and new_value:
        st.session_state.aviation_dict[new_key] = new_value
        save_dictionary(st.session_state.aviation_dict)
        st.sidebar.success(f"🎉 Đã thêm thành công: {new_key}")
        time.sleep(1)
        st.rerun()
    else:
        st.sidebar.error("Vui lòng nhập đầy đủ cả 2 ô!")

with st.sidebar.expander("📝 Từ điển viết tắt đang áp dụng", expanded=False):
    st.json(st.session_state.aviation_dict)


# --- GIAO DIỆN KHÔNG GIAN LÀM VIỆC CHÍNH ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống tự động chuyển đổi báo cáo Word chuyên ngành thành file âm thanh MP3 AI Neural.")

uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Đã tải file lên thành công. Đang xử lý cấu trúc...")
    
    raw_text = extract_text_from_docx(uploaded_file)
    clean_text = normalize_text(raw_text, st.session_state.aviation_dict)
    
    st.subheader("Xem trước văn bản xử lý")
    st.text_area("Văn bản AI sẽ đọc thực tế (Đã bung từ viết tắt):", value=clean_text, height=200)
        
    if st.button("🚀 Xuất file MP3", type="primary"):
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{uploaded_file.name.split('.')[0]}_{timestamp}.mp3"
        
        with st.spinner("🤖 Bot AI Neural đang xử lý giọng đọc... Vui lòng đợi."):
            # ÉP CHẠY LUỒNG ASYNC TRÊN NỀN TẢNG STREAMLIT AN TOÀN
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
