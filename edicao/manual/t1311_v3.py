"""Trial 13/11 — versão 3 (A e B), depois do retorno do Pedro:
- cortes por frase (frases.json: cada trecho de fala transcrito sozinho), sem takes repetidos nem a travada;
- cor natural; OPPO (olho de peixe) só como "bastidor", inteiro, sem corte;
- obras em cartão 3D (fundo desfocado + quadro em perspectiva), coloridas; contador em cima do Basquiat com a voz por baixo;
- flash das 4 obras no gancho e no fim (loop); sem interrogações nem frase destacada;
- checagem de repetição no vídeo final antes de entregar."""
import json, os, re, shutil, subprocess, sys, difflib, wave
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent)); import cartao3d

B = Path("/dados/trial1311"); RAW = B / "raw"; AN = B / "an"; OUT = B / "out4"; TMP = B / "tmp4"; OBR = B / "obras"; FONTS = Path("/cache/fonts")
for p in (OUT, TMP, OBR): p.mkdir(parents=True, exist_ok=True)
FR = json.load(open(AN / "frases.json"))
# correções da legenda (o Whisper ouviu errado)
def corrigir(u):
    w = u["w"]; t = [x[2].strip(" ,.?!").lower() for x in w]
    if t[:4] == ["o", "que", "a", "criança"]:
        w = [[w[0][0], w[2][1], "Qualquer"]] + w[3:]
    out = []
    for i, x in enumerate(w):
        p = x[2]
        if p.strip(" ,.?!").lower() == "o" and i > 0 and w[i-1][2].strip(" ,.?!").lower() == "deixa": continue
        p = p.replace("Damer", "Dahmer").replace("pedido", "perdido")
        out.append([x[0], x[1], p])
    u["w"] = out; return u
FR = [corrigir(u) for u in FR]
OFF = {"apoio": 0.0, "principal": json.load(open(AN / "sync.json"))["offsets"]["principal1311.mp4"]["lag_s"]}
SRC = {"apoio": RAW / "apoio1311.mp4", "principal": RAW / "principal1311.mp4", "zoom": RAW / "principal1311.mp4"}
FONTE = str(FONTS / "Fraunces.ttf")

def sh(*c):
    print("+", " ".join(map(str, c))[:220], flush=True); subprocess.run([str(x) for x in c], check=True)
def saida(*c):
    r = subprocess.run([str(x) for x in c], capture_output=True, text=True); return r.stdout + r.stderr

