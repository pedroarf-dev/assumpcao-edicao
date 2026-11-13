"""Trial 13/11 "Isso aí qualquer criança faz" — edição manual (versões A e B).
Linha do tempo de referência = áudio do OPPO (apoio). Pixel (principal): t_ref = t + 1.16 (palma).
"""
import json, os, subprocess, math, wave, shutil, urllib.request
from pathlib import Path
import numpy as np

B = Path("/dados/trial1311"); RAW = B / "raw"; AN = B / "an"; OUT = B / "out"; TMP = B / "tmp"; FONTS = Path("/cache/fonts")
for p in (OUT, TMP, FONTS): p.mkdir(parents=True, exist_ok=True)
SYNC = json.load(open(AN / "sync.json")); TR = json.load(open(AN / "transcricao.json"))
OFF = {"apoio": 0.0, "principal": SYNC["offsets"]["principal1311.mp4"]["lag_s"]}   # t_ref = t_arquivo + OFF
SRC = {"apoio": RAW / "apoio1311.mp4", "principal": RAW / "principal1311.mp4"}
MARCA = Path("/dados/marca")

def sh(*c):
    print("+", " ".join(map(str, c))[:300], flush=True)
    subprocess.run([str(x) for x in c], check=True)
def out(*c): return subprocess.run([str(x) for x in c], capture_output=True, text=True).stdout + subprocess.run([str(x) for x in c], capture_output=True, text=True).stderr

# ---------- fonte Fraunces (OFL) ----------
fr = FONTS / "Fraunces.ttf"
if not fr.exists():
    try:
        urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf", fr)
    except Exception as e: print("aviso: sem Fraunces", e)
for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
    if Path(f).exists() and not (FONTS / Path(f).name).exists(): shutil.copy(f, FONTS)

# ---------- melhor áudio (fala x fundo) ----------
def snr(w):
    f = wave.open(str(w)); x = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
    n = len(x) // 800; e = 20 * np.log10(np.sqrt((x[:n*800].reshape(n, 800) ** 2).mean(1)) + 1e-9)
    return float(np.percentile(e, 90) - np.percentile(e, 10)), float(np.percentile(e, 90))
med = {k: snr(AN / f"{k}1311.wav") for k in SRC}
AUD = max(med, key=lambda k: med[k][0])
print("AUDIO", med, "->", AUD, flush=True)

# ---------- palavras ----------
W = [(w[0], w[1], w[2]) for s in TR for w in s["w"]]

# ---------- roteiro de cortes (tempos da referência) ----------
SEG = [  # (id, ini, fim, só_em)
    ("gancho", 2.55, 4.70, None),
    ("escutado", 4.80, 9.80, None),
    ("cafe", 14.70, 18.50, "A"),
    ("beleza", 24.20, 29.80, None),
    ("basquiat", 38.10, 53.85, None),
    ("crianca", 63.25, 74.75, None),          # corta a travada 76–79,6
    ("perguntar", 82.00, 94.30, None),
    ("dahmer", 118.70, 137.50, None),         # último take
    ("talento", 154.80, 166.90, None),        # último take
    ("picasso", 203.70, 222.10, None),        # último take
    ("parou", 231.20, 241.30, None),
    ("pergunta", 246.55, 251.60, None),
    ("loop1", 262.05, 263.30, None),
    ("loop2", 264.35, 267.10, None),
]
FIXO_PRINCIPAL = {"gancho", "basquiat", "pergunta", "loop1", "loop2"}
GAP, PRE, POS = 0.50, 0.10, 0.20

def grupos(a, b):
    ws = [w for w in W if w[0] >= a - 0.05 and w[1] <= b + 0.05]
    if not ws: return [(a, b)]
    g, cur = [], [ws[0]]
    for w in ws[1:]:
        if w[0] - cur[-1][1] > GAP: g.append(cur); cur = [w]
        else: cur.append(w)
    g.append(cur)
    r = []
    for x in g:
        s, e = max(a, x[0][0] - PRE), min(b, x[-1][1] + POS)
        if r and s < r[-1][1]: s = r[-1][1]
        r.append((s, e))
    return r

def plano(versao):
    clips, t, cam, shot = [], 0.0, "principal", 0.0
    for sid, a, b, so in SEG:
        if so and so != versao: continue
        for (s, e) in grupos(a, b):
            if sid in FIXO_PRINCIPAL: c = "principal"
            else:
                c = cam
                if shot >= 4.5: c = "zoom" if cam == "principal" else "principal"
            if c != cam: shot = 0.0
            cam = c; d = e - s
            clips.append({"sid": sid, "a": s, "b": e, "cam": c, "o": t}); t += d; shot += d
    return clips, t

