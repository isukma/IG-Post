#!/usr/bin/env python3
"""Mesin render video YouTube @15ukma.

Pemakaian:
  python3 render.py <no_video> <berkas_audio> [--voice own|ai] [--out DIR]

- Audio boleh MP3/M4A/WAV/OGG (rekaman HP). Dibersihkan dan diseragamkan ke -14 LUFS.
- Batas antarsegmen dicari dari jeda dalam rekaman yang paling dekat dengan posisi
  perkiraan (proporsi jumlah kata). Jeda 2-3 detik antarbagian saat merekam membuat
  sinkronisasi paling tepat.
- Keluaran: <slug>.mp4 (1920x1080, H.264/AAC), <slug>_thumb.jpg (1280x720),
  <slug>_meta.json (judul, deskripsi dengan bab waktu, tag).
"""
import json, os, re, subprocess, sys, argparse, textwrap
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts import V

W, H = 1920, 1080
FONT_DIR = "/usr/share/fonts/opentype/inter/"
def F(size, weight="Bold"):
    return ImageFont.truetype(FONT_DIR + f"Inter-{weight}.otf", size)

BG1, BG2 = (11, 22, 44), (20, 38, 72)
WHITE, MUTED = (245, 247, 250), (160, 175, 200)

def hex2rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr[-3000:])
    return r

def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", path]).stdout.strip())

def silences(path, noise="-35dB", d=0.7):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af",
                        f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
                       capture_output=True, text=True)
    out, start = [], None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m: start = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", line)
        if m and start is not None:
            out.append((start, float(m.group(1)), float(m.group(2)))); start = None
    return out

def boundaries(audio, segs, total):
    words = [len(s["n"].split()) for s in segs]
    tot = sum(words); cum = 0; exp = []
    for w in words[:-1]:
        cum += w; exp.append(total * cum / tot)
    sil = silences(audio)
    bounds, last = [], 0.0
    for e in exp:
        win = max(12.0, total * 0.08)
        cands = [s for s in sil if abs((s[0]+s[1])/2 - e) <= win and s[0] > last + 3]
        if cands:
            best = max(cands, key=lambda s: s[2] - abs((s[0]+s[1])/2 - e) / win)
            b = (best[0] + best[1]) / 2
        else:
            b = max(e, last + 3)
        bounds.append(b); last = b
    return [0.0] + bounds + [total]

def bg(accent):
    img = Image.new("RGB", (W, H), BG1)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(BG1[i]*(1-t) + BG2[i]*t) for i in range(3)))
    # grid tipis
    for x in range(0, W, 80):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 8) if False else (24, 40, 70))
    for y in range(0, H, 80):
        d.line([(0, y), (W, y)], fill=(24, 40, 70))
    return img

def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def slide(v, si, nshow, voice):
    acc = hex2rgb(v["accent"])
    img = bg(acc); d = ImageDraw.Draw(img)
    seg = v["segs"][si]; n = len(v["segs"])
    # header
    d.text((110, 70), "@15ukma", font=F(34), fill=WHITE)
    d.text((110 + d.textlength("@15ukma ", font=F(34)), 76), "· Aman digital, tanpa ribet", font=F(28, "Medium"), fill=MUTED)
    # progress dots
    for i in range(n):
        x = W - 110 - (n - i) * 34
        d.ellipse([x, 84, x + 18, 102], fill=acc if i <= si else (52, 70, 104))
    # accent bar + title
    d.rectangle([110, 220, 122, 330], fill=acc)
    tf = F(72, "ExtraBold")
    lines = wrap(d, seg["t"], tf, W - 360)
    y = 210
    for ln in lines[:2]:
        d.text((160, y), ln, font=tf, fill=WHITE); y += 92
    y += 50
    pf = F(46, "SemiBold")
    for i, p in enumerate(seg["p"]):
        if i >= nshow: break
        pl = wrap(d, p, pf, W - 420)
        d.rounded_rectangle([160, y + 14, 186, y + 40], radius=6, fill=acc)
        for j, ln in enumerate(pl):
            d.text((220, y), ln, font=pf, fill=WHITE if i == nshow - 1 else (215, 222, 235)); y += 62
        y += 26
    # footer
    d.line([(110, H - 120), (W - 110, H - 120)], fill=(52, 70, 104), width=2)
    foot = "Konten edukasi literasi digital · bukan pernyataan resmi instansi mana pun"
    if voice == "ai": foot += " · narasi suara AI"
    if voice == "clone": foot += " · narasi: suara kloning AI pemilik channel"
    d.text((110, H - 95), foot, font=F(26, "Medium"), fill=MUTED)
    d.text((W - 110 - d.textlength(f"{si+1}/{n}", font=F(26)), H - 95), f"{si+1}/{n}", font=F(26), fill=MUTED)
    return img