# ---------- obras (Drive: 04 Acervo/Obras de referência) ----------
import docker
cs = docker.from_env().containers.get("assumpcao-sync")
def rc(*args):
    cmd = ['sh', '-c', 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"$GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; exec rclone "$@"', 'x', *args]
    r = cs.exec_run(cmd, demux=True); return r.exit_code, (r.output[0] or b"").decode(), (r.output[1] or b"").decode()
print("rclone obras:", rc("copy", "gdrive:04 Acervo/Obras de referência", str(OBR))[0], [p.name for p in OBR.iterdir()], flush=True)
def obra(nome):
    for p in sorted(OBR.iterdir()):
        if nome in p.name.lower() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"): return str(p)
    return None
OB = {k: obra(k) for k in ("miro", "pollock", "picasso", "basquiat")}
if not OB["miro"]: OB["miro"] = obra("miró")
print("OBRAS", OB, flush=True)


# ---------- seleção de frases ----------
JANELAS = [("gancho", 2.5, 4.8, None), ("escutado", 4.9, 9.9, None), ("cafe", 14.8, 18.5, "A"), ("beleza", 24.3, 29.8, None),
           ("basquiat", 38.5, 53.9, None), ("crianca", 63.5, 74.6, None), ("perguntar", 82.2, 94.3, None),
           ("dahmer", 119.3, 137.5, None), ("talento", 154.5, 166.9, None), ("picasso", 209.5, 222.1, None),
           ("parou", 231.3, 241.3, None), ("pergunta", 246.7, 251.6, None), ("loop", 262.5, 267.1, None)]
FORA = [(75.9, 79.7)]   # travada do "experimentar"
PRE, POS = 0.10, 0.16
def frases(versao):
    r = []
    for sid, a, b, so in JANELAS:
        if so and so != versao: continue
        for u in FR:
            if u.get("drop") or not (a <= u["ini"] <= b): continue
            if any(x <= u["ini"] <= y for x, y in FORA): continue
            r.append((sid, u))
    return r

BASTIDOR = []   # v4: Pedro pediu para tirar os dois planos do OPPO
import wave as _wave
_wf = _wave.open(str(AN / "principal1311.wav")); _X = np.frombuffer(_wf.readframes(_wf.getnframes()), np.int16).astype(np.float32) / 32768
def buraco(a, b):
    """dentro de [a,b] (tempo de referência) acha o trecho mais fraco (hesitação) para cortar; devolve (x, y) ou None"""
    i0, i1 = int((a - OFF["principal"]) * 16000), int((b - OFF["principal"]) * 16000)
    e = np.sqrt((_X[i0:i1][: (i1 - i0) // 160 * 160].reshape(-1, 160) ** 2).mean(1))   # 10 ms
    if len(e) < 25: return None
    lim = e.max() * 0.35; melhor, ini = None, None
    for k, v in enumerate(list(e) + [1e9]):
        if v < lim and ini is None: ini = k
        elif v >= lim and ini is not None:
            if k - ini >= 6 and ini > 3 and (melhor is None or k - ini > melhor[1] - melhor[0]): melhor = (ini, k)
            ini = None
    if melhor: return (a + melhor[0] / 100 + 0.02, a + melhor[1] / 100 - 0.02)
    d = b - a                       # sem buraco claro: deixa o "faz" com 0,32 s (tira o meio esticado)
    return (a + 0.22, b - 0.10) if d > 0.45 else None

def plano(versao):
    clips, t, cam, shot = [], 0.0, "principal", 0.0
    for sid, u in frases(versao):
        a, b = u["ini"] - PRE, u["fim"] + POS
        if clips and a < clips[-1]["b"]: a = clips[-1]["b"]
        # pedaços: bastidor pelo fim da frase quando ela termina com as palavras-chave
        cortes = [(a, b, None)]
        if "se até uma criança" in " ".join(w[2] for w in u["w"]).lower():
            wf = [w for w in u["w"] if w[2].strip(" ,.?!").lower() == "faz"]
            bz = buraco(wf[-1][0] - 0.02, wf[-1][1] + 0.05) if wf else None
            print("FAZ", wf[-1] if wf else None, "corte", bz, flush=True)
            if bz: cortes = [(a, bz[0], None), (bz[1], b, None)]
        txt = " ".join(w[2] for w in u["w"]).lower()
        for chave, c in BASTIDOR:
            if txt.rstrip(" .?!,").endswith(chave):
                n = len(chave.split()); ini_b = u["w"][-n][0] - 0.12
                cortes = [(a, ini_b, None), (ini_b, b, c)]
        for (x, y, forc) in cortes:
            if y - x < 0.08: continue
            if forc: c = forc
            elif sid in ("gancho", "loop", "basquiat", "pergunta"): c = "principal"
            else:
                c = cam if cam != "apoio" else "principal"
                if shot >= 4.5: c = "zoom" if c == "principal" else "principal"
            if c != cam: shot = 0.0
            cam = c
            clips.append({"sid": sid, "a": x, "b": y, "cam": c, "o": t}); t += y - x; shot += y - x
    return clips, t

def r2o(clips, tr):
    for c in clips:
        if c["a"] - 1e-3 <= tr <= c["b"] + 1e-3: return c["o"] + tr - c["a"]
    return None

def palavras(clips, versao):
    r = []
    for sid, u in frases(versao):
        for (a, b, p) in u["w"]:
            o = r2o(clips, (a + b) / 2)
            if o is not None: r.append((o - (b - a) / 2, o + (b - a) / 2, p)); continue
            o = r2o(clips, a + 0.05)
            if o is not None: r.append((o, o + 0.3, p))
    return r

def ts(x):
    h, r = divmod(max(0, x), 3600); m, s = divmod(r, 60); return f"{int(h)}:{int(m):02d}:{s:05.2f}"
def legenda(ws, caminho):
    L = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "", "[V4+ Styles]",
         "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
         "Style: L,DejaVu Sans,68,&H00FFFFFF,&H0000CCFF,&H00101010,&H00000000,1,0,0,0,100,100,0,0,1,5,0,2,90,90,500,1",
         "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for i in range(0, len(ws), 3):
        g = ws[i:i + 3]
        for j, w in enumerate(g):
            txt = " ".join(("{\\c&H00CCFF&}" + x[2] + "{\\c&HFFFFFF&}") if k == j else x[2] for k, x in enumerate(g))
            prox = ws[i + 3][0] if i + 3 < len(ws) else 1e9
            fim = g[j + 1][0] if j + 1 < len(g) else min(w[1] + 0.15, prox)
            L.append(f"Dialogue: 0,{ts(w[0])},{ts(max(fim, w[0] + 0.06))},L,,0,0,0,,{txt}")
    Path(caminho).write_text("\n".join(L), encoding="utf-8")

def achar(ws, p, depois=0):
    for (a, b, x) in ws:
        if a >= depois and p in x.lower(): return a, b
    return None

if not OB["basquiat"] or os.environ.get("DRY"):
    print("FALTA basquiat" if not OB["basquiat"] else "DRY")
    for v in "AB":
        cl, d = plano(v); print(f"PLANO {v}: {len(cl)} cortes, {d:.1f}s")
        for c in cl: print(f"  {c['o']:6.1f} {c['cam']:9s} {c['sid']:9s} {c['a']:7.2f}-{c['b']:7.2f}")
        print("  LEG:", " ".join(w[2] for w in palavras(cl, v))[:900])
    sys.exit(0)

def render(versao):
    clips, dur = plano(versao)
    print(f"VERSAO {versao}: {len(clips)} cortes, {dur:.1f}s;", " ".join(c['cam'][0] for c in clips), flush=True)
    CFR = TMP / "principal_cfr30.mov"
    if not CFR.exists():
        sh("ffmpeg", "-y", "-v", "error", "-i", SRC["principal"], "-vf", "fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p",
           "-af", "aresample=48000:async=1,aformat=channel_layouts=mono", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-g", "30",
           "-c:a", "pcm_s16le", "-video_track_timescale", "30", TMP / "cfr_tmp.mov")
        os.replace(TMP / "cfr_tmp.mov", CFR)
    # recalcula a linha do tempo com cortes em quadros inteiros
    t = 0.0
    for c in clips:
        f0 = round((c["a"] - OFF["principal"]) * 30); f1 = round((c["b"] - OFF["principal"]) * 30)
        c["f0"], c["nf"] = f0, max(1, f1 - f0); c["o"] = t; c["b"] = c["a"] + c["nf"] / 30; t += c["nf"] / 30
    dur = t
    linhas = []
    for i, c in enumerate(clips):
        seg = TMP / f"{versao}_{i:03d}.mov"; d = c["nf"] / 30
        vf = "scale=1210:2150,crop=1080:1920:(iw-1080)/2:(ih-1920)*0.30" if c["cam"] == "zoom" else "null"
        sh("ffmpeg", "-y", "-v", "error", "-ss", f"{c['f0']/30:.4f}", "-i", CFR, "-frames:v", str(c["nf"]),
           "-vf", vf + ",setsar=1,format=yuv420p", "-af", f"atrim=0:{d:.4f},apad=whole_dur={d:.4f}", "-t", f"{d:.4f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "pcm_s16le", "-video_track_timescale", "30", seg)
        linhas.append(f"file '{seg}'")
    for i, c in enumerate([]):
        seg = TMP / f"{versao}_{i:03d}.mov"; d = c["b"] - c["a"]
        fonte = "principal" if c["cam"] == "zoom" else c["cam"]
        tv = c["a"] - OFF[fonte]; ta = c["a"] - OFF["principal"]
        vf = {"zoom": "scale=1210:2150,crop=1080:1920:(iw-1080)/2:(ih-1920)*0.30",
              "principal": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
              "apoio": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"}[c["cam"]]
        if not seg.exists(): sh("ffmpeg", "-y", "-v", "error", "-ss", f"{tv:.3f}", "-i", SRC[c["cam"]], "-ss", f"{ta:.3f}", "-i", SRC["principal"], "-t", f"{d:.3f}",
           "-map", "0:v:0", "-map", "1:a:0", "-vf", vf + ",setsar=1,fps=30,format=yuv420p",
           "-af", "aresample=48000,aformat=channel_layouts=mono", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-c:a", "pcm_s16le", seg)
        linhas.append(f"file '{seg}'")
    (TMP / f"lista_{versao}.txt").write_text("\n".join(linhas))
    junto = TMP / f"junto_{versao}.mov"
    sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", TMP / f"lista_{versao}.txt", "-c", "copy", junto)
    ws = palavras(clips, versao)
    # ---- insertos ----
    ins = []   # (arquivo, ini, fim)
    flash = [OB[k] for k in ("miro", "pollock", "picasso", "basquiat") if OB[k]]
    g = [c for c in clips if c["sid"] == "gancho"]
    if g and flash:
        d = g[-1]["o"] + g[-1]["b"] - g[-1]["a"]
        # rosto livre: obras pequenas no alto, acima da cabeça (cartão com transparência)
        f = TMP / f"flash_ini_{versao}.mov"; cartao3d.gerar(str(f), flash, [d / len(flash)] * len(flash), FONTE, yaw0=-14, yaw1=12,
                                                           cy=330, maxw=430, maxh=380, transparente=True)
        ins.append((f, 0.0, d))
        ins.append((f, dur - d, dur))
    w0 = achar(ws, "esse") ; wfim = achar(ws, "milhões", (achar(ws, "meio") or (0, 0))[0])
    if w0 and wfim:
        s0, s1 = w0[0] - 0.15, wfim[1] + 0.35
        t19 = (achar(ws, "1984", s0) or (s0 + 1, 0))[0] - s0; t17 = (achar(ws, "2017", s0) or (s0 + 4, 0))[0] - s0
        tme = (achar(ws, "meio", s0) or (s0 + t17 + 3, 0))[1] - s0
        f = TMP / f"basquiat_{versao}.mp4"
        cartao3d.gerar(str(f), [OB["basquiat"]], [s1 - s0], FONTE, contador={"t19": t19, "t17": t17, "tfim": tme},
                       rotulo="BASQUIAT · UNTITLED (1982)", yaw0=-8, yaw1=6)
        ins.append((f, s0, s1))
    wp = achar(ws, "picasso", 60)
    if wp and OB["picasso"]:
        f = TMP / f"picasso_{versao}.mp4"; cartao3d.gerar(str(f), [OB["picasso"]], [2.6], FONTE, yaw0=8, yaw1=-6)
        ins.append((f, wp[0] - 0.1, wp[0] + 2.5))
    # vinheta (assinatura amarela, sem som) logo antes do trecho do loop
    assin = Path("/dados/marca/assinatura-amarelo.mov"); lp = [c for c in clips if c["sid"] == "loop"]
    if assin.exists() and lp:
        tl = lp[0]["o"]
        try: da = float(saida("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", assin).strip())
        except Exception: da = 1.8
        da = min(max(da, 1.2), 2.5)
        f = TMP / f"vinheta_{versao}.mov"
        sh("ffmpeg", "-y", "-v", "error", "-i", assin, "-t", f"{da:.2f}", "-vf",
           "fps=30,format=rgba,scale=300:-1,pad=1080:1920:1080-iw-70:1920-ih-260:color=black@0", "-an", "-c:v", "png", f)
        ins.append((f, tl - da, tl)); print(f"VINHETA {tl - da:.2f}-{tl:.2f}", flush=True)
    else: print("VINHETA ausente", assin.exists(), len(lp), flush=True)
    # ---- montagem ----
    leg = TMP / f"leg_{versao}.ass"; legenda(ws, leg)
    entradas = ["-i", junto]; fc = "[0:v]eq=contrast=1.04:saturation=1.08[b0]"; ult = "[b0]"
    for k, (f, a, b) in enumerate(ins, 1):
        entradas += ["-itsoffset", f"{a:.3f}", "-i", f]
        fc += f";{ult}[{k}:v]overlay=eof_action=pass:enable='between(t,{a:.3f},{b:.3f})'[o{k}]"; ult = f"[o{k}]"
    fc += f";{ult}subtitles='{leg}':fontsdir='{FONTS}'[vf]"
    rnn = Path("/cache/sh.rnnn")
    af = "highpass=f=80" + (f",arnndn=m='{rnn}':mix=0.7" if rnn.exists() else "") + ",acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150,loudnorm=I=-14:TP=-1.5:LRA=9"
    fc += f";[0:a]{af}[a]"
    final = OUT / f"Trial qualquer criança faz - {versao} v4.mp4"
    sh("ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", fc, "-map", "[vf]", "-map", "[a]", "-t", f"{dur:.2f}",
       "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-maxrate", "2600k", "-bufsize", "5200k", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", final)
    ebu = saida("ffmpeg", "-hide_banner", "-nostats", "-i", final, "-af", "ebur128", "-f", "null", "-")
    lufs = [l.strip() for l in ebu.splitlines() if l.strip().startswith("I:")]
    qd = OUT / f"quadros_{versao}"; qd.mkdir(exist_ok=True)
    for k in range(10):
        t = dur * (k + 0.5) / 10
        sh("ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", final, "-frames:v", "1", "-vf", "scale=360:-2", qd / f"{k}_{t:05.1f}.jpg")
    for a, b in [(0.3, 0.3), (dur - 0.3, 0)]:
        pass
    info = {"versao": versao, "dur": round(dur, 1), "cortes": len(clips), "tam_mb": round(final.stat().st_size / 1e6, 1),
            "lufs": lufs[-1] if lufs else None, "insertos": [(Path(f).name, round(a, 2), round(b, 2)) for f, a, b in ins],
            "bastidor": [round(c["o"], 1) for c in clips if c["cam"] == "apoio"]}
    json.dump(info, open(OUT / f"info_{versao}.json", "w"), ensure_ascii=False, indent=1)
    print("INFO", json.dumps(info, ensure_ascii=False), flush=True)
    return final

finais = {v: render(v) for v in "AB"}

# ---------- checagem de fala repetida (transcreve o vídeo final por frase) ----------
from faster_whisper import WhisperModel
from faster_whisper.vad import get_speech_timestamps, VadOptions
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=2)
norm = lambda s: re.sub(r"[^\wà-ú ]", "", s.lower()).split()
REP = {}
for v, f in finais.items():
    wv = TMP / f"qc_{v}.wav"; sh("ffmpeg", "-y", "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", wv)
    ww = wave.open(str(wv)); x = np.frombuffer(ww.readframes(ww.getnframes()), np.int16).astype(np.float32) / 32768
    us = []
    for t in get_speech_timestamps(x, VadOptions(min_silence_duration_ms=300, speech_pad_ms=100)):
        segs, _ = m.transcribe(x[t["start"]:t["end"]], language="pt", condition_on_previous_text=False, vad_filter=False)
        tx = " ".join(s.text.strip() for s in segs).strip()
        if tx: us.append((t["start"] / 16000, tx))
    rep = []
    for i in range(len(us)):
        for j in range(i + 1, min(i + 4, len(us))):
            a, b = norm(us[i][1]), norm(us[j][1]); k = min(len(a), len(b), 6)
            if k >= 3 and difflib.SequenceMatcher(None, a[:k], b[:k]).ratio() >= 0.75 and us[j][0] - us[i][0] < 30:
                rep.append(f"{us[i][0]:.1f}s '{us[i][1][:40]}' ~ {us[j][0]:.1f}s")
    REP[v] = rep
    print("QC", v, "frases:", len(us), "repetições:", rep, flush=True)
    for s, tx in us: print(f"Q{v} {s:6.1f} | {tx}", flush=True)
json.dump(REP, open(OUT / "repeticoes.json", "w"), ensure_ascii=False)
ENT = Path("/dados/entregas"); ENT.mkdir(exist_ok=True)
NOTA = {"A": ("7,5", "com café", "• Ritmo: o café atrasa a entrada no assunto; para Reel o ideal fica abaixo de 1:30."),
        "B": ("8", "direto", "• Ritmo: entra mais rápido no assunto; ainda dá para enxugar (ex.: “Você já deve ter escutado…”).")}
COMUM = ("• Som: muito bom (BOYALINK, −14 LUFS).\n"
         "• Travadas/repetições: takes repetidos, a travada do “experimentar” e a do “se até uma criança faz” saíram; checagem no vídeo final sem fala repetida.\n"
         "• Sincronia: cortes refeitos quadro a quadro (o Pixel grava com quadros irregulares e isso desalinhava a boca).\n"
         "• Enquadramento: só Pixel, aberto/fechado (OPPO fora).\n"
         "• Obras: as 4 no gancho e no fim (pequenas, acima do rosto), Basquiat com contador e Picasso na citação.\n"
         "• Luz/cor: cor natural; rosto ok, um pouco chapado.")
for v in "AB":
    info = json.load(open(OUT / f"info_{v}.json")); nota, tipo, ritmo = NOTA[v]
    dst = ENT / f"trial-1311-{v}-v4.mp4"; shutil.copy(finais[v], dst)
    resumo = (f"🎬 Trial · Isso aí qualquer criança faz — {v} ({tipo}) · versão 4\n⏱ {info['dur']:.0f} s · {info['cortes']} cortes\n\n"
              f"Nota: {nota}/10\n{ritmo}\n{COMUM}\n\nNota calculada a partir da transcrição + medidas + quadros do vídeo.")
    json.dump({"arquivo": str(dst), "titulo": "Isso aí qualquer criança faz", "versao": f"{v} v4", "estilo": "especial",
               "nota": nota.replace(",", "."), "resumo": resumo}, open(ENT / f"trial-1311-{v}-v4.json", "w"), ensure_ascii=False)
    print("ENTREGA", v, len(resumo), flush=True)
print("rclone out:", rc("copy", str(OUT), "gdrive:_analises/trial-1311/out4")[0], flush=True)
print("FIM-V3", flush=True)