def ref2out(clips, tr):
    for c in clips:
        if c["a"] - 1e-3 <= tr <= c["b"] + 1e-3: return c["o"] + tr - c["a"]
    return None

# ---------- ASS ----------
def ts(x):
    h, r = divmod(max(0, x), 3600); m, s = divmod(r, 60); return f"{int(h)}:{int(m):02d}:{s:05.2f}"
CAB = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: L,DejaVu Sans,70,&H00FFFFFF,&H0000CCFF,&H00101010,&H00000000,1,0,0,0,100,100,0,0,1,5,0,2,90,90,520,1",
       "Style: N,Fraunces,150,&H0000CCFF,&H0000CCFF,&H00101010,&H64000000,1,0,0,0,100,100,0,0,1,6,2,5,60,60,0,1",
       "Style: R,DejaVu Sans,44,&H00FFFFFF,&H00FFFFFF,&H00101010,&H64000000,1,0,0,0,100,100,2,0,1,4,0,5,60,60,0,1",
       "Style: D,Fraunces,96,&H0000CCFF,&H0000CCFF,&H00101010,&H64000000,1,0,0,0,100,100,0,0,1,5,2,5,80,80,0,1",
       "Style: Q,Fraunces,220,&H0000CCFF,&H0000CCFF,&H00101010,&H00000000,1,0,0,0,100,100,0,0,1,6,0,5,0,0,0,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]

def wout(clips):
    r = []
    for (a, b, p) in W:
        o = ref2out(clips, (a + b) / 2)
        if o is None: continue
        r.append((o - (b - a) / 2, o + (b - a) / 2, p))
    return r

def ass(clips, dur, caminho):
    L = list(CAB); ws = wout(clips)
    # legenda palavra a palavra, 3 por tela, palavra falada em amarelo
    for i in range(0, len(ws), 3):
        g = ws[i:i + 3]
        for j, w in enumerate(g):
            txt = " ".join(("{\\c&H00CCFF&}" + x[2] + "{\\c&HFFFFFF&}") if k == j else x[2] for k, x in enumerate(g))
            fim = g[j + 1][0] if j + 1 < len(g) else w[1] + 0.15
            L.append(f"Dialogue: 0,{ts(w[0])},{ts(max(fim, w[0] + 0.06))},L,,0,0,0,,{txt}")
    def achar(p, depois=0):
        for (a, b, x) in ws:
            if a >= depois and p.lower() in x.lower(): return a, b
        return None
    # contador Basquiat
    seg = [c for c in clips if c["sid"] == "basquiat"]
    if seg:
        s0, s1 = seg[0]["o"], seg[-1]["o"] + seg[-1]["b"] - seg[-1]["a"]
        L.append(f"Dialogue: 1,{ts(s0)},{ts(s1)},R,,0,0,0,,{{\\pos(540,170)\\fad(200,200)}}BASQUIAT · UNTITLED (1982)")
        w19 = achar("19", s0) or (s0 + 3, s0 + 3.3); w17 = achar("2017", s0) or (s0 + 7, s0 + 7.3); wme = achar("meio", w17[0]) or (w17[0] + 3, w17[0] + 3.3)
        L.append(f"Dialogue: 1,{ts(w19[0])},{ts(w17[0])},R,,0,0,0,,{{\\pos(540,470)}}1984")
        L.append(f"Dialogue: 2,{ts(w19[0])},{ts(w17[0])},N,,0,0,0,,{{\\pos(540,330)\\fscx40\\fscy40\\t(0,180,\\fscx100\\fscy100)}}US$ 19 mil")
        L.append(f"Dialogue: 1,{ts(w17[0])},{ts(s1)},R,,0,0,0,,{{\\pos(540,470)}}2017")
        n = 40; t0, t1 = w17[0], max(wme[1], w17[0] + 1.5)
        for k in range(n):
            f = (k + 1) / n; v = 19e3 * (110.5e6 / 19e3) ** (f ** 0.8)
            txt = f"US$ {v/1e6:.1f} mi".replace(".", ",") if v >= 1e6 else f"US$ {v/1e3:.0f} mil"
            a = t0 + (t1 - t0) * k / n; b = t0 + (t1 - t0) * (k + 1) / n if k < n - 1 else s1
            if k == n - 1: txt = "US$ 110,5 mi"
            L.append(f"Dialogue: 2,{ts(a)},{ts(b)},N,,0,0,0,,{{\\pos(540,330)}}{txt}")
    # frase destaque: "…um dia fez isso e parou."
    w = achar("parou")
    if w: L.append(f"Dialogue: 2,{ts(w[0] - 1.6)},{ts(w[1] + 1.2)},D,,0,0,0,,{{\\pos(540,340)\\fad(150,250)}}um dia fez…{{\\N}}e parou.")
    # interrogações pulsando na pergunta final
    seg = [c for c in clips if c["sid"] == "pergunta"]
    if seg:
        s0 = seg[0]["o"]; s1 = seg[-1]["o"] + seg[-1]["b"] - seg[-1]["a"]
        for (x, y, atraso) in [(220, 420, 0), (860, 520, 300), (540, 300, 600)]:
            puls = "".join(f"\\t({k*700},{k*700+350},\\fscx125\\fscy125)\\t({k*700+350},{k*700+700},\\fscx100\\fscy100)" for k in range(int((s1 - s0) / 0.7) + 1))
            L.append(f"Dialogue: 2,{ts(s0 + atraso/1000)},{ts(s1)},Q,,0,0,0,,{{\\pos({x},{y})\\fad(150,150){puls}}}?")
    Path(caminho).write_text("\n".join(L), encoding="utf-8")

