"""Capa do Reel 27/11 (Eulino Falante) — padrão capa 3 colorida, etiqueta do eixo LEGÍVEL (Pedro 27/11),
título dentro do recorte 3:4 da grade (y 240–1680). Gera 2 títulos x posição automática (longe do rosto)."""
import os
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter, ImageStat
import numpy as np, docker
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
from PIL import ImageEnhance
# Pedro 27/11: branco estourado -> baixa os claros (curva) e sobe o contraste
lut = [int(255 * ((i / 255) ** 1.35)) for i in range(256)]
im0 = im0.point(lut * 3)
im0 = ImageEnhance.Contrast(im0).enhance(1.18)
im0 = ImageEnhance.Color(im0).enhance(1.06)
g = np.asarray(im0.convert("L"), dtype=np.float32)
def calma(y0, y1):  # menos detalhe = melhor lugar para o título
    a = g[y0:y1]; return float(np.abs(np.diff(a, axis=1)).mean() + np.abs(np.diff(a, axis=0)).mean())
face = None
CALMA = {"topo": calma(270, 700), "base": calma(1220, 1650)}
print("foto", foto.name, "calma", CALMA, flush=True)
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
    alt = int(tam * 2.45) + 110
    y0 = TOP if CALMA["topo"] <= CALMA["base"] else BOT - alt
    y0 = min(max(y0, TOP), BOT - alt)
    lum = ImageStat.Stat(im.crop((0, y0, W, y0 + alt)).convert("L")).mean[0]
    escuro = lum < 120; INK = (250, 250, 247) if escuro else (18, 18, 20); SH = (0, 0, 0) if escuro else None
    if escuro:   # faixa escura só se o fundo for escuro (a faixa clara estourava o branco)
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rectangle((0, y0 - 60, W, y0 + alt + 60), fill=140 if escuro else 130)
        im = Image.composite(Image.new("RGB", (W, H), (12, 12, 14) if escuro else (245, 245, 240)), im, m.filter(ImageFilter.GaussianBlur(80))); d = ImageDraw.Draw(im)
    def linha(y, partes):
        cx = x
        for txt, hl in partes:
            if hl:
                bb = d.textbbox((cx, y), txt, font=f); d.rectangle((bb[0] - 12, bb[1] - 4, bb[2] + 12, bb[3] + 12), fill=YEL)   # marca-texto na palavra inteira
                d.text((cx, y), txt, font=f, fill=(18, 18, 20))
            else:
                if SH: d.text((cx + 3, y + 4), txt, font=f, fill=SH)
                d.text((cx, y), txt, font=f, fill=INK)
            cx += d.textlength(txt, font=f)
    linha(y0, l1); linha(y0 + int(tam * 1.12), l2)
    yt = y0 + int(tam * 2.45)
    d.line([(x + 2, yt), (x + 190, yt)], fill=INK, width=7)
    fe = fnt(74, 700)                                    # etiqueta do eixo: maior e com peso (antes 38 fino)
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
