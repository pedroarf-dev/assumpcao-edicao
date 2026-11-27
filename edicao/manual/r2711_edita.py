"""Reel 27/11 (Eulino Falante) — edição padrão (sem motion): frases escolhidas (SEL), Pixel aberto/fechado,
apoio (OPPO) DESLIGADO desde 27/11, legenda palavra a palavra, cor natural, −14 LUFS, vinheta no fim, QC de repetição, entrega no Telegram."""
import json, os, re, shutil, subprocess, difflib, wave
from pathlib import Path
import numpy as np
B = Path("/dados/r2711"); RAW = B / "raw"; AN = B / "an"; OUT = B / "out"; TMP = B / "tmp"; FONTS = Path("/cache/fonts")
for p in (OUT, TMP): p.mkdir(parents=True, exist_ok=True)
FR = json.load(open(AN / "frases.json"))
CFG = json.loads(os.environ["CFG"])          # {"sel":[[id, cortaIni, cortaFim],...], "apoio":[ids], "fix":{"errado":"certo"}, "versao":"v1", "nota":"7", "resumo":"..."}
OFFA = json.load(open(AN / "sync.json"))["off"]["apoio2711.mp4"]["por_palma"]   # t_principal = t_apoio + OFFA
def sh(*c):
    print("+", " ".join(map(str, c))[:200], flush=True); subprocess.run([str(x) for x in c], check=True)
def saida(*c):
    r = subprocess.run([str(x) for x in c], capture_output=True, text=True); return r.stdout + r.stderr
FIX = CFG.get("fix", {})
def fix(p):
    for a, b in FIX.items(): p = re.sub(r"\b" + re.escape(a) + r"\b", b, p, flags=re.I)
    return p
PRE, POS = 0.08, 0.14
CFR = TMP / "principal_cfr30.mov"
if not CFR.exists():
    sh("ffmpeg", "-y", "-v", "error", "-i", RAW / "principal2711.mp4", "-vf", "fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p",
       "-af", "aresample=48000:async=1,aformat=channel_layouts=mono", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-g", "30",
       "-c:a", "pcm_s16le", "-video_track_timescale", "30", TMP / "cfr_tmp.mov"); os.replace(TMP / "cfr_tmp.mov", CFR)
# ---- plano ----
clips, t, cam, shot = [], 0.0, "principal", 0.0
for k, (fid, ci, cf) in enumerate(CFG["sel"]):
    u = FR[fid]; ws = [w for w in u["w"] if w[0] >= u["ini"] + (ci or 0) - 1e-3 and w[1] <= u["fim"] - (cf or 0) + 1e-3]
    a = ws[0][0] - PRE; b = ws[-1][1] + POS
    if k == len(CFG["sel"]) - 1: b += float(CFG.get("parado", 1.4))      # 1–2 s parado no fim
    if False: c = "apoio"   # 27/11: apoio (OPPO) desligado — o corte de apoio quebrava a emenda; áudio é sempre o da principal
    elif k == 0 or k >= len(CFG["sel"]) - 1: c = "principal"
    else:
        c = cam if cam != "apoio" else "principal"
        if shot >= 4.5: c = "zoom" if c == "principal" else "principal"
    if c != cam: shot = 0.0
    cam = c
    f0 = round(a * 30); nf = max(1, round(b * 30) - f0)
    clips.append({"fid": fid, "a": f0 / 30, "nf": nf, "cam": c, "o": t, "ws": ws}); t += nf / 30; shot += nf / 30
dur = t
print("PLANO", len(clips), "cortes", round(dur, 1), "s", " ".join(c["cam"][0] for c in clips), flush=True)
linhas = []
for i, c in enumerate(clips):
    seg = TMP / f"{CFG['versao']}_{i:03d}.mov"; d = c["nf"] / 30
    if c["cam"] == "apoio":
        sh("ffmpeg", "-y", "-v", "error", "-ss", f"{c['a'] - OFFA:.4f}", "-i", RAW / "apoio2711.mp4", "-ss", f"{c['a']:.4f}", "-i", CFR, "-t", f"{d:.4f}",
           "-map", "0:v:0", "-map", "1:a:0", "-vf", "fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p",
           "-af", f"aresample=48000,aformat=channel_layouts=mono,apad=whole_dur={d:.4f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "pcm_s16le",
           "-video_track_timescale", "30", "-frames:v", str(c["nf"]), seg)
    else:
        vf = "scale=1210:2150,crop=1080:1920:(iw-1080)/2:(ih-1920)*0.30" if c["cam"] == "zoom" else "null"
        sh("ffmpeg", "-y", "-v", "error", "-ss", f"{c['a']:.4f}", "-i", CFR, "-frames:v", str(c["nf"]), "-vf", vf + ",setsar=1,format=yuv420p",
           "-af", f"atrim=0:{d:.4f},apad=whole_dur={d:.4f}", "-t", f"{d:.4f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "pcm_s16le",
           "-video_track_timescale", "30", seg)
    linhas.append(f"file '{seg}'")
