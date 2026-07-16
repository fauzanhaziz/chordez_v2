# Chordez AI - Intelligent Chord Detection System

Chordez AI adalah platform web cerdas yang dirancang untuk mendeteksi kord musik dari file audio menggunakan integrasi **Agentic AI (Google Gemini)**. Proyek ini dibangun dengan arsitektur *Full-Stack* modern yang terintegrasi secara *containerized* menggunakan **Docker Compose**.

## 🚀 Technical Stack

### Frontend
- **Next.js**: Framework React untuk antarmuka pengguna yang responsif dan cepat.

### Backend
- **FastAPI**: *Framework* Python berperforma tinggi untuk menangani logika API dan pemrosesan audio.
- **Google Generative AI (Gemini)**: Otak di balik deteksi kord musik.

### Database
- **MongoDB**: Database NoSQL untuk menyimpan histori transkripsi kord.

### DevOps & Orchestration
- **Docker & Docker Compose**: Menyatukan seluruh ekosistem (Frontend, Backend, Database) dalam lingkungan yang terisolasi dan mudah di-deploy.

---

## 🏗️ System Architecture
Sistem ini menggunakan arsitektur 3-tier:
1. **Frontend**: Melayani *user interface* (Port 3000).
2. **Backend**: API *server* yang memproses request dan berkomunikasi dengan Gemini AI (Port 8000).
3. **Database**: *Instance* MongoDB untuk persistensi data (Port 27017).

---

## 🛠️ Prerequisites
Pastikan kamu telah menginstal:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Harus menyala)
- Git

---

## 🚀 Getting Started

### 1. Clone Repository
```bash
git clone [https://github.com/fauzanhaziz/chordez_v2.git](https://github.com/fauzanhaziz/chordez_v2.git)
cd chordez_v2