"""Capa do Reel 27/11 (Eulino Falante) — padrão capa 3 colorida, etiqueta do eixo LEGÍVEL (Pedro 27/11),
título dentro do recorte 3:4 da grade (y 240–1680). Gera 2 títulos x posição automática (longe do rosto)."""
import os
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter, ImageStat
import numpy as np, cv2, docker
B = Path("/dados/r2711/capa"); B.mkdir(parents=True, exist_ok=True)
FID = os.environ.get("FOTO_ID", "128brvDxXXwaBxgxO8tsKzDar5D19Cue1")
cs = docker.from_env().containers.get("assumpcao-sync")
def rc(*args):
    cmd = ['sh', '-c', 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"$GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; exec rclone "$@"', 'x', *args]
    r = cs.exec_run(cmd, demux=True); return r.exit_code, (r.output[1] or b"").decode()[-300:]
src = B / "src"; src.mkdir(exist_ok=True)
if not list(src.glob("*")): print("copyid", rc("backend", "copyid", "gdrive:", FID, str(src) + "/"), flush=True)
foto = sorted(src.glob("*"))[0]; W, H = 1080, 1920
im0 = ImageOps.fit(ImageOps.exif_transpose(Image.open(foto)).convert("RGB"), (W, H), Image.LANCZOS)
g = cv2.cvtColor(np.array(im0), cv2.COLOR_RGB2GRAY)
fc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml").detectMultiScale(g, 1.1, 6, minSize=(150, 150))
face = max(fc, key=lambda r: r[2] * r[3]) if len(fc) else None
print("foto", foto.name, "rosto", face, flush=True)
FONT = "/cache/fonts/Fraunces.ttf"
def fnt(s, w=400):
    f = ImageFont.truetype(FONT, s)
    try: f.set_variation_by_axes([144, w, 0, 0])
    except Exception: pass
    return f
YEL = (255, 204, 0)
TOP, BOT = 270, 1650          # dentro do recorte 3:4 (240–1680) com folga
def capa(nome, l1, l2, dest, eixo="criar", tam=118):
    im = im0.copy(); d = ImageDraw.Draw(im); f = fnt(tam, 500); x = 90
    alt = int(tam * 2.45) + 90
    if face is not None:
        fy0, fy1 = face[1], face[1] + face[3]
        y0 = TOP if (fy0 - TOP) >= alt + 40 else max(fy1 + 60, BOT - alt) if (BOT - fy1) >= alt + 40 else TOP
    else: y0 = TOP
    y0 = min(max(y0, TOP), BOT - alt)
    lum = ImageStat.Stat(im.crop((0, y0, W, y0 + alt)).convert("L")).mean[0]
    escuro = lum < 120; INK = (250, 250, 247) if escuro else (18, 18, 20); SH = (0, 0, 0) if escuro else None
    if escuro or lum < 160:   # faixa suave para leitura
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle((0, y0 - 60, W, y0 + alt + 30), fill=140 if escuro else 90)
        im = Image.composite(Image.new("RGB", (W, H), (12, 12, 14) if escuro else (245, 245, 240)), im, m.filter(ImageFilter.GaussianBlur(80))); d = ImageDraw.Draw(im)
    def linha(y, partes):
        cx = x
        for txt, hl in partes:
            if hl:
                bb = d.textbbox((cx, y), txt, font=f); d.rectangle((bb[0] - 10, bb[1] + int(tam * .18), bb[2] + 10, bb[3] + 6), fill=YEL)
                d.text((cx, y), txt, font=f, fill=(18, 18, 20))
            else:
                if SH: d.text((cx + 3, y + 4), txt, font=f, fill=SH)
                d.text((cx, y), txt, font=f, fill=INK)
            cx += d.textlength(txt, font=f)
    linha(y0, l1); linha(y0 + int(tam * 1.12), l2)
    yt = y0 + int(tam * 2.45)
    d.line([(x + 2, yt), (x + 170, yt)], fill=INK, width=6)
    fe = fnt(58, 600)                                    # etiqueta do eixo: maior e com peso (antes 38 fino)
    if SH: d.text((x + 2, yt + 22), eixo, font=fe, fill=SH)
    d.text((x, yt + 18), eixo, font=fe, fill=INK)
    im.save(B / f"{nome}.jpg", quality=93)
    pv = im.resize((405, 720), Image.LANCZOS); dp = ImageDraw.Draw(pv); dp.rectangle((0, 90, 404, 630), outline=(255, 0, 0), width=2)
    pv.save(B / f"{nome}_previa.jpg", quality=82)
    grade = im.crop((0, 240, W, 1680)).resize((360, 480), Image.LANCZOS); grade.save(B / f"{nome}_grade.jpg", quality=82)
    print(nome, "y0", y0, "lum", round(lum), "dentro do 3:4:", 240 <= y0 and y0 + alt + 80 <= 1680, flush=True)
capa("capa-r2711-A-censores", [("Os nossos", False)], [("censores", True)], None)
capa("capa-r2711-B-proibiu", [("Ninguém te", False)], [("proibiu", True)], None)
im0.resize((405, 720), Image.LANCZOS).save(B / "foto_previa.jpg", quality=80)
print("rclone", rc("copy", str(B), "gdrive:_analises/r2711/capa", "--exclude", "src/**"), flush=True)
print("FIM-CAPA", flush=True)
