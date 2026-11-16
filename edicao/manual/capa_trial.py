"""Capa do Trial "qualquer criança faz" no padrão capa 3 (colorida): foto inteira, título Fraunces em 2 linhas,
palavra de destaque em amarelo #FFCC00, traço curto e nome do eixo. Gera 2 opções de posição + prévias pequenas."""
import os, subprocess
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter
import docker

B = Path("/dados/trial1311/capa"); B.mkdir(parents=True, exist_ok=True)
FID = os.environ.get("FOTO_ID", "1OAYNsIlGv2Sc1Pzvj9FggC9bopgOj4bH")
cs = docker.from_env().containers.get("assumpcao-sync")
def rc(*args):
    cmd = ['sh', '-c', 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"$GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; exec rclone "$@"', 'x', *args]
    r = cs.exec_run(cmd, demux=True); return r.exit_code, (r.output[1] or b"").decode()[-300:]

src_dir = B / "src"; src_dir.mkdir(exist_ok=True)
if not list(src_dir.glob("*")): print("copyid", rc("backend", "copyid", "gdrive:", FID, str(src_dir) + "/"), flush=True)
foto = sorted(src_dir.glob("*"))[0]
W, H = 1080, 1920
im0 = ImageOps.exif_transpose(Image.open(foto)).convert("RGB")
print("foto", foto.name, im0.size, flush=True)
im0 = ImageOps.fit(im0, (W, H), Image.LANCZOS, centering=(0.5, 0.5))
FONT = "/cache/fonts/Fraunces.ttf"
def fnt(s):
    f = ImageFont.truetype(FONT, s)
    try: f.set_variation_by_axes([144, 400, 0, 0]) if len(f.get_variation_axes()) == 4 else None
    except Exception: pass
    return f
YEL, WHITE = (255, 204, 0), (250, 250, 247)

def capa(nome, y0, tam, sombra_de, sombra_ate):
    im = im0.copy()
    # escurece de leve só a faixa do título, para leitura (degradê suave)
    faixa = Image.new("L", (W, H), 0); d = ImageDraw.Draw(faixa)
    d.rectangle((0, sombra_de, W, sombra_ate), fill=150)
    faixa = faixa.filter(ImageFilter.GaussianBlur(90))
    im = Image.composite(Image.new("RGB", (W, H), (12, 12, 14)), im, faixa)
    d = ImageDraw.Draw(im); f = fnt(tam); x = 90
    def linha(y, partes):
        cx = x
        for txt, cor in partes:
            d.text((cx + 3, y + 4), txt, font=f, fill=(0, 0, 0))      # sombra curta
            d.text((cx, y), txt, font=f, fill=cor); cx += d.textlength(txt, font=f)
    linha(y0, [("Qualquer", WHITE)])
    linha(y0 + int(tam * 1.12), [("criança", YEL), (" faz", WHITE)])
    yt = y0 + int(tam * 2.45)
    d.line([(x + 2, yt), (x + 150, yt)], fill=WHITE, width=4)
    d.text((x, yt + 18), "arte", font=fnt(38), fill=WHITE)
    # guia do recorte 3:4 da grade só na prévia
    im.save(B / f"{nome}.jpg", quality=93)
    pv = im.resize((405, 720), Image.LANCZOS); dp = ImageDraw.Draw(pv)
    dp.rectangle((0, 90, 404, 630), outline=(255, 0, 0), width=1)
    pv.save(B / f"{nome}_previa.jpg", quality=80)

# ---------- opção C: título no alto, para onde o dedo aponta ----------
import numpy as np, cv2
arr = cv2.cvtColor(np.array(im0), cv2.COLOR_RGB2BGR)
# tira o reflexo redondo (anel de luz) no vidro de um quadro
cx, cy, rr = int(os.environ.get("ANEL_X", "456")), int(os.environ.get("ANEL_Y", "720")), int(os.environ.get("ANEL_R", "44"))
m = np.zeros(arr.shape[:2], np.uint8); cv2.circle(m, (cx, cy), rr, 255, -1)
arr = cv2.inpaint(arr, m, 7, cv2.INPAINT_TELEA)
limpa = Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))
DESCE = 300                                            # desce a foto e continua a parede lisa no alto
base = Image.new("RGB", (W, H)); topo = limpa.crop((0, 0, W, 24)).resize((W, DESCE + 24), Image.BILINEAR).filter(ImageFilter.GaussianBlur(18))
base.paste(topo, (0, 0)); base.paste(limpa.crop((0, 0, W, H - DESCE)), (0, DESCE))
# emenda suave entre a parede continuada e a foto
faixa = base.crop((0, DESCE - 30, W, DESCE + 30)).filter(ImageFilter.GaussianBlur(12)); base.paste(faixa, (0, DESCE - 30))
d = ImageDraw.Draw(base); INK = (20, 20, 22); tam = 112; f = fnt(tam); x = 90; y = 268
d.text((x, y), "Qualquer", font=f, fill=INK)
y2 = y + int(tam * 1.12); wcr = d.textlength("criança", font=f)
bb = d.textbbox((x, y2), "criança", font=f)
d.rectangle((bb[0] - 10, bb[1] + int(tam * 0.18), bb[2] + 10, bb[3] + 6), fill=YEL)      # marca-texto amarelo
d.text((x, y2), "criança", font=f, fill=INK); d.text((x + wcr, y2), " faz", font=f, fill=INK)
yt = y + int(tam * 2.5); d.line([(x + 2, yt), (x + 150, yt)], fill=INK, width=4); d.text((x, yt + 14), "arte", font=fnt(38), fill=INK)
base.save(B / "capa-trial-C-dedo.jpg", quality=93)
pv = base.resize((405, 720), Image.LANCZOS); ImageDraw.Draw(pv).rectangle((0, 90, 404, 630), outline=(255, 0, 0), width=1); pv.save(B / "capa-trial-C-dedo_previa.jpg", quality=80)
im0 = limpa                                            # A e B também sem o anel
capa("capa-trial-A-embaixo", 1300, 104, 1230, 1720)   # título sobre o casaco
capa("capa-trial-B-emcima", 300, 104, 230, 720)       # título sobre a parede
im0.resize((405, 720), Image.LANCZOS).save(B / "foto_previa.jpg", quality=80)
print("rclone", rc("copy", str(B), "gdrive:_analises/trial-1311/capa", "--exclude", "src/**"), flush=True)
print("FIM-CAPA", flush=True)
