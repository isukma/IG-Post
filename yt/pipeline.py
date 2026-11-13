#!/usr/bin/env python3
"""Pengendali produksi YouTube @15ukma (dijalankan dari root repo isukma/IG-Post).

  python3 yt/pipeline.py status            -> ringkasan naskah, rekaman, dan jadwal
  python3 yt/pipeline.py render-pending    -> render semua rekaman baru di yt-audio/ yang naskahnya ada,
                                              salin MP4 + thumbnail ke media/yt/, tetapkan slot tayang,
                                              cetak JSON berisi URL raw GitHub + metadata untuk Metricool
  python3 yt/pipeline.py mark vNN <metricool_post_id>   -> catat bahwa vNN sudah terjadwal di Metricool

Aturan slot: setiap video mengambil slot kosong paling awal yang waktunya >= sekarang + 45 menit.
Slot dasar: 13 Nov 2026 19.00 WIB, lalu setiap hari 16.00 WIB (puncak audiens YouTube menurut Metricool).
"""
import json, os, re, subprocess, sys, shutil, glob, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YT = os.path.join(ROOT, "yt"); AUD = os.path.join(ROOT, "yt-audio"); MED = os.path.join(ROOT, "media", "yt")
STATE = os.path.join(YT, "state.json")
RAW = "https://raw.githubusercontent.com/isukma/IG-Post/main/"
WIB = dt.timezone(dt.timedelta(hours=7))
sys.path.insert(0, YT)

def load():
    if os.path.exists(STATE): return json.load(open(STATE))
    return {"videos": {}}

def save(s): json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=2)

def base_slots(n=60):
    slots = [dt.datetime(2026, 11, 13, 19, 0, tzinfo=WIB)]
    d = dt.datetime(2026, 11, 14, 16, 0, tzinfo=WIB)
    for i in range(n): slots.append(d + dt.timedelta(days=i))
    return slots

def next_slot(state):
    taken = {v["slot"] for v in state["videos"].values() if v.get("slot")}
    floor = dt.datetime.now(WIB) + dt.timedelta(minutes=45)
    for s in base_slots():
        iso = s.isoformat()
        if s >= floor and iso not in taken: return iso
    raise SystemExit("slot habis")

def recordings():
    out = {}
    for p in sorted(glob.glob(os.path.join(AUD, "v*.*"))):
        m = re.match(r"v(\d+)\.(m4a|mp3|wav|ogg|aac|opus|webm|mp4|3gp|amr)$", os.path.basename(p), re.I)
        if m: out[int(m.group(1))] = p
    return out

def cmd_status():
    from scripts import V
    s = load(); rec = recordings()
    rows = []
    for k in sorted(set(V) | set(rec)):
        st = s["videos"].get(f"v{k:02d}", {})
        rows.append(dict(no=k, naskah=k in V, rekaman=k in rec, slot=st.get("slot"), metricool=st.get("post_id")))
    print(json.dumps(rows, ensure_ascii=False, indent=1))

def cmd_render():
    from scripts import V
    s = load(); rec = recordings(); os.makedirs(MED, exist_ok=True); ready = []
    for k, path in rec.items():
        key = f"v{k:02d}"
        if key in s["videos"] and s["videos"][key].get("post_id"): continue
        if k not in V: print(f"# {key}: rekaman ada, naskah belum ada di scripts.py", file=sys.stderr); continue
        r = subprocess.run([sys.executable, os.path.join(YT, "render.py"), str(k), path, "--voice", "own",
                            "--out", os.path.join(YT, "_out")], capture_output=True, text=True)
        if r.returncode: print(f"# {key}: render gagal\n{r.stderr[-1500:]}", file=sys.stderr); continue
        slug = V[k]["slug"]; o = os.path.join(YT, "_out")
        shutil.copy(os.path.join(o, slug + ".mp4"), os.path.join(MED, slug + ".mp4"))
        shutil.copy(os.path.join(o, slug + "_thumb.jpg"), os.path.join(MED, slug + "_thumb.jpg"))
        meta = json.load(open(os.path.join(o, slug + "_meta.json")))
        ent = s["videos"].get(key, {})
        ent.update(slug=slug, slot=ent.get("slot") or next_slot(s), duration=meta["duration"])
        s["videos"][key] = ent; save(s)
        ready.append(dict(key=key, slot=ent["slot"], video_url=RAW + f"media/yt/{slug}.mp4",
                          thumb_url=RAW + f"media/yt/{slug}_thumb.jpg", title=meta["title"],
                          description=meta["description"], tags=meta["tags"], duration=meta["duration"]))
    print(json.dumps(ready, ensure_ascii=False, indent=1))

def cmd_mark(key, post_id):
    s = load(); s["videos"].setdefault(key, {})["post_id"] = post_id; save(s); print("ok", key, post_id)

if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"status": cmd_status, "render-pending": cmd_render}.get(c, lambda: cmd_mark(sys.argv[2], sys.argv[3]))() \
        if c != "mark" else cmd_mark(sys.argv[2], sys.argv[3])