(TMP / "lista.txt").write_text("\n".join(linhas)); junto = TMP / "junto.mov"
sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", TMP / "lista.txt", "-c", "copy", junto)
FIXF = CFG.get("fixf", {})
def fixf(fid, p):
    for a, b in FIXF.get(str(fid), {}).items(): p = re.sub(r"\b" + re.escape(a) + r"\b", b, p, flags=re.I)
    return p
ws = [(c["o"] + w[0] - c["a"], c["o"] + w[1] - c["a"], fixf(c["fid"], fix(w[2]))) for c in clips for w in c["ws"]]
def ts(x):
    h, r = divmod(max(0, x), 3600); m, s = divmod(r, 60); return f"{int(h)}:{int(m):02d}:{s:05.2f}"
L = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "", "[V4+ Styles]",
     "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
     "Style: L,DejaVu Sans,68,&H00FFFFFF,&H0000CCFF,&H00101010,&H00000000,1,0,0,0,100,100,0,0,1,5,0,2,90,90,500,1", "", "[Events]",
     "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for i in range(0, len(ws), 3):
    g = ws[i:i + 3]
    for j, w in enumerate(g):
        txt = " ".join(("{\\c&H00CCFF&}" + x[2] + "{\\c&HFFFFFF&}") if k == j else x[2] for k, x in enumerate(g))
        prox = ws[i + 3][0] if i + 3 < len(ws) else 1e9; fim = g[j + 1][0] if j + 1 < len(g) else min(w[1] + 0.15, prox)
        L.append(f"Dialogue: 0,{ts(w[0])},{ts(max(fim, w[0] + 0.06))},L,,0,0,0,,{txt}")
leg = TMP / "leg.ass"; leg.write_text("\n".join(L), encoding="utf-8")
entradas = ["-i", junto]; fc = "[0:v]eq=contrast=1.04:saturation=1.08[b0]"; ult = "[b0]"
assin = Path("/dados/marca/assinatura-amarelo.mov")
if assin.exists():
    da = 1.7; ini = max(0, dur - da - 0.1); f = TMP / "vinheta.mov"
    sh("ffmpeg", "-y", "-v", "error", "-i", assin, "-t", f"{da:.2f}", "-vf", "fps=30,format=rgba,scale=300:-1,pad=1080:1920:1080-iw-70:1920-ih-260:color=black@0", "-an", "-c:v", "png", f)
    entradas += ["-itsoffset", f"{ini:.3f}", "-i", f]; fc += f";{ult}[1:v]overlay=eof_action=pass:enable='between(t,{ini:.3f},{dur:.3f})'[o1]"; ult = "[o1]"
fc += f";{ult}subtitles='{leg}':fontsdir='{FONTS}'[vf]"
rnn = Path("/cache/sh.rnnn")
fc += ";[0:a]highpass=f=80" + (f",arnndn=m='{rnn}':mix=0.7" if rnn.exists() else "") + ",acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150,loudnorm=I=-14:TP=-1.5:LRA=9[a]"
final = OUT / f"Eulino Falante - {CFG['versao']}.mp4"
sh("ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", fc, "-map", "[vf]", "-map", "[a]", "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "22",
   "-maxrate", "2600k", "-bufsize", "5200k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", final)
