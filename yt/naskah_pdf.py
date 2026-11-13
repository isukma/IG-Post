import sys
from reportlab.lib.pagesizes import A5
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from scripts import V
pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
H1 = ParagraphStyle("h1", fontName="DVB", fontSize=15, leading=19, spaceAfter=6)
H2 = ParagraphStyle("h2", fontName="DVB", fontSize=11, leading=14, textColor="#1d4ed8", spaceBefore=8, spaceAfter=3)
B = ParagraphStyle("b", fontName="DV", fontSize=12.5, leading=19)
S = ParagraphStyle("s", fontName="DV", fontSize=9.5, leading=13, textColor="#444444")
P = ParagraphStyle("p", fontName="DVB", fontSize=11, leading=15, textColor="#b45309", spaceBefore=4, spaceAfter=4)
import re
def human(t):
    rep=[("i a s c titik o j k titik go titik i d","iasc.ojk.go.id (baca: i-a-s-c titik o-j-k titik go titik i-d)"),
         ("Chat G P T","ChatGPT"),("Open A I","OpenAI"),("A P K","APK"),("O T P","OTP"),("O J K","OJK"),("I A S C","IASC"),
         ("A I-nya","AI-nya")]
    for a,b in rep: t=t.replace(a,b)
    return re.sub(r"\bA I\b","AI",t)
nums = [int(x) for x in sys.argv[2:]] or sorted(V)
doc = SimpleDocTemplate(sys.argv[1], pagesize=A5, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36,
                        title="Naskah Rekam YouTube @15ukma")
st = [Paragraph("Naskah Rekam YouTube @15ukma", H1),
      Paragraph("Cara merekam (sekali saja dibaca):", H2),
      Paragraph("1. Rekam di ruangan sunyi, HP 20–30 cm dari mulut, pakai aplikasi Perekam Suara bawaan HP.<br/>"
                "2. Baca dengan tempo santai seperti menjelaskan ke keluarga. Salah ucap? Diam 2 detik, ulangi kalimatnya. Tidak perlu mengulang dari awal.<br/>"
                "3. Di setiap tanda <b>JEDA 3 DETIK</b>, diam 3 detik penuh. Jeda inilah yang dipakai untuk menyinkronkan slide.<br/>"
                "4. Satu video = satu berkas. Beri nama v01, v02, dst. (format m4a/mp3/wav bebas).<br/>"
                "5. Kirim: unggah ke repo GitHub isukma/IG-Post, folder <b>yt-audio</b> (aplikasi GitHub di HP: Add file → Upload files), "
                "atau lampirkan langsung di percakapan Claude.", S), PageBreak()]
for k in nums:
    v = V[k]
    st.append(Paragraph(f"Video {k:02d} — simpan sebagai v{k:02d}", H1))
    st.append(Paragraph(v["title"], S)); st.append(Spacer(1, 6))
    for i, s in enumerate(v["segs"]):
        st.append(Paragraph(f"Bagian {i+1} · {s['t']}", H2))
        st.append(Paragraph(human(s["n"]), B))
        if i < len(v["segs"]) - 1: st.append(Paragraph("[ JEDA 3 DETIK ]", P))
    st.append(Paragraph("[ SELESAI. Hentikan rekaman. ]", P)); st.append(PageBreak())
doc.build(st)
