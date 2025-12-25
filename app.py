# Import library yang dibutuhkan
from flask import Flask, render_template_string, request, redirect, url_for, send_file
import datetime                    # Untuk waktu dan ID urut
import os                         # Untuk mengelola file/folder
import pandas as pd               # Untuk grafik dan export Excel
import matplotlib.pyplot as plt   # Untuk membuat grafik
from io import BytesIO            # Untuk kirim gambar grafik
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors  # Untuk export PDF
import smtplib                    # Kirim email notifikasi
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders        # Lampirkan gambar di email

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Folder untuk menyimpan gambar bukti pengaduan
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Buat folder jika belum ada

# ================== KONFIGURASI - GANTI DENGAN DATA KAMU ==================
ADMIN_PASSWORD = "pipp2025"                          # Password login admin
EMAIL_PENGIRIM = "emailkamu@gmail.com"               # Gmail pengirim notifikasi
EMAIL_PASSWORD = "abcd efgh ijkl mnop"               # App Password Gmail (16 digit, tanpa spasi)
EMAIL_PENERIMA = "adminpipp@gmail.com"               # Email penerima notifikasi
# ===========================================================================

# File penyimpanan laporan utama (semua data + status)
FILE_LAPORAN = "laporan.txt"

# File counter untuk ID urut laporan (1, 2, 3, dst)
FILE_COUNTER = "counter.txt"

# Fungsi: Dapatkan ID urut berikutnya untuk laporan
def get_next_id():
    if not os.path.exists(FILE_COUNTER):
        with open(FILE_COUNTER, "w", encoding="utf-8") as f:
            f.write("1")
        return 1
    with open(FILE_COUNTER, "r", encoding="utf-8") as f:
        current = int(f.read().strip())
    next_id = current + 1
    with open(FILE_COUNTER, "w", encoding="utf-8") as f:
        f.write(str(next_id))
    return current

# Fungsi: Kirim email notifikasi ke admin
def kirim_email_notifikasi(jenis, data, gambar_path=None):
    print("EMAIL DINONAKTIFKAN DI PRODUCTION")
    return

# Fungsi: Simpan laporan baru dengan ID urut dan status default
def simpan_laporan(jenis, data, gambar_nama=None):
    laporan_id = get_next_id()
    waktu = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(FILE_LAPORAN, "a", encoding="utf-8") as f:
        f.write(f"[{waktu}] {jenis} | ID:{laporan_id}\n")
        for key, value in data.items():
            f.write(f"{key}: {value}\n")
        if gambar_nama:
            f.write(f"Gambar: {gambar_nama}\n")
        f.write("Status: Sedang Ditindaklanjuti\n")
        f.write("-" * 50 + "\n")
    
    gambar_path = os.path.join(app.config['UPLOAD_FOLDER'], gambar_nama) if gambar_nama else None
    kirim_email_notifikasi(jenis, data, gambar_path)