# ---------- render ----------
def render(versao):
    clips, dur = plano(versao)
    print(f"VERSAO {versao}: {len(clips)} cortes, {dur:.1f}s; câmeras:", " ".join(c['cam'][0] for c in clips), flush=True)
    lst = TMP / f"lista_{versao}.txt"; linhas = []
    for i, c in enumerate(clips):
        seg = TMP / f"v2_{versao}_{i:03d}.mp4"; d = c["b"] - c["a"]
        fonte = "principal" if c["cam"] == "zoom" else c["cam"]
        tv = c["a"] - OFF[fonte]; ta = c["a"] - OFF[AUD]
        vf = ("scale=1210:2150,crop=1080:1920:(iw-1080)/2:(ih-1920)*0.30" if c["cam"] == "zoom"
              else "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920")
        if not seg.exists():
            sh("ffmpeg", "-y", "-v", "error", "-ss", f"{tv:.3f}", "-i", SRC[fonte], "-ss", f"{ta:.3f}", "-i", SRC[AUD], "-t", f"{d:.3f}",
               "-map", "0:v:0", "-map", "1:a:0",
               "-vf", vf + ",setsar=1,fps=30,format=yuv420p",
               "-af", "aresample=48000,aformat=channel_layouts=mono", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
               "-c:a", "pcm_s16le", "-f", "mov", seg)
        linhas.append(f"file '{seg}'")
    lst.write_text("\n".join(linhas))
    junto = TMP / f"junto_{versao}.mov"
    sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", junto)
    a = TMP / f"leg_{versao}.ass"; ass(clips, dur, a)
    final = OUT / f"Trial qualquer criança faz - {versao}.mp4"
    rnn = Path("/cache/sh.rnnn")
    af = "highpass=f=80" + (f",arnndn=m='{rnn}':mix=0.8" if rnn.exists() else ",afftdn=nf=-25") + \
         ",acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150,loudnorm=I=-14:TP=-1.5:LRA=9"
    # whoosh sintético (sem licença) na entrada do contador
    bq = [c for c in clips if c["sid"] == "basquiat"]
    wt = bq[0]["o"] if bq else 0
    entradas = ["-i", junto, "-f", "lavfi", "-t", "0.6", "-i", "anoisesrc=color=pink:amplitude=0.5:r=48000"]
    fc = (f"[0:v]hue=s=0,eq=contrast=1.08:brightness=0.01,subtitles='{a}':fontsdir='{FONTS}'[v0];"
          f"[0:a]{af}[a0];"
          f"[1:a]bandpass=f=900:w=1200,afade=t=in:d=0.25,afade=t=out:st=0.3:d=0.3,volume=0.35,adelay={int(wt*1000)}|{int(wt*1000)}[wh];"
          f"[a0][wh]amix=inputs=2:normalize=0:duration=first[a1]")
    ultimo, mapa_a = "[v0]", "[a1]"
    assin, som = MARCA / "assinatura-amarelo.mov", MARCA / "som-assinatura-padrao.wav"
    if assin.exists():
        ini = max(0.0, dur - 1.8)
        entradas += ["-itsoffset", f"{ini:.2f}", "-i", assin]
        fc += f";[2:v]scale=260:-1[ass];[v0][ass]overlay=x=W-w-70:y=H-h-300:eof_action=pass[v1]"
        ultimo = "[v1]"
    sh("ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", fc, "-map", ultimo, "-map", mapa_a,
       "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-maxrate", "2600k", "-bufsize", "5200k",
       "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", final)
    # medidas + quadros para a nota
    ebu = out("ffmpeg", "-hide_banner", "-nostats", "-i", final, "-af", "ebur128", "-f", "null", "-")
    lufs = [l for l in ebu.splitlines() if l.strip().startswith("I:")]
    qd = OUT / f"quadros_{versao}"; qd.mkdir(exist_ok=True)
    for k in range(8):
        t = dur * (k + 0.5) / 8
        sh("ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", final, "-frames:v", "1", "-vf", "scale=360:-2", qd / f"{k}_{t:05.1f}.jpg")
    info = {"versao": versao, "dur": round(dur, 1), "cortes": len(clips), "tam_mb": round(final.stat().st_size / 1e6, 1),
            "lufs": lufs[-1].strip() if lufs else None, "audio": AUD, "snr": med,
            "trocas_camera": sum(1 for i in range(1, len(clips)) if clips[i]["cam"] != clips[i-1]["cam"]),
            "plano": [(c["sid"], round(c["a"], 2), round(c["b"], 2), c["cam"]) for c in clips]}
    json.dump(info, open(OUT / f"info_{versao}.json", "w"), ensure_ascii=False, indent=1)
    print("INFO", json.dumps({k: v for k, v in info.items() if k != "plano"}, ensure_ascii=False), flush=True)

