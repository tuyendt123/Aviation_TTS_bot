import streamlit as st
import json
import re
import os
import time
from docx import Document
from gtts import gTTS

# Cấu hình giao diện Web
st.set_page_config(page_title="Aviation TTS Bot", page_icon="✈️", layout="centered")

# Đường dẫn file lưu từ điển trên server
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

# 2. Hàm lưu từ điển mới (Khi người dùng bấm thêm từ trên giao diện Web)
def save_dictionary(dictionary, file_path=DICT_FILE):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=2)

# Bảng tra cứu phiên âm CHỈ DÀNH CHO CHỮ CÁI tiếng Anh (Đã loại bỏ chữ số)
ENGLISH_LETTERS_PHONETICS = {
    'A': ' ây ', 'B': ' bi ', 'C': ' xi ', 'D': ' di ', 'E': ' i ', 
    'F': ' ép ', 'G': ' ji ', 'H': ' ét chơ ', 'I': ' ai ', 'J': ' jê ', 
    'K': ' cây ', 'L': ' eo ', 'M': ' em ', 'N': ' en ', 'O': ' ô ', 
    'P': ' pi ', 'Q': ' qui ', 'R': ' a ', 'S': ' ét ', 'T': ' ti ', 
    'U': ' u ', 'V': ' vi ', 'W': ' dáp liu ', 'X': ' ích ', 'Y': ' guai ', 'Z': ' jét '
}

# 3. Hàm chuẩn hóa văn bản (Chữ đọc tiếng Anh, Số đọc tiếng Việt)
def normalize_text(text, dictionary):
    if not text:
        return ""
        
    # Bước a: Dịch các thuật ngữ viết tắt theo file từ điển JSON trước (Ưu tiên số 1)
    sorted_keywords = sorted(dictionary.keys(), key=len, reverse=True)
    for kw in sorted_keywords:
        pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
        text = pattern.sub(dictionary[kw], text)
    
    # Bước b: Tự động quét các từ viết tắt hoặc cụm chứa chữ viết hoa (Ví dụ: GPM, 5L, A320)
    words = text.split()
    for i, word in enumerate(words):
        # Kiểm tra xem từ đó có chứa ít nhất một chữ viết hoa hay không
        if any(char.isupper() for char in word):
            phonetic_word = ""
            for char in word:
                upper_char = char.upper()
                # TÁCH BIỆT: Nếu là chữ cái viết hoa -> Đổi sang phiên âm tiếng Anh
                if upper_char in ENGLISH_LETTERS_PHONETICS:
                    phonetic_word += ENGLISH_LETTERS_PHONETICS[upper_char]
                # TÁCH BIỆT: Nếu là số hoặc dấu câu -> Giữ nguyên để gTTS đọc tiếng Việt
                else:
                    phonetic_word += char
                    
            words[i] = phonetic_word
            
    return " ".join(words)

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
st.sidebar.info("Hệ thống đang sử dụng công cụ gTTS (Google Text-to-Speech) mặc định.")

st.sidebar.markdown("---")

# ✨ KHU VỰC BỔ SUNG TỪ VIẾT TẮT TRỰC TIẾP TRÊN WEB
st.sidebar.subheader("➕ Thêm từ viết tắt nhanh")
new_key = st.sidebar.text_input("Từ viết tắt (Ví dụ: MEL):").strip()
new_value = st.sidebar.text_input("Cách đọc hoàn chỉnh (Ví dụ: Minimum Equipment List):").strip()

if st.sidebar.button("Thêm vào từ điển", use_container_width=True):
    if new_key and new_value:
        # Cập nhật vào bộ nhớ tạm session_state và ghi trực tiếp vào file JSON trên server
        st.session_state.aviation_dict[new_key] = new_value
        save_dictionary(st.session_state.aviation_dict)
        st.sidebar.success(f"🎉 Đã thêm thành công: {new_key}")
        time.sleep(1)
        st.rerun()  # Làm mới trang để cập nhật từ điển ngay lập tức
    else:
        st.sidebar.error("Vui lòng nhập đầy đủ cả 2 ô!")

# Hiển thị bảng từ điển hiện tại cho người dùng theo dõi
with st.sidebar.expander("📝 Từ điển viết tắt đang áp dụng", expanded=True):
    st.json(st.session_state.aviation_dict)

# --- GIAO DIỆN KHÔNG GIAN LÀM VIỆC CHÍNH ---
st.title("✈️ Aviation Report-to-Voice Converter")
st.write("Hệ thống tự động chuyển đổi báo cáo Word chuyên ngành thành file âm thanh MP3.")

# Khu vực Upload file Word từ máy tính
uploaded_file = st.file_uploader("Tải lên file báo cáo Word (.docx)", type=["docx"])

if uploaded_file is not None:
    st.success("Đã tải file lên thành công. Đang xử lý cấu trúc...")
    
    # Đọc text gốc từ file Word
    raw_text = extract_text_from_docx(uploaded_file)
    
    # Tiến hành dịch các thuật ngữ viết tắt theo từ điển mới nhất
    clean_text = normalize_text(raw_text, st.session_state.aviation_dict)
    
    st.subheader("Xem trước văn bản xử lý")
    st.text_area("Văn bản AI sẽ đọc thực tế (Đã bung từ viết tắt):", value=clean_text, height=200)
        
    # Nút bấm kích hoạt chuyển đổi
    if st.button("🚀 Xuất file MP3", type="primary"):
        # Chèn timestamp tạo tên file duy nhất, tránh lỗi bộ nhớ đệm (cache) của trình duyệt
        timestamp = time.strftime("%H%M%S")
        output_filename = f"converted_{uploaded_file.name.split('.')[0]}_{timestamp}.mp3"
        
        with st.spinner("🤖 Bot đang xử lý giọng đọc... Vui lòng đợi."):
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
            
            # Khử file tạm sau khi hiển thị để giải phóng bộ nhớ hệ thống
            os.remove(output_filename)