def thumb(v, path):
    acc = hex2rgb(v["accent"])
    img = bg(acc).resize((1280, 720)); d = ImageDraw.Draw(img)
    big, sub, tag = v["thumb"]
    bf = F(118, "Black") if os.path.exists(FONT_DIR + "Inter-Black.otf") else F(118, "ExtraBold")
    lines = wrap(d, big, bf, 1160)
    while len(lines) > 2:
        bf = ImageFont.truetype(bf.path, bf.size - 10); lines = wrap(d, big, bf, 1160)
    y = 150
    for ln in lines:
        d.text((60, y), ln, font=bf, fill=acc if ln is lines[0] else WHITE); y += bf.size + 12
    d.rectangle([60, y + 20, 72, y + 90], fill=acc)
    d.text((95, y + 22), sub, font=F(54, "Bold"), fill=WHITE)
    tf = F(40, "Bold"); tw = d.textlength(tag, font=tf)
    d.rounded_rectangle([60, 600, 60 + tw + 50, 670], radius=14, fill=acc)
    d.text((85, 612), tag, font=tf, fill=(10, 18, 36))
    d.text((1280 - 60 - d.textlength("@15ukma", font=F(36)), 620), "@15ukma", font=F(36), fill=WHITE)
    img.save(path, quality=92)

def ts(sec):
    sec = int(round(sec)); return f"{sec//60:02d}:{sec%60:02d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("no", type=int); ap.add_argument("audio")
    ap.add_argument("--voice", default="own", choices=["own", "ai", "clone"])
    ap.add_argument("--first", type=int, default=0, help="uji: hanya N segmen pertama")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out"))
    a = ap.parse_args()
    a.out = os.path.abspath(a.out); v = dict(V[a.no]); os.makedirs(a.out, exist_ok=True)
    if a.first: v["segs"] = v["segs"][:a.first]; v["slug"] += "_TEST"
    work = os.path.join(a.out, v["slug"] + "_work"); os.makedirs(work, exist_ok=True)

    # 1. bersihkan audio: buang hening awal/akhir, peredam derau ringan, loudness -14 LUFS
    clean = os.path.join(work, "voice.m4a")
    af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.3,"
          "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.6,areverse,"
          "highpass=f=80,afftdn=nf=-25,loudnorm=I=-14:TP=-1.5:LRA=11")
    if a.voice in ("ai", "clone"):
        af = "loudnorm=I=-14:TP=-1.5:LRA=11"
    run(["ffmpeg", "-y", "-hide_banner", "-i", a.audio, "-af", af, "-ar", "48000", "-ac", "2",
         "-c:a", "aac", "-b:a", "192k", clean])
    total = duration(clean)
    b = boundaries(clean, v["segs"], total)

    # 2. slide bertahap: setiap poin muncul berurutan dalam segmennya
    lines, chapters = [], []
    for si, seg in enumerate(v["segs"]):
        s0, s1 = b[si], b[si+1]; k = max(1, len(seg["p"]))
        chapters.append((s0, seg["t"]))
        step = (s1 - s0) / k
        for j in range(k):
            p = os.path.join(work, f"s{si:02d}_{j}.png")
            slide(v, si, j + 1, a.voice).save(p)
            lines.append(f"file '{p}'\nduration {step:.3f}")
    lines.append(f"file '{p}'")  # syarat concat demuxer
    lst = os.path.join(work, "list.txt"); open(lst, "w").write("\n".join(lines) + "\n")

    mp4 = os.path.join(a.out, v["slug"] + ".mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-f", "concat", "-safe", "0", "-i", lst, "-i", clean,
         "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
         "-crf", "20", "-c:a", "copy", "-shortest", "-movflags", "+faststart", mp4])
    thumb(v, os.path.join(a.out, v["slug"] + "_thumb.jpg"))

    # 3. deskripsi dengan bab waktu (bab pertama 00:00, minimal 10 detik per bab)
    ch = [c for i, c in enumerate(chapters) if i == 0 or c[0] - chapters[i-1][0] >= 10]
    chap = "\n".join(f"{ts(t)} {name}" for t, name in ch)
    voice_note = {"own": "Narasi dibacakan langsung oleh pemilik channel.",
                  "clone": "Narasi dibuat dengan suara kloning AI dari suara pemilik channel, atas izin dan naskah pemilik channel sendiri.",
                  "ai": "Narasi menggunakan suara sintetis AI."}[a.voice]
    desc = (f"{v['intro']}\n\nDi video ini:\n{chap}\n\n{v['links']}\n\n{v['refs']}\n\n"
            f"Konten edukasi literasi digital, bukan pernyataan resmi instansi mana pun. {voice_note}\n\n{v['hashtags']}")
    meta = dict(title=v["title"], description=desc, tags=v["tags"], duration=round(duration(mp4), 1),
                boundaries=[round(x, 2) for x in b])
    json.dump(meta, open(os.path.join(a.out, v["slug"] + "_meta.json"), "w"), ensure_ascii=False, indent=2)
    print(json.dumps({"mp4": mp4, "duration": meta["duration"], "size_mb": round(os.path.getsize(mp4)/1e6, 1),
                      "boundaries": meta["boundaries"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
