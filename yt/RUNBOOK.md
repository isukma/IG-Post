# RUNBOOK — Produksi Harian YouTube @15ukma

Repo: `isukma/IG-Post` (publik, dipakai sebagai inang berkas untuk Metricool).
Metricool brand: `15ukma`, blogId `7328338`, zona waktu `Asia/Jakarta`, YouTube channel `UC2Hl31l68Kl5cW5W25lcreA`.
Dokumen strategi: Claude Docs "YouTube @15ukma — Positioning, 30 Ide Video..." dan project doc
`claude/YT-15ukma-positioning-30-ide-5-video-jadwal-Nov-Des-2026.md` (daftar 30 ide ada di bagian 3 dokumen Docs).

## Struktur
- `yt/scripts.py` — naskah narasi + data slide per video (`V[n]`).
- `yt/render.py` — perakit video 1920x1080 dari rekaman + slide; sinkron lewat jeda 3 detik antarbagian.
- `yt/naskah_pdf.py` — pembuat lembar naskah rekam (PDF A5) untuk pemilik channel.
- `yt/pipeline.py` — `status`, `render-pending`, `mark vNN <post_id>`.
- `yt-audio/vNN.m4a|mp3|wav` — rekaman suara asli pemilik channel (diunggah oleh pemilik).
- `media/yt/` — MP4 dan thumbnail siap tarik oleh Metricool (boleh dikosongkan setelah posting berstatus terjadwal, karena Metricool menyalin berkas ke CDN-nya).
- `yt/state.json` — slot tayang dan ID posting Metricool per video.

## Langkah setiap putaran
1. Clone repo, `git pull`. Jalankan `python3 yt/pipeline.py status`.
2. **Rekaman baru**: `python3 yt/pipeline.py render-pending`. Lihat satu frame tengah tiap MP4 (ffmpeg -ss) untuk memastikan slide tampil. Commit + push `media/yt/` dan `yt/state.json`. Pastikan URL raw mengembalikan HTTP 200.
3. **Jadwalkan** setiap item di Metricool `createScheduledPost`:
   - `providers: [{"network":"youtube"}]`, `media: [video_url]`, `text: description`, `autoPublish: true`
   - `youtubeData: {title, type:"video", privacy:"public", tags, category:"EDUCATION", madeForKids:false, isAiGeneratedContent:false}`
   - `publicationDate: {dateTime: slot tanpa offset, timezone:"Asia/Jakarta"}`
   - Jangan kirim `videoThumbnailUrl` (channel belum terverifikasi; Metricool menolak seluruh permintaan).
   - Lalu `python3 yt/pipeline.py mark vNN <id>`; commit + push.
4. **Naskah lanjutan**: jaga minimal 5 naskah yang belum direkam. Bila kurang, tulis 2 naskah berikutnya dari daftar 30 ide (urutan 6, 7, 8, ...):
   - Riset fakta ke sumber resmi (OJK, Komdigi, BSSN, peraturan, pusat bantuan aplikasi). Setiap angka harus punya sumber dan tanggal. Tanpa politik, tanpa SARA, tanpa data internal instansi, tanpa nama korban/pelaku.
   - Format sama dengan `V[1..5]`: 8–10 segmen, 700–1.000 kata, angka dieja, hook 15 detik di segmen 1, penutup "Aman digital, tanpa ribet."
   - Buat PDF `python3 yt/naskah_pdf.py yt/Naskah-Rekam-Video-NN.pdf NN ...`, commit + push.
   - Kirim notifikasi ke pemilik: naskah mana yang siap direkam dan tautan PDF-nya (`https://github.com/isukma/IG-Post/blob/main/yt/...`).
5. **Laporan singkat**: video yang terjadwal (tanggal/jam), rekaman yang ditunggu, naskah baru. Bila slot hari ini/besok kosong karena belum ada rekaman, sebutkan dengan jelas.

## Larangan
- Jangan pernah memakai suara AI untuk video tayang (pilihan pemilik: suara sendiri; paket ElevenLabs gratis tidak berlisensi komersial).
- Jangan mengunggah ulang video yang sudah punya `post_id`.
- Jangan menghapus rekaman di `yt-audio/`.