# Fungsi: Baca semua laporan termasuk status
def baca_laporan_dengan_status():
    laporan_list = []
    current = {}
    if not os.path.exists(FILE_LAPORAN):
        return []
    with open(FILE_LAPORAN, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("["):
                if current:
                    laporan_list.append(current)
                parts = line.split(" | ID:")
                waktu_jenis = parts[0][1:]
                laporan_id = parts[1] if len(parts) > 1 else "unknown"
                current = {"Waktu_Jenis": waktu_jenis, "ID": laporan_id}
            elif ":" in line and not line.startswith("-"):
                key, value = line.split(":", 1)
                current[key.strip()] = value.strip()
        if current:
            laporan_list.append(current)
    return laporan_list

# Fungsi: Update status laporan (versi aman, hanya 1 laporan yang berubah)
def update_status(laporan_id, new_status):
    if not os.path.exists(FILE_LAPORAN):
        return
    lines = []
    with open(FILE_LAPORAN, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    current_block_has_target = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            current_block_has_target = f"ID:{laporan_id}" in stripped
            new_lines.append(line)
            continue
        if current_block_has_target and stripped.startswith("Status:"):
            new_lines.append(f"Status: {new_status}\n")
        else:
            new_lines.append(line)
    with open(FILE_LAPORAN, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

# Halaman Dashboard utama (8 menu)
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard PIPP - BPJS Kesehatan</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; padding: 20px; }
        .card { transition: transform 0.3s; }
        .card:hover { transform: translateY(-10px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
        h1 { color: #0d6efd; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center my-5">Dashboard PIPP BPJS Kesehatan</h1>
        <div class="row row-cols-1 row-cols-md-3 g-4">
            <div class="col"><div class="card h-100 text-center"><div class="card-body">
                <h5 class="card-title">1. Informasi dan Pengaduan</h5><p class="card-text">Ajukan pengaduan atau cari informasi layanan</p>
                <a href="/pengaduan" class="btn btn-primary">Masuk</a>
            </div></div></div>
            <div class="col"><div class="card h-100 text-center"><div class="card-body">
                <h5 class="card-title">2. Pendaftaran BPJS Bayi Baru Lahir</h5><p class="card-text">Daftarkan bayi baru lahir dengan mudah</p>
                <a href="/bayi_baru_lahir" class="btn btn-primary">Masuk</a>
            </div></div></div>
            <div class="col"><div class="card h-100 text-center"><div class="card-body">
                <h5 class="card-title">3. Denda Pelayanan</h5><p class="card-text">Cek informasi denda pelayanan</p>
                <a href="/denda_pelayanan" class="btn btn-primary">Masuk</a>
            </div></div></div>
            <div class="col"><div class="card h-100 text-center"><div class="card-body">
                <h5 class="card-title">4. Status Kepesertaan</h5><p class="card-text">Cek status kepesertaan BPJS Anda</p>
                <a href="/status_kepesertaan" class="btn btn-primary">Masuk</a>
            </div></div></div>
            <div class="col"><div class="card h-100 text-center"><div class="card-body">
                <h5 class="card-title">5. Pendaftaran Universal Health Coverage (UHC)</h5><p class="card-text">Informasi dan pendaftaran UHC</p>
                <a href="/uhc" class="btn btn-primary">Masuk</a>
            </div></div></div>
            <div class="col"><div class="card h-100 text-center"><div class="card-body">
                <h5 class="card-title">6. Capaian Penggunaan Mobile JKN (MJKN)</h5><p class="card-text">Lihat statistik penggunaan Mobile JKN</p>
                <a href="/mjkn" class="btn btn-primary">Masuk</a>
            </div></div></div>
            <div class="col"><div class="card h-100 text-center"><div class="card-body">
                <h5 class="card-title">7. KESSAN (Kesan dan Pesan setelah Layanan)</h5><p class="card-text">Berikan kesan dan pesan setelah mendapat layanan</p>
                <a href="/kessan" class="btn btn-primary">Masuk</a>
            </div></div></div>
            <div class="col"><div class="card h-100 text-center bg-warning text-dark"><div class="card-body">
                <h5 class="card-title">ADMIN - Dashboard Laporan</h5><p class="card-text">Statistik, grafik & export</p>
                <a href="/login" class="btn btn-dark">Masuk Admin</a>
            </div></div></div>
        </div>
    </div>
</body>
</html>
"""

# Form Pengaduan (menu 1)
HTML_PENGADUAN = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Form Pengaduan</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <h2 class="text-center text-primary mb-4">Form Informasi dan Pengaduan</h2>
        <form action="/submit_pengaduan" method="post" enctype="multipart/form-data">
            <div class="mb-3"><label class="form-label">Nama </label><input type="text" name="Nama" class="form-control"></div>
            <div class="mb-3"><label class="form-label">No Kartu BPJS/NIK </label><input type="text" name="No Kartu BPJS/NIK" class="form-control"></div>
            <div class="mb-3"><label class="form-label">Sumber Data</label>
                <select name="jenis" class="form-select">
                    <option value="Pilihan">Sms</option>
                    <option value="Pilihan">Telepon</option>
                    <option value="Pilihan">Tatap Muka</option>
                    <option value="Pilihan">Whatsapp</option>
                    <option value="Pilihan">Telegram</option>
                    <option value="Pilihan">Media Sosial</option>
                    <option value="Pilihan">Media Cetak</option>
                    <option value="Pilihan">Surat</option>
                    <option value="Pilihan">Lainnya</option>
                </select>
            </div>
            <div class="mb-3"><label class="form-label">No.Handphone </label><input type="text" name="No.Handphone" class="form-control"></div>
            <div class="mb-3"><label class="form-label">Tanggal Kejadian</label><input type="date" name="tgl_lahir" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Tempat Kejadian</label><input type="text" name="Tempat Kejadian" class="form-control"></div>
            <div class="mb-3"><label class="form-label">Pengaduan/Permintaan Informasi</label><textarea name="isi" class="form-control" rows="5" required></textarea></div>
            <div class="mb-3"><label class="form-label">File Pendukung (Foto/Gambar)</label>
                <input type="file" name="gambar" class="form-control" accept="image/*">
                <small class="text-muted">Opsional</small>
            </div>
            <div class="mb-3"><label class="form-label">Catatan Tindak Lanjut (Di Isi Oleh Petugas PIPP)</label><textarea name="Catatan Tindak Lanjut" class="form-control" rows="5" required></textarea></div>
            <button type="submit" class="btn btn-primary">Kirim Pengaduan</button>
            <a href="/" class="btn btn-secondary ms-2">Kembali</a>
        </form>
    </div>
</body>
</html>
"""

# Form KESSAN (menu 7)
HTML_KESSAN = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Form KESSAN</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <h2 class="text-center text-primary mb-4">Form KESSAN (Kesan dan Pesan)</h2>
        <form action="/submit_kessan" method="post">
            <div class="mb-3"><label class="form-label">Nama (Opsional)</label><input type="text" name="nama" class="form-control"></div>
            <div class="mb-3"><label class="form-label">Kesan Anda</label><textarea name="kesan" class="form-control" rows="4" required></textarea></div>
            <div class="mb-3"><label class="form-label">Saran/Pesan</label><textarea name="pesan" class="form-control" rows="4"></textarea></div>
            <button type="submit" class="btn btn-primary">Kirim KESSAN</button>
            <a href="/" class="btn btn-secondary ms-2">Kembali</a>
        </form>
    </div>
</body>
</html>
"""

# Form 2: Pendaftaran Bayi Baru Lahir
HTML_BAYI_BARU_LAHIR = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Pendaftaran BPJS Bayi Baru Lahir</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <h2 class="text-center text-primary mb-4">Pendaftaran BPJS Bayi Baru Lahir</h2>
        <form action="/submit_bayi" method="post">
            <div class="mb-3"><label class="form-label">Nama Bayi</label><input type="text" name="nama_bayi" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Tanggal Lahir</label><input type="date" name="tgl_lahir" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Tanggal Pendaftaran</label><input type="date" name="tgl_pendaftaran" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Nama Orang Tua</label><input type="text" name="nama_ortu" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Nama Petugas Entri</label><input type="text" name="nama_petugas_entri" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">No. Kartu BPJS/NIK Orang Tua Bayi</label><input type="text" name="no_bpjs" class="form-control" required></div>
            <button type="submit" class="btn btn-primary">Ajukan Pendaftaran</button>
            <a href="/" class="btn btn-secondary ms-2">Kembali</a>
        </form>
    </div>
</body>
</html>
"""

# Form 3: Cek Denda Pelayanan
HTML_DENDA_PELAYANAN = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Cek Denda Pelayanan</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <h2 class="text-center text-primary mb-4">Cek Denda Pelayanan</h2>
        <form action="/submit_denda" method="post">
            <div class="mb-3"><label class="form-label">No. Kartu BPJS</label><input type="text" name="no_bpjs" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Tanggal Pelayanan</label><input type="date" name="tgl_pelayanan" class="form-control" required></div>
            <button type="submit" class="btn btn-primary">Cek Denda</button>
            <a href="/" class="btn btn-secondary ms-2">Kembali</a>
        </form>
    </div>
</body>
</html>
"""

# Form 4: Cek Status Kepesertaan (pilih NIK atau No Kartu, arahkan ke MJKN resmi)
HTML_STATUS_KEPESERTAAN = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Cek Status Kepesertaan</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <h2 class="text-center text-primary mb-4">Cek Status Kepesertaan BPJS</h2>
        <div class="alert alert-info">
            Untuk cek status akurat & aman, gunakan aplikasi resmi <strong>Mobile JKN</strong>.
        </div>
        <form action="/submit_status" method="post">
            <div class="mb-3">
                <label class="form-label">Pilih Jenis Pencarian</label>
                <select name="jenis_cari" class="form-select" onchange="toggleInput(this.value)">
                    <option value="nik">NIK (16 digit)</option>
                    <option value="nokartu">Nomor Kartu BPJS (13 digit)</option>
                </select>
            </div>
            <div class="mb-3" id="input_nik">
                <label class="form-label">NIK</label>
                <input type="text" name="nik" class="form-control" maxlength="16" placeholder="Contoh: 3171234567890123" required>
            </div>
            <div class="mb-3" id="input_nokartu" style="display:none;">
                <label class="form-label">Nomor Kartu BPJS</label>
                <input type="text" name="nokartu" class="form-control" maxlength="13" placeholder="Contoh: 0001234567890">
            </div>
            <button type="submit" class="btn btn-primary">Catat & Buka Mobile JKN</button>
            <a href="/" class="btn btn-secondary ms-2">Kembali</a>
        </form>
        <script>
            function toggleInput(value) {
                document.getElementById('input_nik').style.display = value === 'nik' ? 'block' : 'none';
                document.getElementById('input_nokartu').style.display = value === 'nokartu' ? 'block' : 'none';
                if (value === 'nik') {
                    document.querySelector('input[name="nik"]').required = true;
                    document.querySelector('input[name="nokartu"]').required = false;
                } else {
                    document.querySelector('input[name="nik"]').required = false;
                    document.querySelector('input[name="nokartu"]').required = true;
                }
            }
        </script>
        <div class="text-center mt-4">
            <p>Belum punya Mobile JKN?</p>
            <a href="https://play.google.com/store/apps/details?id=app.bpjs.mobile" target="_blank" class="btn btn-success me-2">Download Android</a>
            <a href="https://apps.apple.com/id/app/mobile-jkn/id1181438635" target="_blank" class="btn btn-success">Download iOS</a>
        </div>
    </div>
</body>
</html>
"""

# Form 5: Pendaftaran UHC
HTML_UHC = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Pendaftaran UHC</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <h2 class="text-center text-primary mb-4">Pendaftaran Universal Health Coverage (UHC)</h2>
        <form action="/submit_uhc" method="post">
            <div class="mb-3"><label class="form-label">Nama Lengkap</label><input type="text" name="nama" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">NIK</label><input type="text" name="nik" class="form-control" required></div>
            <div class="mb-3"><label class="form-label">Alamat</label><textarea name="alamat" class="form-control" rows="3" required></textarea></div>
            <div class="mb-3"><label class="form-label">No. Telepon</label><input type="text" name="telepon" class="form-control" required></div>
            <button type="submit" class="btn btn-primary">Ajukan Pendaftaran UHC</button>
            <a href="/" class="btn btn-secondary ms-2">Kembali</a>
        </form>
    </div>
</body>
</html>
"""

# Halaman 6: Capaian MJKN (data dummy)
HTML_MJKN = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Capaian Penggunaan Mobile JKN</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <h2 class="text-center text-primary mb-4">Capaian Penggunaan Mobile JKN (MJKN)</h2>
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">Statistik Bulan Desember 2025</h5>
            </div>
            <div class="card-body">
                <ul class="list-group list-group-flush">
                    <li class="list-group-item"><strong>Total Pengguna Aktif:</strong> 2.450.000 orang</li>
                    <li class="list-group-item"><strong>Pendaftaran Online:</strong> 156.000 orang</li>
                    <li class="list-group-item"><strong>Cek Status Kepesertaan:</strong> 489.000 kali</li>
                    <li class="list-group-item"><strong>Capaian Target Nasional:</strong> 94%</li>
                </ul>
                <div class="text-center mt-4">
                    <img src="https://via.placeholder.com/800x400?text=Grafik+Capaian+Mobile+JKN+Desember+2025" class="img-fluid rounded shadow">
                    <small class="text-muted d-block mt-2">Grafik capaian penggunaan Mobile JKN</small>
                </div>
            </div>
        </div>
        <div class="text-center mt-4">
            <a href="/" class="btn btn-secondary">Kembali ke Dashboard</a>
        </div>
    </div>
</body>
</html>
"""

# Halaman Login Admin
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Login Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-4">
                <div class="card shadow">
                    <div class="card-body">
                        <h3 class="text-center mb-4">Login Admin PIPP</h3>
                        {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
                        <form action="/login" method="post">
                            <div class="mb-3"><label class="form-label">Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                        <a href="/" class="btn btn-secondary w-100 mt-3">Kembali</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Halaman Admin Dashboard
HTML_ADMIN_DASH = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Admin Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-4">
        <h2 class="text-center text-danger mb-4">ADMIN DASHBOARD PIPP</h2>
        <div class="row mb-4">
            <div class="col-md-6"><h5 class="text-center">Pengaduan vs KESSAN</h5>
                <img src="/grafik_total" class="img-fluid border rounded shadow"></div>
            <div class="col-md-6"><h5 class="text-center">Jenis Pengaduan</h5>
                <img src="/grafik_jenis" class="img-fluid border rounded shadow"></div>
        </div>
        <div class="text-center mb-4">
            <a href="/export_excel" class="btn btn-success me-3">Export Excel</a>
            <a href="/export_pdf" class="btn btn-danger me-3">Export PDF</a>
            <a href="/" class="btn btn-secondary">Kembali</a>
        </div>
        <hr>
        <h4 class="text-center">Daftar Laporan</h4>
        {% for lap in laporan %}
        <div class="card mb-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <strong>{{ lap.Waktu_Jenis }}</strong>
                    <div class="text-end">
                        <span class="badge {% if lap.get('Status', '') == 'Selesai' %}bg-success{% else %}bg-warning text-dark{% endif %} fs-6 px-3 py-2">
                            {{ lap.get('Status', 'Sedang Ditindaklanjuti') }}
                        </span>
                        <form action="/update_status" method="post" class="mt-2">
                            <input type="hidden" name="id" value="{{ lap.ID }}">
                            <div class="input-group input-group-sm">
                                <select name="status" class="form-select">
                                    <option value="Sedang Ditindaklanjuti" {% if lap.get('Status', '') != 'Selesai' %}selected{% endif %}>Sedang Ditindaklanjuti</option>
                                    <option value="Selesai" {% if lap.get('Status', '') == 'Selesai' %}selected{% endif %}>Selesai</option>
                                </select>
                                <button type="submit" class="btn btn-primary">Update</button>
                            </div>
                        </form>
                    </div>
                </div>
                <hr>
                {% for k, v in lap.items() %}
                    {% if k not in ['Waktu_Jenis', 'ID', 'Status'] %}
                    <strong>{{ k }}:</strong> {{ v }}<br>
                    {% endif %}
                {% endfor %}
                {% if 'Gambar' in lap %}
                <img src="/uploads/{{ lap.Gambar }}" class="img-fluid mt-3 rounded shadow" style="max-height: 400px;">
                {% endif %}
            </div>
        </div>
        {% else %}
        <p class="text-center text-muted">Belum ada laporan masuk.</p>
        {% endfor %}
    </div>
</body>
</html>
"""

# Route-route aplikasi
@app.route('/')
def dashboard():
    return render_template_string(HTML_DASHBOARD)

@app.route('/pengaduan')
def pengaduan():
    return render_template_string(HTML_PENGADUAN)

@app.route('/kessan')
def kessan():
    return render_template_string(HTML_KESSAN)

@app.route('/bayi_baru_lahir')
def bayi_baru_lahir():
    return render_template_string(HTML_BAYI_BARU_LAHIR)

@app.route('/denda_pelayanan')
def denda_pelayanan():
    return render_template_string(HTML_DENDA_PELAYANAN)

@app.route('/status_kepesertaan')
def status_kepesertaan():
    return render_template_string(HTML_STATUS_KEPESERTAAN)

@app.route('/uhc')
def uhc():
    return render_template_string(HTML_UHC)

@app.route('/mjkn')
def mjkn():
    return render_template_string(HTML_MJKN)

# Submit form-form
@app.route('/submit_pengaduan', methods=['POST'])
def submit_pengaduan():
    nama = request.form.get('nama', 'Anonim')
    jenis = request.form['jenis']
    isi = request.form['isi']
    gambar_nama = None
    if 'gambar' in request.files:
        file = request.files['gambar']
        if file and file.filename != '':
            gambar_nama = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_") + file.filename.replace(" ", "_")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], gambar_nama))
    data = {"Nama": nama, "Jenis Pengaduan": jenis, "Isi Pengaduan": isi}
    simpan_laporan("PENGADUAN", data, gambar_nama)
    return '<h3 class="text-center text-success mt-5">Pengaduan berhasil dikirim!</h3><p class="text-center"><a href="/" class="btn btn-primary">Kembali</a></p>'

@app.route('/submit_kessan', methods=['POST'])
def submit_kessan():
    data = {
        "Nama": request.form.get('nama', 'Anonim'),
        "Kesan": request.form['kesan'],
        "Pesan/Saran": request.form.get('pesan', '-')
    }
    simpan_laporan("KESSAN", data)
    return '<h3 class="text-center text-success mt-5">Terima kasih atas kesan dan pesan Anda!</h3><p class="text-center"><a href="/" class="btn btn-primary">Kembali</a></p>'

@app.route('/submit_bayi', methods=['POST'])
def submit_bayi():
    data = {
        "Nama Bayi": request.form['nama_bayi'],
        "Tanggal Lahir": request.form['tgl_lahir'],
        "Nama Orang Tua": request.form['nama_ortu'],
        "No BPJS Orang Tua": request.form['no_bpjs']
    }
    simpan_laporan("PENDAFTARAN BAYI BARU LAHIR", data)
    return '<h3 class="text-center text-success mt-5">Pendaftaran bayi baru lahir berhasil diajukan!</h3><p class="text-center"><a href="/" class="btn btn-primary">Kembali</a></p>'

@app.route('/submit_denda', methods=['POST'])
def submit_denda():
    data = {
        "No BPJS": request.form['no_bpjs'],
        "Tanggal Pelayanan": request.form['tgl_pelayanan']
    }
    simpan_laporan("CEK DENDA PELAYANAN", data)
    return '<h3 class="text-center text-success mt-5">Permintaan cek denda telah dikirim.</h3><p class="text-center"><a href="/" class="btn btn-primary">Kembali</a></p>'

@app.route('/submit_uhc', methods=['POST'])
def submit_uhc():
    data = {
        "Nama": request.form['nama'],
        "NIK": request.form['nik'],
        "Alamat": request.form['alamat'],
        "No Telepon": request.form['telepon']
    }
    simpan_laporan("PENDAFTARAN UHC", data)
    return '<h3 class="text-center text-success mt-5">Pendaftaran UHC berhasil diajukan!</h3><p class="text-center"><a href="/" class="btn btn-primary">Kembali</a></p>'

# Submit Cek Status Kepesertaan (catat permintaan & arahkan ke MJKN resmi)
@app.route('/submit_status', methods=['POST'])
def submit_status():
    jenis_cari = request.form['jenis_cari']
    if jenis_cari == "nik":
        identifier = request.form.get('nik', '').strip()
        identifier_type = "NIK"
    else:
        identifier = request.form.get('nokartu', '').strip()
        identifier_type = "Nomor Kartu BPJS"
    
    # Simpan permintaan ke laporan admin
    data_laporan = {"Jenis Pencarian": identifier_type, "Identifier": identifier}
    simpan_laporan("CEK STATUS KEPESERTAAN", data_laporan)
    
    return f"""
    <div class="container mt-5 text-center">
        <h3 class="text-success">Permintaan cek status telah dicatat!</h3>
        <p>Gunakan aplikasi <strong>Mobile JKN</strong> resmi untuk cek langsung:</p>
        <a href="https://mobilejkn.bpjs-kesehatan.go.id/" target="_blank" class="btn btn-primary me-3">Buka Mobile JKN</a>
        <p class="mt-3">Atau download dulu:</p>
        <a href="https://play.google.com/store/apps/details?id=app.bpjs.mobile" target="_blank" class="btn btn-success me-2">Android</a>
        <a href="https://apps.apple.com/id/app/mobile-jkn/id1181438635" target="_blank" class="btn btn-success">iOS</a>
        <p class="mt-4"><a href="/" class="btn btn-secondary">Kembali ke Dashboard</a></p>
    </div>
    """

# Login & Admin
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            return redirect(url_for('admin_dash'))
        else:
            return render_template_string(HTML_LOGIN, error="Password salah!")
    return render_template_string(HTML_LOGIN)

@app.route('/admin')
def admin_dash():
    laporan = baca_laporan_dengan_status()
    return render_template_string(HTML_ADMIN_DASH, laporan=laporan)

@app.route('/update_status', methods=['POST'])
def update_status_route():
    laporan_id = request.form['id']
    new_status = request.form['status']
    update_status(laporan_id, new_status)
    return redirect('/admin')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

# Grafik & Export
@app.route('/grafik_total')
def grafik_total():
    laporan = baca_laporan_dengan_status()
    if not laporan:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'Belum ada data', ha='center', va='center', fontsize=14)
    else:
        df = pd.DataFrame(laporan)
        df['Jenis'] = df['Waktu_Jenis'].apply(lambda x: x.split(' - ')[1] if ' - ' in x else 'Unknown')
        counts = df['Jenis'].value_counts()
        fig, ax = plt.subplots(figsize=(6,5))
        counts.plot.pie(autopct='%1.1f%%', ax=ax, startangle=90, colors=['#ff9999','#66b3ff','#99ff99'])
        ax.set_ylabel('')
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return send_file(buf, mimetype='image/png')

@app.route('/grafik_jenis')
def grafik_jenis():
    laporan = baca_laporan_dengan_status()
    if not laporan:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'Belum ada data pengaduan', ha='center', va='center', fontsize=14)
    else:
        df = pd.DataFrame(laporan)
        pengaduan = df[df['Waktu_Jenis'].str.contains('PENGADUAN', na=False)]
        if 'Jenis Pengaduan' not in pengaduan.columns or pengaduan.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'Belum ada data pengaduan', ha='center', va='center', fontsize=14)
        else:
            counts = pengaduan['Jenis Pengaduan'].value_counts()
            fig, ax = plt.subplots(figsize=(6,5))
            counts.plot.bar(ax=ax, color=['#ff9999', '#66b3ff', '#99ff99'])
            ax.set_ylabel('Jumlah')
            for i, v in enumerate(counts):
                ax.text(i, v + 0.1, str(v), ha='center')
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return send_file(buf, mimetype='image/png')

@app.route('/export_excel')
def export_excel():
    laporan = baca_laporan_dengan_status()
    df = pd.DataFrame(laporan)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="laporan_pipp.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/export_pdf')
def export_pdf():
    laporan = baca_laporan_dengan_status()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("Laporan PIPP BPJS Kesehatan", styles['Title']))
    elements.append(Spacer(1, 12))
    data = [["No", "Waktu", "Jenis", "Status", "Detail"]]
    for i, lap in enumerate(laporan, 1):
        detail = " | ".join([f"{k}: {v}" for k, v in lap.items() if k not in ["Waktu_Jenis", "ID", "Status", "Gambar"]])
        waktu = lap["Waktu_Jenis"].split(" - ")[0]
        jenis = lap["Waktu_Jenis"].split(" - ")[1] if " - " in lap["Waktu_Jenis"] else ""
        data.append([i, waktu, jenis, lap.get("Status", ""), detail])
    table = Table(data)
    table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey),
                               ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                               ('GRID',(0,0),(-1,-1),0.5,colors.black)]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="laporan_pipp.pdf", mimetype='application/pdf')

# Jalankan aplikasi
if __name__ == '__main__':

    app.run(host='0.0.0.0', port=8080)
