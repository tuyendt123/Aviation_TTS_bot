from gtts import gTTS
import streamlit as st
import json
import re
import os
import time
from docx import Document

# Cấu hình giao diện Web
st.set_page_config(page_title="Aviation TTS Bot", page_icon="✈️", layout="centered")

DICT_FILE = "aviation_dict.json"

# Bảng tra cứu phiên âm các chữ cái viết hoa sang tiếng Anh để gTTS đọc chuẩn
ENGLISH_LETTERS = {
    'A': ' ây ', 'B': ' bi ', 'C': ' xi ', 'D': ' di ', 'E': ' i ', 
    'F': ' ép ', 'G': ' ji ', 'H': ' ét chơ ', 'I': ' ai ', 'J': ' jê ', 
    'K': ' cây ', 'L': ' eo ', 'M': ' em ', 'N': ' en ', 'O': ' ô ', 
    'P': ' pi ', 'Q': ' qui ', 'R': ' a ', 'S': ' ét ', 'T': ' ti ', 
    'U': ' u ', 'V': ' vi ', 'W': ' dáp liu ', 'X': ' ích ', 'Y': ' guai ', 'Z': ' jét '
}

# Danh sách từ tiếng Anh thông dụng nguyên cụm giữ nguyên cách đọc
COMMON_ENGLISH_WORDS = {
    'CHECK': 'check',
    'NO GO': 'nô gâu',
    'GO': 'gâu'
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

# 2. Hàm ghi file từ điển JSON khi người dùng thêm từ trên Web
def save_dictionary(dictionary, file_path=DICT_FILE):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=2)

# 3. Hàm lọc thông minh: Ưu tiên từ điển -> Từ thông dụng -> Ép ký tự hoa đọc tiếng Anh
def normalize_text(text, dictionary):
    if not text:
        return ""
    
    # Bước a: Dịch các thuật ngữ viết tắt theo file từ điển JSON trước (Ưu tiên số 1)
    sorted_keywords = sorted(dictionary.keys(), key=len, reverse=True)
    for kw in sorted_keywords:
        pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
        text = pattern.sub(dictionary[kw], text)
        
    # Bước b: Thay thế các cụm từ tiếng Anh nguyên bản thông dụng (Ưu tiên số 2)
    for word, pronunciation in COMMON_ENGLISH_WORDS.items():
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        text = pattern.sub(pronunciation, text)
        
    # Bước c: Quét tất cả chữ cái viết hoa (A-Z) để ép đọc theo tiếng Anh (Ví dụ: GPM, L, R)
    # Giữ nguyên số để gTTS đọc bằng tiếng Việt
    def replace_upper_char(match):
        char = match.group(0)
        return ENGLISH_LETTERS.get(char, char)
        
    text = re.sub(r'[A-Z]', replace_upper_char, text)
    
    # Bước d: Thu gọn khoảng trắng thừa để chuỗi văn bản mạch lạc
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 4. Hàm trích xuất toàn bộ văn bản từ file Word (.docx)
def extract_text_from_docx(file_bytes):
    doc = Document(file_bytes)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)

# 5. Hàm gọi Engine gTTS chuyển text thành file âm thanh MP3
def generate_audio_sync(text, output_path):
    if not text.strip():
        raise ValueError("Văn bản bị trống!")
    tts = gTTS(text=text, lang='vi', slow=False)
    tts.save(output_path)


# --- KHỞI TẠO BỘ NHỚ TẠM CHO TỪ ĐIỂN ---
if 'aviation_dict' not in st.session_state:
    st.session_state.aviation_dict = load_dictionary()


# --- GIAO DIỆN THANH BÊN (SIDEBAR) ---
st.sidebar.header("Cấu hình Giọng đọc AI")
st.sidebar.info("Hệ thống sử dụng Google TTS ổn định. Lựa chọn giọng đọc dưới đây chỉ áp dụng cho Edge-TTS (đã tạm ẩn).")

st.sidebar.markdown("---")

# ✨ KHU VỰC BỔ SUNG TỪ VIẾT TẮT TRỰC TIẾP TRÊN WEB
st.sidebar.subheader("➕ Thêm từ viết tắt nhanh")
new_key = st.sidebar.text_input("Từ viết tắt (Ví dụ: AOG):").strip()
new_value = st.sidebar.text_input("Cách đọc mong muốn (Ví dụ: ây ô gi tàu bay dừng):").strip()

if st.sidebar.button("Thêm vào từ điển", use_container_width=True):
    if new_key and new_value:
        # Cập nhật vào session_state và ghi trực tiếp vào file JSON trên server
        st.session_state.aviation_dict[new_key] = new_value
        save_dictionary(st.session_state.aviation_dict)
        st.sidebar.success(f"🎉 Đã thêm thành công: {new_key}")
        time.sleep(0.5)
        st.rerun()  # Làm mới trang để cập nhật từ điển lập tức
    else:
        st.sidebar.error("Vui lòng nhập đầy đủ cả 2 ô!")

# Hiển thị bảng từ điển hiện tại
with st.sidebar.expander("📝 Từ điển viết tắt đang áp dụng", expanded=True):
    st.json(st.session_state.aviation_dict)


# --- KHÔNG GIAN LÀM VIỆC CHÍNH ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống tự động chuyển đổi báo cáo Word chuyên ngành thành file âm thanh MP3.")

# Khu vực Upload file Word từ máy tính
uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Đã tải file lên thành công. Đang xử lý cấu trúc...")
    
    # Đọc text gốc từ file Word
    raw_text = extract_text_from_docx(uploaded_file)
    
    # Tiến hành dịch các thuật ngữ theo từ điển mới nhất trong session_state
    clean_text = normalize_text(raw_text, st.session_state.aviation_dict)
    
    # Hiển thị khu vực xem trước kết quả dịch chữ trước khi đọc
    st.subheader("Xem trước văn bản xử lý")
    st.text_area("Văn bản AI sẽ đọc thực tế (Đã bung từ viết tắt):", value=clean_text, height=200)
        
    # Nút bấm kích hoạt chuyển đổi
    if st.button("🚀 Xuất file MP3", type="primary"):
        # Thêm timestamp vào tên file tránh dính cache trình duyệt
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{uploaded_file.name.split('.')[0]}_{timestamp}.mp3"
        
        with st.spinner("🤖 Bot đang xử lý giọng đọc... Vui lòng đợi."):
            try:
                generate_audio_sync(clean_text, output_filename)
                
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
                    
                    # Dọn dẹp file tạm trên máy sau khi xử lý xong
                    os.remove(output_filename)
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {e}")
