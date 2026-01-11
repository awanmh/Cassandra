# Cassandra

![Badge Status](https://img.shields.io/badge/Status-Active-green) ![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue) ![Docker](https://img.shields.io/badge/Docker-Ready-blue) ![WAF](https://img.shields.io/badge/WAF-Evasion-red)

## 1. Apa itu Tools Cassandra?

**Cassandra 2.1** adalah agen keamanan siber otonom (_Autonomous Security Agent_) yang dirancang khusus untuk para _Red Teamer_ dan pemburu _Bug Bounty_. Tidak seperti scanner konvensional yang "berisik" dan mudah diblokir, Cassandra v2.1 mengadopsi pendekatan **Smart Reconnaissance**.

Sistem ini memiliki "Otak" (_Smart Decision Engine_) yang mampu mengenali teknologi target dan memutuskan serangan spesifik yang paling efektif, sembari tetap menjaga keamanan operasional (_Stealth Mode_) agar tidak terdeteksi oleh Web Application Firewall (WAF) atau menyebabkan pemblokiran IP.

### Arsitektur Sistem

```plaintext
[ USER ]
    |
    v
[ CASSANDRA ORCHESTRATOR v2.1 ]
    |--[ Check Scope Rule ] (Safety: Deny List)
    |--[ Load Proxies ] (Stealth: Rotation)
    |
    |--> [ FINGERPRINT MODULE ] (Detect Tech)
    |
    |--> [ SMART DECISION ENGINE ]
    |       |-- IF React/Vue --> [ JS HUNTER ] --> (Extract Endpoints & Secrets) -> [ DB ]
    |       |-- IF Laravel   --> [ NUCLEI ] (Proxy Rotated) --> [ Discord Alert ]
    |       |-- IF WP        --> [ WPSCAN ] (Proxy Rotated) --> [ Discord Alert ]
```

## 2. Tech Stack

Cassandra dibangun di atas fondasi teknologi modern, modular, dan skalabel:

- **Core Logic**: Python 3.10+ (Mengelola orkestrasi, logika keputusan, dan pemrosesan data).
- **Infrastructure**: Docker & Docker Compose (Isolasi lingkungan yang konsisten).
- **Database**: PostgreSQL (Via SQLAlchemy untuk penyimpanan data yang robust).
- **Message Queue**: Redis (Persiapan untuk pemrosesan antrian asinkron skala besar).
- **Scanning Engine**: Integrasi alat terbaik industri (_Nuclei, Subfinder, Httpx, Dalfox_).
- **Fingerprinting**: Wappalyzer & Httpx Tech Detect.
- **Secret Harvesting**: Playwright (Headless Browser) & Regex.
- **Dashboard**: Streamlit (Visualisasi data interaktif).

## 3. Fitur Utama

Cassandra v2.1 dilengkapi dengan 4 pilar fitur utama:

### 1. Stealth Mode (The Ghost)

Mekanisme otomatis untuk menghindari deteksi WAF dan IP Ban.

- **Proxy Rotary**: Mengganti alamat IP secara otomatis setiap kali melakukan request eksternal menggunakan daftar proxy di `config/proxies.txt`.
- **Smart Delay**: Jika terdeteksi _Rate Limiting_ (HTTP 429), sistem akan "tidur" secara acak selama 30-60 detik sebelum mencoba lagi.

### 2. Scope Safety System (Compliance)

Fitur kepatuhan untuk mencegah serangan "Out-of-Scope" yang dapat menyebabkan akun Bug Bounty dibanned.

- **Deny List**: Sistem mengecek setiap target terhadap daftar hitam di `config/scope_deny.txt` (misal: `gov.id`, `google.com`). Jika cocok, target akan dilewati.

### 3. Smart Orchestration (The Brain)

Tidak lagi melakukan serangan membabi-buta (_blind scanning_).

- Mendeteksi teknologi (misal: WordPress, Laravel, Spring Boot).
- Hanya menjalankan eksploit yang relevan (misal: WPScan hanya jalan di WordPress).

### 4. Advanced JS Extraction (The Gold Mine)

Modul ekstraksi tingkat lanjut pada file JavaScript.

- **Secret Hunter**: Mencari kebocoran API Key (AWS, Google, Stripe, Slack).
- **Endpoint Miner**: Mengekstrak _hidden endpoints_ (URL tersembunyi seperti `/api/v1/admin`, `/internal/debug`) yang seringkali luput dari scanner biasa.

## 4. Prerequisites (Persyaratan Sistem)

Sebelum menginstal, pastikan sistem Anda memiliki:

- **Docker & Docker Compose** (Wajib, karena seluruh sistem berjalan dalam container).
- **Git** (Untuk mengunduh repositori).
- **Koneksi Internet** (Untuk mengunduh image Docker dan dependensi).

## 5. Instalasi

Proses instalasi sangat mudah berkat Docker:

1.  **Clone Repositori**:

    ```bash
    git clone https://github.com/username/cassandra.git
    cd cassandra
    ```

2.  **Konfigurasi Environment**:
    Buat file `.env` dari template `config/secrets.env` dan isi kredensial yang diperlukan (terutama `DISCORD_WEBHOOK_URL` untuk notifikasi real-time).

    ```env
    DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
    POSTGRES_USER=cassandra
    POSTGRES_PASSWORD=secret
    ```

3.  **Setup Konfigurasi Serangan**:

    - Isi `config/proxies.txt` dengan daftar proxy Anda (Format: `http://ip:port`).
    - Isi `config/scope_deny.txt` dengan domain yang **DILARANG** diserang.

4.  **Bangun & Jalankan**:
    ```bash
    docker-compose up --build -d
    ```
    Perintah ini akan mendownload semua tools, membangun database, dan menyiapkan sistem.

## 6. Struktur Direktori

- `core/`: **Inti Sistem**. Berisi `orchestrator.py` (logika utama), `notifier.py` (alerting), dan `database.py` (model DB).
- `modules/`: **Modul Serangan**. Berisi `fingerprint.py` (Wappalyzer), `js_scanner.py` (Playwright), dll.
- `config/`: **Pusat Konfigurasi**. Tempat menaruh `proxies.txt`, `rules.json`, dan `scope_deny.txt`.
- `dashboard/`: **Antarmuka Pengguna**. Kode untuk tampilan Web UI.
- `data/`: **Penyimpanan**. Folder mount untuk hasil scan fisik.

## 7. Cara Menjalankan

Setelah container berjalan, Anda dapat menjalankan perintah scan langsung dari dalam container:

1.  **Masuk ke Container Aplikasi**:

    ```bash
    docker-compose exec cassandra-app bash
    ```

2.  **Jalankan Perintah Scan**:
    ```bash
    python main.py --mode full --policy policy.txt
    ```
    - `--mode full`: Menjalankan seluruh rangkaian (Recon -> Fingerprint -> Smart Attack -> JS Scan).
    - `--policy policy.txt`: File berisi daftar target scope.

## 8. Dashboard

Cassandra menyediakan **Command Center** berbasis Web untuk memantau operasi. Akses melalui browser di:
**`http://localhost:8501`**

### Isi Dashboard:

1.  **Overview Metrics**:

    - **Targets Engaged**: Jumlah domain yang sedang diproses.
    - **Vulnerabilities**: Total bug yang ditemukan (Critical/High ditandai warna merah).
    - **Secrets Leaked**: Jumlah kredensial sensitif yang berhasil dicuri.
    - **API Endpoints**: Jumlah endpoint tersembunyi yang ditemukan.

2.  **Tab "👁️ Recon (The Eyes)"**:

    - Menampilkan teknologi yang digunakan target (Framework, Server, CMS).
    - Grafik distribusi teknologi.

3.  **Tab "🧠 Vulns (The Brain)"**:

    - Tabel detail kerentanan dengan tingkat keparahan (Severity).
    - Warna indikator otomatis (Merah = Critical, Kuning = Medium).

4.  **Tab "💰 Secrets (The Looter)"**:

    - Daftar API Key yang bocor beserta lokasi file sumbernya.
    - Tombol **Export CSV** untuk mengunduh bukti temuan.

5.  **Tab "📍 Endpoints (The Mine)"**:
    - Daftar URL endpoint API unik (`/api/...`) yang diekstrak dari file JavaScript untuk analisis manual lebih lanjut.

---

<p align="center">
  **Cassandra 2.1 - Stay Safe, Hunt Hard.**
</p>
