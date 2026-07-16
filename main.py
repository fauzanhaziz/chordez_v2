from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from google import genai
import tempfile
import os
import re
from datetime import datetime
import time
from dotenv import load_dotenv

# Inisialisasi Aplikasi Backend
app = FastAPI(title="Chordez Agentic API")

# Konfigurasi CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv() 
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY belum diatur di file .env!")

client_genai = genai.Client(api_key=API_KEY)

# Koneksi Database
try:
    mongo_client = MongoClient("mongodb://admin:rahasia123@database:27017/")
    db = mongo_client["chordez_db"]
    history_collection = db["transcriptions"]
    print("✅ Database MongoDB: Online")
except Exception as e:
    print(f"❌ Database Error: {e}")
    history_collection = None

# ==========================================
# AGENT TOOLS (Alat-alat Eksternal untuk AI)
# ==========================================
class AgentTools:
    """Kumpulan alat (Tools) yang bisa digunakan agen untuk berinteraksi dengan dunia luar."""
    
    @staticmethod
    def read_memory(file_name: str, instrument: str, nada_dasar: str) -> str:
        """Alat untuk membaca memori jangka panjang (Database)."""
        if history_collection is not None:
            data = history_collection.find_one({
                "file_name": file_name, 
                "instrument": instrument, 
                "nada_dasar": nada_dasar
            })
            return data["chord_lyric"] if data else None
        return None

    @staticmethod
    def save_memory(file_name: str, instrument: str, nada_dasar: str, chord_lyric: str):
        """Alat untuk menyimpan hasil ke memori jangka panjang."""
        if history_collection is not None:
            history_collection.insert_one({
                "file_name": file_name, 
                "instrument": instrument,
                "nada_dasar": nada_dasar, 
                "chord_lyric": chord_lyric,
                "created_at": datetime.now()
            })


# ==========================================
# AGENT ORCHESTRATOR (ReAct Workflow)
# ==========================================
@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    instrument: str = Form(...),
    nada_dasar: str = Form(...)
):
    try:
        print(f"\n🤖 [AGENT START] Menerima misi transkripsi untuk file: {file.filename}")
        
        # --- TAHAP 1: ACTING (MENGGUNAKAN ALAT MEMORI) ---
        print("🛠️ [AGENT ACT] Mengecek memori jangka panjang (Database)...")
        memory_result = AgentTools.read_memory(file.filename, instrument, nada_dasar)
        
        # --- TAHAP 2: REASONING (PENGAMBILAN KEPUTUSAN) ---
        if memory_result:
            print("💡 [AGENT REASONING] Data ditemukan di memori! Melewati proses AI untuk menghemat resource.")
            return {"status": "success", "source": "agent_memory", "data": memory_result}
            
        print("💡 [AGENT REASONING] Data belum ada di memori. Agen memutuskan untuk memproses audio.")
        
        # --- TAHAP 3: ACTING (MENGGUNAKAN SENSOR AUDIO) ---
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        print("📤 [AGENT ACT] Mengaktifkan sensor telinga (Upload ke Gemini)...")
        audio_file = client_genai.files.upload(file=temp_path)
        
        while audio_file.state.name == "PROCESSING":
            print("⏳ [AGENT WAIT] Menunggu sistem memproses spektrum audio...")
            time.sleep(2)
            audio_file = client_genai.files.get(name=audio_file.name)
        
        # --- TAHAP 4: REASONING (PROSES KOGNITIF UTAMA) ---
        prompt = f"""
        Kamu adalah Agen Transkripsi Musik Profesional. 
        Tugas: Ekstrak chord dan lirik dari audio ini.
        Instrumen: {instrument}
        Nada Dasar: {nada_dasar}
        
        Aturan Output:
        - Tuliskan chord tepat di atas suku kata yang sesuai.
        - Gunakan blok penanda bagian lagu seperti [Intro], [Verse], [Chorus].
        - Berikan hasil transkripsi final secara langsung tanpa kalimat pengantar.
        """
        
        print("🧠 [AGENT REASONING] Memulai proses kognitif (Ekstraksi Kord)...")
        
        # Model fallback untuk memastikan agent "Tahan Banting" (Self-Healing)
        MODEL_LIST = ['gemini-3.5-flash', 'gemini-3.1-pro', 'gemini-3-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
        response = None
        
        for model_name in MODEL_LIST:
            try:
                print(f"⚙️ Menghubungi unit otak: {model_name}...")
                response = client_genai.models.generate_content(
                    model=model_name, 
                    contents=[prompt, audio_file]
                )
                print(f"✅ [AGENT SUCCESS] Berhasil menggunakan otak {model_name}")
                break
            except Exception as e:
                print(f"⚠️ [AGENT SELF-HEAL] Otak {model_name} gagal, memindahkan ke otak cadangan. Error: {e}")
                continue
                
        if not response:
            raise Exception("Semua sistem otak AI sedang kritis/gagal.")
            
        raw_text = response.text.strip()
        raw_text = re.sub(r'```[a-z]*\n?', '', raw_text).replace('```', '').strip()
        
        # --- TAHAP 5: ACTING (MENYIMPAN PENGETAHUAN BARU) ---
        print("🛠️ [AGENT ACT] Menyimpan pengetahuan baru ke memori (Database)...")
        AgentTools.save_memory(file.filename, instrument, nada_dasar, raw_text)
        
        # Pembersihan Jejak (Cleanup)
        client_genai.files.delete(name=audio_file.name)
        os.remove(temp_path)
        
        print("🏁 [AGENT MISSION COMPLETE] Tugas selesai dengan sempurna.")
        return {"status": "success", "source": "agent_cognitive", "data": raw_text}
        
    except Exception as e:
        print(f"❌ [AGENT ERROR] Kegagalan sistem terdeteksi: {e}")
        return {"status": "error", "message": str(e)}