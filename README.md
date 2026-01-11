# Cassandra

![Badge Status](https://img.shields.io/badge/Status-Active-green) ![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue) ![Go Version](https://img.shields.io/badge/Go-1.21%2B-cyan)

## 1. Apa itu Tools Cassandra?

**Cassandra Ultimate** adalah sebuah agen otonom _end-to-end_ yang dirancang khusus untuk kegiatan **Bug Bounty Hunting** dan **Penetration Testing**. Tools ini tidak hanya sekadar scanner biasa, melainkan sebuah sistem cerdas yang mampu menangani seluruh siklus serangan siber secara otomatis, mulai dari penguraian ruang lingkup (_scope parsing_), pengintis pertahanan (_reconnaissance_), pemindaian terautentikasi (_authenticated scanning_), hingga eksploitasi tingkat lanjut (_advanced exploitation_) seperti SQL Injection, XSS, dan IDOR.

Fokus utama Cassandra adalah memberikan hasil yang akurat dengan laporan profesional, sembari tetap menjaga keamanan operasional melalui teknik evasi WAF (_WAF Evasion_) yang canggih.

## 2. Tech Stack

Cassandra dibangun di atas fondasi teknologi modern untuk menjamin kecepatan, skalabilitas, dan keandalan:

- **Core Engine**: Python 3.10+ (Logika utama, orkestrasi serangan, dan pemrosesan data).
- **High-Speed Scanner**: Go 1.21+ (Digunakan untuk _subdomain enumeration_ dan pemindaian jaringan berkecepatan tinggi).
- **Browser Automation**: Playwright (Untuk simulasi interaksi pengguna nyata, _crawling_ dinamis, dan bypass proteksi berbasis JavaScript).
- **Keamanan & Eksploitasi**: Integrasi mendalam dengan _Nuclei_, _SQLMap_, _Dalfox_, dan _Subfinder_.
- **Dashboard & Reporting**: Streamlit (Menyajikan visualisasi data temuan dan laporan yang mudah dipahami).
- **Database**: SQLite/JSON (Penyimpanan data hasil temuan yang terstruktur).

## 3. Fitur Utama

Cassandra dilengkapi dengan serangkaian fitur _enterprise-grade_ untuk memaksimalkan temuan bug:

1.  **Smart Scope Parsing**: Secara otomatis memvalidasi dan memisahkan target yang valid dari _out-of-scope_.
2.  **Deep Reconnaissance**: Melakukan _subdomain enumeration_ pasif dan aktif, _port scanning_, serta _tech stack detection_.
3.  **Authenticated Scanning**: Mampu melakukan login secara otomatis untuk memindai area yang dilindungi kata sandi (_behind login pages_).
4.  **Advanced Exploitation Modules**:
    - **SQL Injection**: Deteksi dan eksploitasi otomatis menggunakan _SQLMap_ yang dioptimalkan.
    - **Cross-Site Scripting (XSS)**: Pengujian payload berbasis konteks menggunakan _Dalfox_ dan _browser verification_.
    - **IDOR (Insecure Direct Object Reference)**: Analisis pola parameter untuk mendeteksi kerentanan akses data vertikal maupun horizontal.
5.  **WAF Evasion**: Teknik rotasi _User-Agent_, pengaturan _delay_ acak, dan penggunaan _proxy_ untuk menghindari deteksi firewall.
6.  **Interactive Dashboard**: Antarmuka grafis berbasis web untuk memantau serangan secara _real-time_ dan mengunduh laporan.

## 4. Prerequisites (Persyaratan Sistem)

Sebelum menginstal, pastikan sistem Anda memenuhi persyaratan berikut:

- **Sistem Operasi**: Windows, Linux, atau macOS.
- **Bahasa Pemrograman**:
  - Python versi **3.10** atau lebih baru.
  - Go (Golang) versi **1.21** atau lebih baru.
- **Tools Eksternal (Wajib)**:
  - [Subfinder](https://github.com/projectdiscovery/subfinder) (Recon)
  - [Nuclei](https://github.com/projectdiscovery/nuclei) (Scanning)
  - [Httpx](https://github.com/projectdiscovery/httpx) (Probing)
  - [Dalfox](https://github.com/hahwul/dalfox) (XSS)
  - [SQLMap](https://github.com/sqlmapproject/sqlmap) (SQLi)

## 5. Instalasi

Ikuti langkah-langkah berikut untuk menginstal Cassandra secara lengkap:

### Langkah 1: Install Go Tools

Buka terminal dan jalankan perintah berikut untuk menginstal alat-alat berbasis Go:

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/hahwul/dalfox/v2@latest
```

### Langkah 2: Install SQLMap

Clone repositori SQLMap versi developer:

```bash
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap-dev
# Catatan: Pastikan path folder sqlmap-dev ini dicatat untuk konfigurasi file .env nanti.
```

### Langkah 3: Install Dependensi Python

Instal _library_ Python yang dibutuhkan dan browser untuk Playwright:

```bash
pip install -r requirements.txt
playwright install
```

### Langkah 4: Konfigurasi Environment

1.  Salin file `config/secrets.env` (atau buat baru) menjadi file bernama `.env` di direktori utama (`root`).
2.  Edit file `.env` tersebut dan isi konfigurasi yang diperlukan, seperti API Key (jika ada) dan _path_ ke tools eksternal jika tidak terdeteksi otomatis.

## 6. Struktur Direktori

Memahami struktur folder akan membantu Anda dalam penggunaan dan pengembangan lebih lanjut:

- `core/`: **Otak Utama**. Berisi logika untuk parsing scope, autentikasi, evade WAF, dan manajemen sesi.
- `scanner/`: **Scanner Engine**. Modul berbasis Go untuk pemindaian berkecepatan tinggi.
- `modules/`: **Attack Modules**. Script Python spesifik untuk jenis serangan tertentu (misal: `xss_runner.py`, `idor_scanner.py`).
- `dashboard/`: **User Interface**. Kode sumber untuk tampilan dashboard berbasis Streamlit.
- `data/`: **Penyimpanan**. Folder tempat menyimpan hasil scan, log, dan artefak bukti temuan.
- `config/`: **Konfigurasi**. Template konfigurasi dan _wordlist_ dasar.

## 7. Cara Menjalankan

Cassandra memiliki beberapa mode operasi yang dapat dijalankan melalui terminal:

### Mode 1: Recon (Pengintaian)

Mode ini hanya akan melakukan parsing _scope_, mencari subdomain, dan pengecekan dasar tanpa melakukan serangan agresif.

```bash
python main.py --mode recon --policy policy.txt
```

### Mode 2: Full Attack (Serangan Penuh)

Mode ini mencakup seluruh fitur: login otomatis, bypass WAF, scanning kerentanan, hingga eksploitasi aktif (SQLi, XSS, dll).

```bash
python main.py --mode full --policy policy.txt --login
```

_Catatan: Gunakan flag `--login` jika target memerlukan autentikasi._

## 8. Dashboard

Untuk melihat hasil temuan secara visual dan membuat laporan, jalankan dashboard:

```bash
streamlit run dashboard/app.py
```

Akses dashboard melalui browser di alamat yang muncul (biasanya `http://localhost:8501`).

---

<p align="center">
  Dibuat dengan ❤️ untuk Komunitas Keamanan Siber
</p>
