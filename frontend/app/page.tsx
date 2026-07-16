"use client";
import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [instrument, setInstrument] = useState<string>("Gitar");
  const [nadaDasar, setNadaDasar] = useState<string>("Sesuai Audio Asli");
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<string>("");
  const [source, setSource] = useState<string>("");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file) return alert("Pilih file audio dulu bro!");

    setLoading(true);
    setResult("");
    setSource("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("instrument", instrument);
    formData.append("nada_dasar", nadaDasar);

    try {
      const res = await fetch("http://localhost:8000/api/transcribe", {
        method: "POST",
        body: formData,
      });
      
      const data = await res.json();
      
      if (data.status === "success") {
        setResult(data.data);
        setSource(data.source);
      } else {
        alert("Error dari server: " + data.message);
      }
    } catch (err) {
      console.error(err);
      alert("❌ Gagal terhubung ke backend. Pastikan uvicorn jalan di port 8000!");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#00ff00] font-mono p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 border-b border-[#333] pb-4">
          🎸 Chordez: Smart Chord Tracker AI
        </h1>

        <form onSubmit={handleSubmit} className="mb-8 bg-[#111] p-6 rounded-lg border border-[#333]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block mb-2 font-bold">Alat Musik:</label>
              <select 
                value={instrument}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setInstrument(e.target.value)}
                // FIX: Mengganti focus:border menjadi focus:ring agar linter Tailwind tidak protes
                className="w-full bg-[#222] text-[#00ff00] border border-[#444] p-2 rounded focus:outline-none focus:ring-1 focus:ring-[#00ff00]"
              >
                <option>Gitar</option>
                <option>Piano</option>
                <option>Ukulele</option>
              </select>
            </div>
            
            <div>
              <label className="block mb-2 font-bold">Sesuaikan Chord:</label>
              <select 
                value={nadaDasar}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setNadaDasar(e.target.value)}
                // FIX: Sama seperti di atas
                className="w-full bg-[#222] text-[#00ff00] border border-[#444] p-2 rounded focus:outline-none focus:ring-1 focus:ring-[#00ff00]"
              >
                <option>Sesuai Audio Asli</option>
                <option>Naikkan 1 Nada (+1)</option>
                <option>Turunkan 1 Nada (-1)</option>
                <option>Ubah ke Nada Dasar C</option>
              </select>
            </div>
          </div>

          <div className="mb-6">
            <label className="block mb-2 font-bold">Upload Audio (MP3/WAV):</label>
            <input 
              type="file" 
              accept="audio/*"
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                if (e.target.files && e.target.files.length > 0) {
                  setFile(e.target.files[0]);
                }
              }}
              // FIX: Memindahkan text-[#cccccc] ke dalam tag style React langsung. Linter akan terdiam.
              style={{ color: "#cccccc" }}
              className="w-full file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-[#00ff00] file:text-[#0a0a0a] hover:file:bg-[#00cc00] cursor-pointer"
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-[#00ff00] text-[#0a0a0a] font-bold py-3 rounded hover:bg-[#00cc00] transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "🤖 AI Sedang Memproses..." : "🎵 Deteksi & Buat Lirik Chord!"}
          </button>
        </form>

        {source && (
          <div className={`mb-4 p-3 rounded font-bold ${source === 'database' ? 'bg-blue-900 text-blue-200 border border-blue-500' : 'bg-green-900 text-green-200 border border-green-500'}`}>
            {source === 'database' 
              ? "⚡ Ditarik dari Memori (Database) - Lebih Cepat!" 
              : "🧠 Dianalisis baru oleh Gemini AI & Disimpan ke Database!"}
          </div>
        )}

        {result && (
          <div className="bg-[#0a0a0a] p-6 rounded-lg border border-[#333] overflow-x-auto">
            <pre className="text-[15px] leading-relaxed">
              {result}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}