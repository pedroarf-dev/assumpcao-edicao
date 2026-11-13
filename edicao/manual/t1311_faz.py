"""Teste de remendo do "faz" travado (Trial 13/11): só áudio, boca do vídeo original.
Gera um mp4 curto com 3 versões do mesmo trecho (1 atual · 2 e 3 = remendos com outro "faz" do bruto)."""
import json, re, subprocess, wave
from pathlib import Path
import numpy as np

B = Path("/dados/trial1311"); AN = B / "an"; TMP = B / "tmp4"; W = TMP / "faz"; W.mkdir(parents=True, exist_ok=True)
CFR = TMP / "principal_cfr30.mov"
OFF = json.load(open(AN / "sync.json"))["offsets"]["principal1311.mp4"]["lag_s"]   # t_ref = t_pixel + OFF
FR = json.load(open(AN / "frases.json"))
ALVO = (51.57, 52.09); CORTE = (51.73, 51.98)            # do log da v4
CLIPS = [(47.8333, 48.9667), (49.40, 50.5667), (50.8333, 51.10), (51.4667, 52.7667)]   # trechos da A v4 (tempo do Pixel)

def sh(*c): print("+", " ".join(map(str, c))[:200], flush=True); subprocess.run([str(x) for x in c], check=True)
def ler(p):
    w = wave.open(str(p)); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
