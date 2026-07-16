from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from google import genai
import tempfile
import os
import re
from datetime import datetime
import time
from dotenv import load_dotenv

# Inisialisasi Aplikasi Backend
app = FastAPI(title="Chordez API")

# Konfigurasi CORS (PENTING!)
# Agar Next.js (port 3000) diizinkan mengakses API Python (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Izinkan request dari Next.js lokal
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# SETUP MONGODB & GEMINI
# ==========================================
# 1. Panggil load_dotenv() di awal
load_dotenv() 

# 2. Ambil key-nya dari variabel lingkungan
API_KEY = os.getenv("GEMINI_API_KEY")

# 3. Validasi keamanan (agar program langsung mati jika key tidak ditemukan)
if not API_KEY:
    raise ValueError("GEMINI_API_KEY belum diatur di file .env!")

# 4. Inisialisasi client
client_genai = genai.Client(api_key=API_KEY)

# Koneksi MongoDB
try:
    # UBAH DISINI: localhost diganti jadi database
    mongo_client = MongoClient("mongodb://admin:rahasia123@database:27017/")
    db = mongo_client["chordez_db"]
    history_collection = db["transcriptions"]
    print("✅ Database MongoDB: Online")
except Exception as e:
    print(f"❌ Database Error: {e}")
    history_collection = None

# ==========================================
# ENDPOINT API UNTUK NEXT.JS
# ==========================================
@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    instrument: str = Form(...),
    nada_dasar: str = Form(...)
):
    try:
        # AGENT LOGIC 1: Cek Memori (MongoDB)
        query_pencarian = {
            "file_name": file.filename,
            "instrument": instrument,
            "nada_dasar": nada_dasar
        }
        
        if history_collection is not None:
            data_ditemukan = history_collection.find_one(query_pencarian)
            if data_ditemukan:
                print("⚡ Mengambil dari database...")
                return {
                    "status": "success",
                    "source": "database",
                    "data": data_ditemukan["chord_lyric"]
                }
        
        # AGENT LOGIC 2: Jika belum ada, panggil Gemini
        print("🤖 AI sedang memproses audio baru...")
        
        # Simpan file upload sementara
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Upload ke Gemini
        print("📤 Mengunggah audio ke server AI...")
        audio_file = client_genai.files.upload(file=temp_path)
        
        # Tambahkan jeda tunggu sampai file selesai diproses oleh Google
        while audio_file.state.name == "PROCESSING":
            print("⏳ Menunggu AI memproses file audio...")
            time.sleep(2)
            audio_file = client_genai.files.get(name=audio_file.name)
        
        prompt = f"""
Kamu adalah transcriber chord profesional. Tugasmu: transkripsi chord + lirik dari audio ini.
FORMAT WAJIB:
- Chord di BARIS ATAS, lirik di BARIS BAWAH
- Posisikan chord TEPAT di atas suku kata
- Gunakan spasi untuk padding
- Setiap section ada header [Intro], [Verse], dll
Instrumen: {instrument}, Nada: {nada_dasar}
        """
        
        # AGENT LOGIC: Fallback Loop dengan model generasi terbaru
        MODEL_LIST = [
            'gemini-3.5-flash',
            'gemini-3.1-pro',
            'gemini-3-flash'
        ]
        
        response = None
        last_error = None
        
        for model_name in MODEL_LIST:
            try:
                print(f"⏳ Sedang mencoba memanggil model: {model_name}...")
                response = client_genai.models.generate_content(
                    model=model_name, 
                    contents=[prompt, audio_file]
                )
                print(f"✅ Sukses! Model {model_name} berhasil merespons.")
                break # Keluar dari loop karena berhasil
            except Exception as model_err:
                print(f"⚠️ Model {model_name} gagal: {model_err}")
                last_error = model_err
                continue # Lanjut coba model berikutnya di daftar
                
        # Jika semua model di list gagal
        if response is None:
            raise Exception(f"Semua model AI sedang tidak tersedia. Error terakhir: {last_error}")
        
        raw_text = response.text.strip()
        raw_text = re.sub(r'```[a-z]*\n?', '', raw_text)
        raw_text = raw_text.replace('```', '').strip()
        
        # AGENT LOGIC 3: Simpan ke MongoDB
        if history_collection is not None:
            history_collection.insert_one({
                "file_name": file.filename,
                "instrument": instrument,
                "nada_dasar": nada_dasar,
                "chord_lyric": raw_text,
                "created_at": datetime.now()
            })
            
        # Cleanup
        client_genai.files.delete(name=audio_file.name)
        os.remove(temp_path)
        
        return {
            "status": "success", 
            "source": "gemini",
            "data": raw_text
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}