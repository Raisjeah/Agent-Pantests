# AI Security Workflow Engine 🤖

AI Pentest Agent berbasis LangChain dan LangGraph yang bekerja secara **DETERMINISTIK** dan berbasis **EVIDENCE**. Dirancang untuk melakukan automation security testing tanpa halusinasi.

## 🚀 Cara Kerja

Engine ini mengikuti alur kerja 6 fase yang teratur:
1.  **RECON**: Pencarian informasi host/domain menggunakan Nmap dan Nuclei.
2.  **SCAN**: Identifikasi service dan versi secara akurat.
3.  **ENUM**: Enumerasi mendalam pada service yang ditemukan.
4.  **VULN_ANALYSIS**: Analisis kerentanan (SQLi, CVE, misconfiguration) dengan confidence score.
5.  **EXPLOITATION**: Eksekusi payload jika dan hanya jika confidence > 0.7 dan bukti cukup.
6.  **REPORT**: Penyusunan laporan akhir berdasarkan temuan yang tervalidasi.

### Core Principles:
- **Tools as Source of Truth**: Keputusan hanya diambil dari output tool nyata.
- **No Hallucination**: AI dilarang mengarang credential, akses, atau temuan.
- **Strict Validation**: Setiap perintah yang dijalankan (Hydra, Curl, NC) divalidasi keberhasilannya secara otomatis.
- **Safety First**: Interupsi manual diperlukan sebelum fase eksploitasi.

## 🛠 Instalasi

Pastikan Anda memiliki Python 3.10+ dan tool keamanan berikut terinstal: `nmap`, `nuclei`, `sqlmap`.

```bash
# Clone repository
git clone <repo-url>
cd ai-pentest

# Install dependencies
pip install .

# Set Google API Key
export GOOGLE_API_KEY="your-api-key"
```

## 💻 Penggunaan (Command)

Jalankan pemindaian dengan perintah `ai-pentest` atau langsung lewat `cli.py`:

### Pemindaian Standar
```bash
python3 cli.py scan <target>
```

### Opsi Tambahan
- `--scope`: Membatasi cakupan (web, os, mobile, code). Default: `all`.
- `--deep`: Mengaktifkan mode pemindaian mendalam.
- `--output`: Menyimpan hasil scan dan state lengkap ke file JSON.

Contoh:
```bash
python3 cli.py scan 192.168.1.1 --output report.json
```

## ⚙️ Konfigurasi
Konfigurasi model LLM dan path tool tersedia di `agent/config.yaml`.

---
**PENTING**: Gunakan tool ini hanya untuk tujuan legal dan pada target yang Anda miliki izinnya.
