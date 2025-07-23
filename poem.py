import streamlit as st
import fitz  # PyMuPDF
import os, re, tempfile
from deep_translator import GoogleTranslator
from gtts import gTTS
import google.generativeai as genai
from dotenv import load_dotenv

# ============ Gemini setup ============
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# ============ Helper Functions ============
def pdf_text(path_or_bytes):
    text = ""
    with (fitz.open(path_or_bytes) if isinstance(path_or_bytes, str)
          else fitz.open(stream=path_or_bytes.read(), filetype="pdf")) as doc:
        for page in doc:
            text += page.get_text()
    return text

def clean_block(raw_block: str) -> str:
    lines = [ln.strip() for ln in raw_block.splitlines() if ln.strip()]
    lines = [ln for ln in lines if len(ln) < 120 and 'http' not in ln.lower()]
    return "\n".join(lines)

def extract_poem(text, title):
    pattern = re.compile(re.escape(title), re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    after = text[match.end():].splitlines()
    stanza = []
    for ln in after:
        if ln.strip() == "" and stanza:
            break
        if ln.strip():
            stanza.append(ln.strip())
    return clean_block("\n".join(stanza))

def tts_mp3(text, lang_code):
    try:
        tts = gTTS(text, lang=lang_code)
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(f.name)
        return f.name
    except:
        return None

# ============ Streamlit UI ============
st.set_page_config(page_title="🎤 Poem Generator", layout="centered")
st.markdown("""
    <h1 style='color:#00c6ff;text-align:center;'>🎤 Multilingual Poem Generator with Voice</h1>
    <p style='text-align:center;'>Made by <b>Farya Saleem</b></p><hr>
    """, unsafe_allow_html=True)

# Built-in PDF
BUILTIN = "Nursery_Rhyme_Charts.pdf"
if not os.path.exists(BUILTIN):
    st.error(f"Missing built-in file: {BUILTIN}")

# Upload user PDF
user_pdf = st.file_uploader("📄 Upload your own PDF (optional)", type="pdf", key="upload")

# Language Selector
lang_map = {
    "English": "en", "Urdu": "ur", "Hindi": "hi", "Spanish": "es",
    "French": "fr", "German": "de", "Arabic": "ar", "Chinese": "zh-cn",
    "Russian": "ru", "Italian": "it"
}
lang_name = st.selectbox("🌍 Choose language for translation & voice", list(lang_map.keys()))
lang_code = lang_map[lang_name]

# Poem title input
title = st.text_input("✏️ Enter Poem Title", key="poem_title")

# Buttons
col1, col2 = st.columns([1, 1])
generate = col1.button("🔍 Find or Generate Poem")
clear = col2.button("🧹 Clear All")

# ============ Action Buttons ============
if generate:
    if not title.strip():
        st.warning("Please enter a poem title.")
        st.stop()

    texts = []
    if os.path.exists(BUILTIN):
        texts.append(pdf_text(BUILTIN))
    if user_pdf:
        texts.append(pdf_text(user_pdf))

    combined = "\n".join(texts)
    poem = extract_poem(combined, title)

    if poem:
        st.success("✅ Poem found in PDF!")
    else:
        st.info("Not found in PDFs — generating with AI…")
        try:
            prompt = f"Write a short children's poem titled '{title}'"
            poem = model.generate_content(prompt).text.strip()
        except Exception as e:
            st.error(f"AI error: {e}")
            poem = None

    if poem:
        st.markdown("### 📜 Poem:")
        st.text_area("Original", poem, height=180, key="poem_display")

        try:
            translated = GoogleTranslator(source="auto", target=lang_code).translate(poem)
        except Exception as e:
            st.warning(f"Translation failed: {e}")
            translated = poem

        st.markdown(f"### 🌍 Translated ({lang_name}):")
        st.text_area("Translation", translated, height=180, key="trans_display")

        audio_fp = tts_mp3(translated, lang_code)
        if audio_fp:
            st.audio(audio_fp, format="audio/mp3")
        else:
            st.warning("Voice not available for this language.")

# ============ Clear All ============
if clear:
    st.session_state.clear()
    st.rerun()  