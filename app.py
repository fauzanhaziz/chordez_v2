import streamlit as st
from google import genai
import tempfile
import os
import re
from pymongo import MongoClient

st.set_page_config(page_title="Chordez - AI Chord Tracker", page_icon="🎸", layout="wide")

# CSS styling - terminal/hacker dark green aesthetic
st.markdown("""
<style>
    body, .stApp { background-color: #0a0a0a; color: #00ff00; }
    .stSelectbox label, .stFileUploader label { color: #00ff00 !important; }
    .chord-display {
        background-color: #0a0a0a;
        padding: 30px;
        border-radius: 8px;
        border: 1px solid #333;
        font-family: 'Courier New', Courier, monospace;
        font-size: 15px;
        font-weight: bold;
        line-height: 1.6;
        white-space: pre;
        overflow-x: auto;
    }
    .chord-line { color: #00ff00; }
    .lyric-line { color: #cccccc; }
    .section-header { color: #ffaa00; }
    .capo-info { color: #00ff00; font-weight: bold; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🎸 Chordez: Smart Chord Tracker AI")

# API Key dari secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ API Key tidak ditemukan! Pastikan sudah mengatur secrets.toml atau Secrets di Streamlit Cloud.")
    api_key = ""

# ==========================================
# SETUP MONGODB (MEMORI AGENT)
# ==========================================
@st.cache_resource
def init_connection():
    # URL sesuai dengan setup Docker kita sebelumnya
    return MongoClient("mongodb://admin:rahasia123@localhost:27017/")

try:
    mongo_client = init_connection()
    db = mongo_client["chordez_db"]
    history_collection = db["transcriptions"]
    st.sidebar.success("✅ Memori AI (MongoDB): Aktif")
except Exception as e:
    st.sidebar.error(f"❌ Memori AI (MongoDB): Terputus. Error: {e}")
    history_collection = None

col1, col2 = st.columns(2)
with col1:
    instrument = st.selectbox("Alat Musik:", ["Gitar", "Piano", "Ukulele"])
with col2:
    nada_dasar = st.selectbox("Sesuaikan Chord:", [
        "Sesuai Audio Asli",
        "Naikkan 1 Nada (+1)",
        "Turunkan 1 Nada (-1)",
        "Ubah ke Nada Dasar C"
    ])

uploaded_file = st.file_uploader("Pilih file audio", type=['mp3', 'wav'])

if uploaded_file is not None:
    st.audio(uploaded_file, format='audio/mp3')

    if st.button("🎵 Deteksi & Buat Lirik Chord!"):
        if not api_key:
            st.error("⚠️ API Key tidak ditemukan.")
        else:
            try:
                client = genai.Client(api_key=api_key)

                with st.spinner('🤖 AI sedang mendeteksi chord dan lirik...'):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                        temp_file.write(uploaded_file.read())
                        temp_path = temp_file.name

                    audio_file = client.files.upload(file=temp_path)

                    # =====================================================
                    # PROMPT YANG DIPERBAIKI
                    # Kunci: chord harus diposisikan TEPAT di atas suku kata
                    # menggunakan spasi sebagai padding horizontal
                    # =====================================================
                    prompt = f"""
Kamu adalah transcriber chord profesional. Tugasmu: transkripsi chord + lirik dari audio ini.

FORMAT WAJIB (TIDAK BOLEH DILANGGAR):
- Chord ditulis di BARIS ATAS, lirik di BARIS BAWAH
- Chord harus diposisikan TEPAT di atas suku kata yang dinyanyikan menggunakan SPASI sebagai padding
- Gunakan font monospace, jadi 1 spasi = 1 karakter
- Setiap section diberi header dalam kurung siku: [Intro], [Verse 1], [Chorus], dll
- Jika ada Capo, tuliskan di baris paling atas: "Capo ♩ fret X"
- JANGAN gunakan markdown, code block, atau simbol lain
- Instrumen: {instrument}, Nada: {nada_dasar}

CONTOH FORMAT YANG HARUS DITIRU PERSIS:
(perhatikan bahwa chord C, E, F posisinya tepat di atas suku kata yang sesuai)

Capo ♩ fret 2

[Intro]
C..E F (4x)

[Verse 1]
C              E      F
saat.. engkau ter..tidur..
C              E      F
aku.. pergi meng..hibur..
  C
beda kota pisah raga
  E      F
bukan masalahku
  C
lihat wajahmu di layar
  E      F
ku tetap bersyukur

[Chorus]
C              E      F
saat.. engkau ter..jaga..

ATURAN POSISI CHORD:
- Hitung posisi karakter dari kiri (mulai dari 0)
- Letakkan nama chord tepat pada posisi karakter dimana suku kata itu dimulai
- Gunakan spasi untuk mengisi jarak antar chord
- Chord 2 karakter (Am, Em) dan 1 karakter (C, G) dihitung sesuai lebar namanya

Mulai transkripsi sekarang:
"""

                    # Daftar model fallback — dicoba berurutan jika 503
                    MODEL_LIST = [
                        'gemini-2.5-flash',
                        'gemini-2.0-flash',
                        'gemini-1.5-flash',
                    ]

                    response = None
                    last_error = None
                    for model_name in MODEL_LIST:
                        try:
                            st.info(f"⏳ Mencoba model: `{model_name}`...")
                            response = client.models.generate_content(
                                model=model_name,
                                contents=[prompt, audio_file]
                            )
                            st.info(f"✅ Berhasil dengan model: `{model_name}`")
                            break  # sukses, keluar dari loop
                        except Exception as model_err:
                            err_str = str(model_err)
                            if '503' in err_str or 'UNAVAILABLE' in err_str or 'high demand' in err_str.lower():
                                last_error = model_err
                                continue  # coba model berikutnya
                            else:
                                raise  # error lain, langsung lempar

                    if response is None:
                        raise Exception(
                            f"Semua model sedang tidak tersedia (503). Coba lagi beberapa menit. "
                            f"Error terakhir: {last_error}"
                        )

                    raw_text = response.text.strip()

                    # Bersihkan markdown jika ada
                    raw_text = re.sub(r'```[a-z]*\n?', '', raw_text)
                    raw_text = raw_text.replace('```', '').strip()

                    st.success("✅ Selesai! Chord sudah diposisikan di atas lirik:")

                    # =====================================================
                    # RENDERING: Warnai baris chord vs lirik vs header
                    # =====================================================
                    lines = raw_text.split('\n')
                    
                    # Deteksi apakah suatu baris adalah baris chord
                    # Baris chord biasanya berisi: huruf A-G, m, 7, /, #, b, spasi, angka
                    # dan TIDAK mengandung banyak huruf kecil berurutan (bukan lirik)
                    def is_chord_line(line):
                        stripped = line.strip()
                        if not stripped:
                            return False
                        if stripped.startswith('[') and stripped.endswith(']'):
                            return False  # section header
                        # Chord line: mayoritas token adalah nama chord valid
                        tokens = stripped.split()
                        chord_pattern = re.compile(
                            r'^[A-G](#|b)?(m|maj|min|sus|aug|dim|add)?[0-9]?(\/[A-G](#|b)?)?$'
                        )
                        chord_count = sum(1 for t in tokens if chord_pattern.match(t))
                        # Jika lebih dari 50% token adalah chord, ini baris chord
                        return len(tokens) > 0 and chord_count / len(tokens) >= 0.5

                    html_lines = []
                    for line in lines:
                        stripped = line.strip()
                        if not stripped:
                            html_lines.append('')
                        elif stripped.startswith('[') and stripped.endswith(']'):
                            # Section header - warna kuning/orange
                            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            html_lines.append(f'<span style="color:#ffaa00">{escaped}</span>')
                        elif stripped.lower().startswith('capo'):
                            # Capo info
                            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            html_lines.append(f'<span style="color:#00ff00;font-weight:bold">{escaped}</span>')
                        elif is_chord_line(line):
                            # Baris chord - hijau terang
                            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            html_lines.append(f'<span style="color:#00ff00">{escaped}</span>')
                        else:
                            # Baris lirik - putih/abu
                            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            html_lines.append(f'<span style="color:#cccccc">{escaped}</span>')

                    html_content = '\n'.join(html_lines)

                    st.markdown(f'''
                        <div class="chord-display">{html_content}</div>
                    ''', unsafe_allow_html=True)

                    # Tampilkan juga versi plain text untuk copy-paste
                    with st.expander("📋 Salin sebagai teks biasa"):
                        st.code(raw_text, language=None)

                    # Cleanup
                    client.files.delete(name=audio_file.name)
                    os.remove(temp_path)

            except Exception as e:
                st.error(f"❌ Terjadi kesalahan: {e}")