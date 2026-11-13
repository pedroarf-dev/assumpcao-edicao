"""Inserto de obra em "cartão 3D": fundo da própria obra desfocado + quadro inclinado em perspectiva com sombra,
zoom lento e (opcional) contador em Fraunces #FFCC00. Gera mp4 1080x1920 30 fps sem áudio."""
import math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
AMARELO = (255, 204, 0)

def _fonte(caminho, tam, peso="Bold"):
    f = ImageFont.truetype(caminho, tam)
    try: f.set_variation_by_name(peso)
    except Exception: pass
    return f

def _ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def _fundo(img):
    h, w = img.shape[:2]; s = max(W / w, H / h) * 1.15
    b = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    y0, x0 = (b.shape[0] - H) // 2, (b.shape[1] - W) // 2
    b = b[y0:y0 + H, x0:x0 + W]
    b = cv2.GaussianBlur(b, (0, 0), 38)
    return (b * 0.38).astype(np.uint8)

def _cantos(cw, ch, cx, cy, yaw, pitch, esc, f=2200):
    pts = []
    for (x, y) in [(-cw/2, -ch/2), (cw/2, -ch/2), (cw/2, ch/2), (-cw/2, ch/2)]:
        x, y = x * esc, y * esc
        x1, z1 = x * math.cos(yaw), x * math.sin(yaw)
        y2, z2 = y * math.cos(pitch) - z1 * math.sin(pitch), y * math.sin(pitch) + z1 * math.cos(pitch)
        k = f / (f + z2); pts.append([cx + x1 * k, cy + y2 * k])
    return np.float32(pts)

def gerar(saida, imagens, durs, fonte, contador=None, rotulo=None, yaw0=-9, yaw1=7, cy=1020, maxw=880, maxh=1050):
    """imagens: lista de caminhos; durs: duração de cada uma (s). contador: dict(t19, t17, tfim) em s relativos."""
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", saida], stdin=subprocess.PIPE)
    f_num, f_lab = _fonte(fonte, 150, "Bold"), _fonte(fonte, 46, "SemiBold")
    total, t_glob = sum(durs), 0.0
    for idx, (ip, d) in enumerate(zip(imagens, durs)):
        img = cv2.cvtColor(cv2.imread(ip), cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]; s = min(maxw / w, maxh / h); cw, ch = int(w * s), int(h * s)
        card = cv2.resize(img, (cw, ch), interpolation=cv2.INTER_AREA)
        borda = 14; card = cv2.copyMakeBorder(card, borda, borda, borda, borda, cv2.BORDER_CONSTANT, value=(245, 242, 236))
        cw, ch = card.shape[1], card.shape[0]
        fundo = _fundo(img)
        sentido = 1 if idx % 2 == 0 else -1
        n = max(1, int(round(d * FPS)))
        for k in range(n):
            u = k / max(1, n - 1); tt = t_glob + k / FPS
            yaw = math.radians((yaw0 + (yaw1 - yaw0) * _ease(u)) * sentido); pitch = math.radians(4 - 3 * u)
            esc = 0.94 + 0.08 * _ease(u)
            fr = fundo.copy()
            src = np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]])
            dst = _cantos(cw, ch, W / 2, cy, yaw, pitch, esc)
            # sombra
            somb = np.zeros((H, W), np.float32)
            cv2.fillConvexPoly(somb, (dst + np.float32([26, 38])).astype(np.int32), 1.0)
            somb = cv2.GaussianBlur(somb, (0, 0), 28)[..., None] * 0.65
            fr = (fr * (1 - somb)).astype(np.uint8)
            M = cv2.getPerspectiveTransform(src, dst)
            war = cv2.warpPerspective(card, M, (W, H), flags=cv2.INTER_LINEAR)
            mask = cv2.warpPerspective(np.ones((ch, cw), np.float32), M, (W, H))[..., None]
            fr = (fr * (1 - mask) + war * mask).astype(np.uint8)
            if contador or rotulo:
                im = Image.fromarray(fr); dr = ImageDraw.Draw(im)
                # faixa escura no alto para leitura
                grad = np.linspace(0.75, 0, 520)[:, None, None]
                arr = np.array(im).astype(np.float32); arr[:520] *= (1 - grad); im = Image.fromarray(arr.astype(np.uint8)); dr = ImageDraw.Draw(im)
                if rotulo:
                    dr.text((W / 2, 150), rotulo, font=f_lab, fill=(255, 255, 255), anchor="mm")
                if contador:
                    c = contador
                    if tt >= c["t19"]:
                        if tt < c["t17"]: v, ano = 19e3, "1984"
                        else:
                            x = _ease((tt - c["t17"]) / max(0.3, c["tfim"] - c["t17"]))
                            v, ano = 19e3 * (110.5e6 / 19e3) ** x, "2017"
                        txt = (f"US$ {v/1e6:,.1f} mi" if v >= 1e6 else f"US$ {v/1e3:,.0f} mil").replace(",", "X").replace(".", ",").replace("X", ".")
                        pop = 1.0
                        a_in = min(1, (tt - c["t19"]) / 0.25)
                        fn = f_num
                        while dr.textlength(txt, font=fn) > 960 and fn.size > 60: fn = _fonte(fonte, fn.size - 8, "Bold")
                        f_num = fn if fn.size < f_num.size else f_num
                        dr.text((W / 2 + 4, 300 + 5), txt, font=f_num, fill=(0, 0, 0), anchor="mm")
                        dr.text((W / 2, 300), txt, font=f_num, fill=AMARELO if a_in >= 1 else tuple(int(255 * a_in) if i < 2 else 0 for i in range(3)), anchor="mm")
                        dr.text((W / 2, 430), ano, font=f_lab, fill=(255, 255, 255), anchor="mm")
                fr = np.array(im)
            p.stdin.write(fr.tobytes())
        t_glob += d
    p.stdin.close(); p.wait()
    return saida