def gravar(p, x, sr=48000):
    w = wave.open(str(p), "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

SR = 48000
if not (W / "a48.wav").exists():
    sh("ffmpeg", "-y", "-v", "error", "-i", CFR, "-vn", "-ac", "1", "-ar", SR, "-c:a", "pcm_s16le", W / "a48.wav")
A = ler(W / "a48.wav")
px = lambda t_ref: t_ref - OFF
seg = lambda a, b: A[int(round(a * SR)):int(round(b * SR))]

def f0(x):
    """f0 médio e inclinação (Hz/s) na parte sonora (autocorrelação, quadros de 30 ms)"""
    fr, out = int(0.03 * SR), []
    for i in range(0, len(x) - fr, fr // 2):
        q = x[i:i + fr] - x[i:i + fr].mean()
        if np.sqrt((q ** 2).mean()) < 0.01: continue
        c = np.correlate(q, q, "full")[fr - 1:]; lo, hi = SR // 300, SR // 70
        k = lo + int(np.argmax(c[lo:hi]))
        if c[k] > 0.3 * c[0]: out.append((i / SR, SR / k))
    if len(out) < 2: return None, None
    t, f = np.array(out).T
    return float(np.median(f)), float(np.polyfit(t, f, 1)[0])

alvo_x = seg(px(ALVO[0]), px(CORTE[0]))
fa, sa = f0(alvo_x)
print(f"ALVO f0={fa} incl={sa}", flush=True)

norm = lambda s: re.sub(r"[^\wà-ú]", "", s.lower())
cands = []
for u in FR:
    ws = u["w"]
    for k, (a, b, w) in enumerate(ws):
        if norm(w) != "faz" or abs(a - ALVO[0]) < 0.05: continue
        prox = ws[k + 1] if k + 1 < len(ws) else None
        continua = bool(prox and prox[0] - b < 0.35 and not w.strip().endswith((".", "?", "!")))
        x = seg(px(a), px(b)); f, s = f0(x)
        if f is None: continue
        d = b - a
        nota = abs(f - (fa or f)) / 15 + abs(d - 0.30) * 4 + (0 if continua else 1.0) + (abs(s - (sa or 0)) / 200 if sa is not None else 0)
        ant = ws[k - 1][2] if k else ""
        cands.append({"a": a, "b": b, "dur": round(d, 2), "f0": round(f), "incl": round(s), "continua": continua,
                      "ctx": f"{ant} [faz] {prox[2] if prox else ''}", "nota": round(nota, 2)})
cands.sort(key=lambda c: c["nota"])
for c in cands: print("CAND", json.dumps(c, ensure_ascii=False), flush=True)

# trecho de teste com os mesmos cortes da A v4
base = np.concatenate([seg(a, b) for a, b in CLIPS])
off = 0.0; s0 = s1 = None
for a, b in CLIPS:
    if a <= px(ALVO[0]) < b: s0 = off + (px(ALVO[0]) - a)
    if a <= px(ALVO[1]) <= b + 0.02: s1 = off + (min(px(ALVO[1]), b) - a)
    off += b - a
L = s1 - s0
print(f"FAZ no trecho: {s0:.3f}-{s1:.3f} ({L:.3f} s)", flush=True)

def remendo(c, nome):
    gravar(W / f"{nome}_in.wav", seg(px(c["a"]) - 0.01, px(c["b"]) + 0.01))
    r = (c["b"] - c["a"] + 0.02) / L
    at = []
    while r > 2: at.append("atempo=2"); r /= 2
    while r < 0.5: at.append("atempo=0.5"); r /= 0.5
    at.append(f"atempo={r:.4f}")
    sh("ffmpeg", "-y", "-v", "error", "-i", W / f"{nome}_in.wav", "-af", ",".join(at), "-ar", SR, W / f"{nome}_st.wav")
    p = ler(W / f"{nome}_st.wav")
    n = int(round(L * SR)); p = np.pad(p, (0, max(0, n - len(p))))[:n]
    o = base[int(s0 * SR):int(s0 * SR) + n]
    p *= (np.sqrt((o ** 2).mean()) + 1e-6) / (np.sqrt((p ** 2).mean()) + 1e-6)
    y = base.copy(); i0 = int(s0 * SR); xf = int(0.012 * SR)
    ramp = np.linspace(0, 1, xf)
    m = np.ones(n); m[:xf] = ramp; m[-xf:] = ramp[::-1]
    y[i0:i0 + n] = o * (1 - m) + p * m
    return y

versoes = [("1 · atual", base)]
for i, c in enumerate(cands[:2]):
    versoes.append((f"{i + 2} · remendo ({c['ctx'].strip()})", remendo(c, f"r{i + 2}")))

# vídeo do trecho (mesmos quadros) + rótulo
fc = "".join(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{k}];" for k, (a, b) in enumerate(CLIPS))
fc += "".join(f"[v{k}]" for k in range(len(CLIPS))) + f"concat=n={len(CLIPS)}:v=1:a=0[v]"
sh("ffmpeg", "-y", "-v", "error", "-i", CFR, "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", W / "v.mp4")
partes = []
for k, (rot, y) in enumerate(versoes):
    gravar(W / f"x{k}.wav", np.concatenate([np.zeros(int(0.4 * SR)), y]))
    txt = rot.replace(":", "\\:").replace("'", "")
    sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=black:s=1080x1920:r=30:d=0.4", "-i", W / "v.mp4", "-i", W / f"x{k}.wav",
       "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
       f"text='{txt}':fontcolor=0xFFCC00:fontsize=54:x=(w-tw)/2:y=220:box=1:boxcolor=black@0.6:boxborderw=18[vv];"
       "[2:a]highpass=f=80,loudnorm=I=-14:TP=-1.5[aa]", "-map", "[vv]", "-map", "[aa]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
       "-c:a", "aac", "-b:a", "160k", "-ar", "48000", W / f"p{k}.mp4")
    partes.append(f"file '{W / f'p{k}.mp4'}'")
(W / "lista.txt").write_text("\n".join(partes))
ENT = Path("/dados/entregas")
dst = ENT / "trial-1311-teste-faz.mp4"
sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", W / "lista.txt", "-c", "copy", "-movflags", "+faststart", dst)
linhas = "\n".join(f"{r}" for r, _ in versoes)
resumo = ("🧪 Teste do remendo no “faz” (só o áudio; a boca é a do vídeo original)\n\n" + linhas +
          "\n\nOuça de fone. Me diga no chat Técnico qual fica (1, 2 ou 3). Os botões abaixo não valem para este teste.")
json.dump({"arquivo": str(dst), "titulo": "Teste remendo faz", "versao": "teste faz", "estilo": "especial", "nota": None, "resumo": resumo},
          open(ENT / "trial-1311-teste-faz.json", "w"), ensure_ascii=False)
print("FIM-FAZ", flush=True)