def medir(f):
    e = saida("ffmpeg", "-hide_banner", "-nostats", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-")
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", e); return float(m[-1]) if m else None
li = medir(final)
if li is not None and abs(li + 14) > 0.4:
    tmpf = TMP / "ganho.mp4"
    sh("ffmpeg", "-y", "-v", "error", "-i", final, "-c:v", "copy", "-af", f"volume={-14 - li:.2f}dB,alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", tmpf)
    os.replace(tmpf, final); li = medir(final)
lufs = [f"I: {li} LUFS"] if li is not None else []
qd = OUT / f"quadros_{CFG['versao']}"; qd.mkdir(exist_ok=True)
for k in range(10):
    tt = dur * (k + 0.5) / 10; sh("ffmpeg", "-y", "-v", "error", "-ss", f"{tt:.2f}", "-i", final, "-frames:v", "1", "-vf", "scale=360:-2", qd / f"{k}_{tt:05.1f}.jpg")
from faster_whisper import WhisperModel
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=2)
wv = TMP / "qc.wav"; sh("ffmpeg", "-y", "-v", "error", "-i", final, "-ac", "1", "-ar", "16000", wv)
ww = wave.open(str(wv)); x = np.frombuffer(ww.readframes(ww.getnframes()), np.int16).astype(np.float32) / 32768
norm = lambda s: re.sub(r"[^\wà-ú ]", "", s.lower()).split(); us = []; falhas = []
dreal = float(saida("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final).strip() or 0)
if abs(dreal - dur) > 0.3: falhas.append(f"duração {dreal:.1f}s ≠ plano {dur:.1f}s")
# QC por corte: cada corte do plano tem de soar como o texto esperado, no lugar esperado
for i, c in enumerate(clips):
    a0, a1 = int(c["o"] * 16000), int((c["o"] + c["nf"] / 30) * 16000)
    segs, _ = m.transcribe(x[a0:a1], language="pt", condition_on_previous_text=False, vad_filter=False)
    tx = " ".join(s_.text.strip() for s_ in segs).strip(); esp = " ".join(w[2] for w in c["ws"])
    r = difflib.SequenceMatcher(None, norm(tx), norm(esp)).ratio()
    us.append((c["o"], tx)); print(f"Q {c['o']:6.1f} [{c['fid']:02d}] {r:.2f} | {tx}", flush=True)
    if r < 0.6 and len(norm(esp)) > 2: falhas.append(f"{c['o']:.1f}s frase {c['fid']}: ouvi '{tx[:50]}' / esperado '{esp[:50]}'")
rep = [f"{us[i][0]:.1f}s '{us[i][1][:40]}'" for i in range(len(us)) for j in range(i + 1, min(i + 4, len(us)))
       if (lambda a, b: min(len(a), len(b), 6) >= 3 and difflib.SequenceMatcher(None, a[:6], b[:6]).ratio() >= 0.75)(norm(us[i][1]), norm(us[j][1]))
       and us[j][0] - us[i][0] < 30 and i != 0]
info = {"dur": round(dur, 1), "cortes": len(clips), "mb": round(final.stat().st_size / 1e6, 1), "lufs": lufs[-1] if lufs else None, "repeticoes": rep, "falhas": falhas}
print("INFO", json.dumps(info, ensure_ascii=False), flush=True)
ENT = Path("/dados/entregas"); dst = ENT / f"r2711-eulino-{CFG['versao']}.mp4"; shutil.copy(final, dst)
resumo = f"🎬 Reel · Eulino Falante — {CFG['versao']} (padrão, sem motion)\n⏱ {info['dur']:.0f} s · {info['cortes']} cortes · {info['lufs'] or ''}\n\nNota: {CFG['nota']}/10\n{CFG['resumo']}\n\nNota a partir da transcrição + medidas + quadros."
if falhas or rep: print("NAO-ENTREGUE: o QC achou problema — corrigir antes de mandar ao Pedro", flush=True)
if not CFG.get("so_render") and not falhas and not rep:
    json.dump({"arquivo": str(dst), "titulo": "Eulino Falante — os nossos censores", "versao": CFG["versao"], "estilo": "padrao", "nota": CFG["nota"].replace(",", "."),
               "resumo": resumo[:1020]}, open(ENT / f"r2711-eulino-{CFG['versao']}.json", "w"), ensure_ascii=False)
import docker
cs = docker.from_env().containers.get("assumpcao-sync")
cmd = ['sh', '-c', 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"$GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; exec rclone "$@"', 'x', "copy", str(OUT), "gdrive:_analises/r2711/out"]
print("rclone", cs.exec_run(cmd).exit_code, flush=True)
print("FIM-EDITA", flush=True)
