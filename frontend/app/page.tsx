"use client";

import { useState } from "react";
import { Upload, Music, Disc3, Mic2, Guitar, Loader2 } from "lucide-react";

// ✅ 1. Kita buat Interface/Tipe Data khusus untuk menggantikan 'any'
interface TranscriptionResult {
  source?: string;
  transkripsi?: string;
  data?: string | { transkripsi?: string }; // ✅ Sudah benar: bisa nerima string atau object
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [instrument, setInstrument] = useState("Guitar");
  const [nadaDasar, setNadaDasar] = useState("Original");
  const [loading, setLoading] = useState(false);
  
  // ✅ 2. Gunakan Interface TranscriptionResult di sini
  const [result, setResult] = useState<TranscriptionResult | null>(null);
  const [error, setError] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleTranscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Eh, lagunya belum dimasukin tuh, Bro!");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("instrument", instrument);
    formData.append("nada_dasar", nadaDasar);

    try {
      const response = await fetch("http://localhost:8000/api/transcribe", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Gagal terhubung ke studio (server error).");
      }

      const data = await response.json();
      setResult(data);
      
    // ✅ 3. Ganti 'any' menjadi 'unknown' dan cek tipe errornya secara aman
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Waduh, ada yang salah pas dengerin lagunya.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans selection:bg-amber-500/30">
      <nav className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Disc3 className="text-amber-500" size={28} />
            <span className="text-xl font-bold tracking-tight text-white">
              Chordez<span className="text-amber-500">.</span>
            </span>
          </div>
          <p className="text-sm text-zinc-400 hidden sm:block">
            Smart Music Transcriber
          </p>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center space-y-4 mb-12">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white">
            Berhenti nebak-nebak chord. <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-linear-to-r from-amber-400 to-orange-500">
              Mulai mainkan lagumu.
            </span>
          </h1>
          <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
            Upload file MP3 kamu, dan biarkan sistem kami mendengarkan lagunya. 
            Kami akan mengekstrak lirik dan kord yang akurat dalam hitungan detik.
          </p>
        </div>

        <div className="grid md:grid-cols-12 gap-8 items-start">
          
          <div className="md:col-span-5 bg-zinc-900/80 border border-zinc-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
            <form onSubmit={handleTranscribe} className="space-y-6">
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-300">File Audio (MP3/WAV)</label>
                <div className="relative group cursor-pointer">
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={handleFileChange}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                  />
                  <div className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 flex flex-col items-center gap-3 ${file ? 'border-amber-500 bg-amber-500/5' : 'border-zinc-700 bg-zinc-800/50 group-hover:border-zinc-500 group-hover:bg-zinc-800'}`}>
                    {file ? (
                      <>
                        <Music className="text-amber-500" size={32} />
                        <span className="text-amber-400 font-medium truncate max-w-full px-4">{file.name}</span>
                      </>
                    ) : (
                      <>
                        <Upload className="text-zinc-400 group-hover:text-zinc-300" size={32} />
                        <span className="text-zinc-400 font-medium text-sm">Drop lagu di sini atau klik untuk upload</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-300">Mau main pakai apa?</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setInstrument("Guitar")}
                    className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium transition-all ${instrument === "Guitar" ? 'bg-amber-500 text-zinc-950 shadow-md' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}`}
                  >
                    <Guitar size={18} /> Gitar
                  </button>
                  <button
                    type="button"
                    onClick={() => setInstrument("Piano")}
                    className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium transition-all ${instrument === "Piano" ? 'bg-amber-500 text-zinc-950 shadow-md' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}`}
                  >
                    <Music size={18} /> Piano
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-300">Nada Dasar (Key)</label>
                <select 
                  value={nadaDasar} 
                  onChange={(e) => setNadaDasar(e.target.value)}
                  className="w-full bg-zinc-800 border border-zinc-700 text-zinc-200 rounded-lg py-3 px-4 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all"
                >
                  <option value="Original">Sesuai Penyanyi Asli (Original)</option>
                  <option value="C">C (Paling Gampang)</option>
                  <option value="G">G</option>
                  <option value="D">D</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-linear-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white font-bold py-3.5 px-4 rounded-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    Sstt.. Sedang mendengarkan lagu...
                  </>
                ) : (
                  <>
                    <Mic2 size={20} />
                    Ekstrak Kord Sekarang
                  </>
                )}
              </button>

              {error && (
                <div className="p-4 bg-red-900/30 border border-red-800 text-red-300 rounded-lg text-sm text-center">
                  {error}
                </div>
              )}
            </form>
          </div>

          <div className="md:col-span-7">
            {result ? (
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 md:p-8 shadow-xl min-h-full">
                <div className="flex items-center justify-between mb-6 pb-6 border-b border-zinc-800">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-1">Hasil Transkripsi</h2>
                    <p className="text-sm text-zinc-400">
                      Instrumen: <span className="text-amber-500 font-medium">{instrument}</span> • Nada Dasar: <span className="text-amber-500 font-medium">{nadaDasar}</span>
                    </p>
                  </div>
                  {result.source === 'agent_memory' && (
                    <span className="bg-emerald-900/50 text-emerald-400 border border-emerald-800 text-xs px-3 py-1.5 rounded-full font-medium">
                      ⚡ Diambil dari Memori
                    </span>
                  )}
                </div>

                <div className="prose prose-invert max-w-none">
                  <pre className="whitespace-pre-wrap font-mono text-zinc-300 bg-zinc-950 p-6 rounded-xl border border-zinc-800 overflow-x-auto leading-relaxed text-[15px]">
                    {/* ✅ FIX LOGIKA DISINI: Cek apakah result.data berupa string langsung, kalau iya langsung tampilkan */}
                    {typeof result.data === 'string' 
                      ? result.data 
                      : result.data?.transkripsi || result.transkripsi || "Data lirik tidak ditemukan."}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="h-full min-h-100 border-2 border-dashed border-zinc-800 rounded-2xl flex flex-col items-center justify-center text-zinc-500 p-8 text-center bg-zinc-900/30">
                <Music size={48} className="mb-4 opacity-20" />
                <h3 className="text-lg font-medium text-zinc-400 mb-2">Kertas Partitur Masih Kosong</h3>
                <p className="max-w-sm text-sm">Upload lagumu di samping, dan kord berserta liriknya akan muncul di sini layaknya partitur profesional.</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}