render("A"); render("B")

# ---------- entrega no Telegram (n8n "Entrega de vídeo" lê /dados/entregas/*.json) ----------
ENT = Path("/dados/entregas"); ENT.mkdir(exist_ok=True)
AVISO = "Nota calculada a partir da transcrição + medidas (som, duração, cortes) + quadros do vídeo."
COMUM = ("• Som: muito bom (BOYALINK no Pixel, fundo bem baixo, −14 LUFS).\n"
         "• Travadas: 3 trechos repetidos → fiquei com o último take; a travada do “experimentar” saiu.\n"
         "• Enquadramento: só o Pixel (aberto/fechado). O OPPO saiu com vinheta redonda e a lâmpada estourada — ficou de fora.\n"
         "• Luz: rosto ok, mas chapado; uma luz lateral daria mais volume no P&B.\n"
         "• Obras: faltam as imagens (Basquiat etc.) — por isso o gancho não tem a obra na tela.")
RES = {"A": ("7", "• Ritmo: ~2 min, longo para Reel; o café atrasa o “por que você não fez?”. Cortar “Você já deve ter escutado…”, a pergunta repetida e encurtar o Pedrinho → ~80 s."),
       "B": ("7,5", "• Ritmo: ~2 min, longo para Reel; entra mais rápido que a A. Cortar “Você já deve ter escutado…”, a pergunta repetida e encurtar o Pedrinho → ~80 s.")}
for v in "AB":
    info = json.load(open(OUT / f"info_{v}.json"))
    dst = ENT / f"trial-1311-{v}.mp4"; shutil.copy(OUT / f"Trial qualquer criança faz - {v}.mp4", dst)
    nota, ritmo = RES[v]
    resumo = (f"🎬 Trial · Isso aí qualquer criança faz — versão {v} ({'com café' if v == 'A' else 'direto'})\n"
              f"⏱ {info['dur']:.0f} s · {info['cortes']} cortes · {info['tam_mb']} MB\n\n"
              f"Nota: {nota}/10\n{ritmo}\n{COMUM}\n\n{AVISO}")
    json.dump({"arquivo": str(dst), "titulo": "Isso aí qualquer criança faz", "versao": v, "estilo": "especial",
               "nota": nota.replace(",", "."), "resumo": resumo}, open(ENT / f"trial-1311-{v}.json", "w"), ensure_ascii=False)
    print("ENTREGA", v, len(resumo), "caracteres", flush=True)

# copia para o Drive (_analises) para conferência
import docker
c = docker.from_env().containers.get("assumpcao-sync")
cmd = ['sh', '-c', 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"$GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; exec rclone "$@"',
       'x', "copy", "/dados/trial1311/out", "gdrive:_analises/trial-1311/out"]
r = c.exec_run(cmd); print("rclone", r.exit_code, flush=True)
cmd[-2:] = ["/dados/trial1311/an/frames", "gdrive:_analises/trial-1311/frames"]; print("rclone2", c.exec_run(cmd).exit_code)
print("FIM-EDICAO", flush=True)
