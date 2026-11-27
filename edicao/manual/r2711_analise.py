"""Reel 27/11 (Eulino Falante) — análise: brutos, palma (apoio x principal), transcrição por frase, quadros."""
import json, os, shutil, subprocess, glob, re, difflib, wave
from pathlib import Path
import numpy as np
B = Path("/dados/r2711"); RAW = B / "raw"; AN = B / "an"; FR = AN / "frames"
for p in (RAW, AN, FR): p.mkdir(parents=True, exist_ok=True)
def sh(*c, cap=False):
    r = subprocess.run([str(x) for x in c], capture_output=True, text=True)
    if r.returncode: print("ERRO", c[:3], r.stderr[-300:], flush=True)
    return r.stdout if cap else r.returncode
for f in glob.glob("/dados/entrada/*2711*") + glob.glob("/dados/usados/*2711*"):
    n = Path(f).name.split("__", 1)[-1]
    if not (RAW / n).exists(): shutil.copy(f, RAW / n); print("copiado", f, flush=True)
import docker
c = docker.from_env().containers.get("assumpcao-sync")
def rc(*args):
    cmd = ['sh', '-c', 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"$GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; exec rclone "$@"', 'x', *args]
    r = c.exec_run(cmd, demux=True); return (r.output[0] or b"").decode() + (r.output[1] or b"").decode()[-300:]
for n in ("principal2711.mp4", "apoio2711.mp4"):
    if not (RAW / n).exists(): print("baixando", n, rc("copyto", f"gdrive:01 Brutos/padrao/{n}", f"/dados/r2711/raw/{n}"), flush=True)
print("pasta capa:", rc("lsf", "gdrive:", "--dirs-only"), flush=True)
info = {}
for p in sorted(RAW.glob("*.mp4")):
    j = json.loads(sh("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", p, cap=True) or "{}")
    v = next((s for s in j.get("streams", []) if s["codec_type"] == "video"), {}); a = next((s for s in j.get("streams", []) if s["codec_type"] == "audio"), None)
    info[p.name] = {"dur": float(j["format"]["duration"]), "video": f"{v.get('width')}x{v.get('height')} {v.get('r_frame_rate')}", "audio": bool(a)}
print("INFO", json.dumps(info), flush=True)
SR = 16000
def wav(p):
    o = AN / (p.stem + ".wav"); sh("ffmpeg", "-y", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", SR, o)
    w = wave.open(str(o)); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
X = {p.name: wav(p) for p in sorted(RAW.glob("*.mp4")) if info[p.name]["audio"]}
def env(x, hop=160): n = len(x) // hop; return np.abs(x[:n * hop]).reshape(n, hop).max(1)
er = env(X["principal2711.mp4"]); off = {"principal2711.mp4": 0.0}
for n, x in X.items():
    if n == "principal2711.mp4": continue
    e = env(x); pa, pb = int(er[:3000].argmax()), int(e[:3000].argmax())
    a = np.diff(er[:6000]); b = np.diff(e[:6000]); a -= a.mean(); b -= b.mean(); cc = np.correlate(a, b, "full"); lag = int(cc.argmax()) - (len(b) - 1)
    off[n] = {"palma_principal": pa / 100, "palma_apoio": pb / 100, "por_palma": round((pa - pb) / 100, 2), "corr": lag / 100}
print("SYNC (t_principal = t_apoio + off)", json.dumps(off), flush=True)
json.dump({"info": info, "off": off}, open(AN / "sync.json", "w"))
from faster_whisper import WhisperModel
from faster_whisper.vad import get_speech_timestamps, VadOptions
x = X["principal2711.mp4"]; m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=2)
U = []
for t in get_speech_timestamps(x, VadOptions(min_silence_duration_ms=350, speech_pad_ms=120, threshold=0.45)):
    a, b = t["start"], t["end"]
    if (b - a) / SR < 0.3: continue
    segs, _ = m.transcribe(x[a:b], language="pt", word_timestamps=True, vad_filter=False, condition_on_previous_text=False, beam_size=5,
                           initial_prompt="Eulino Falante. Quantas coisas você deixou de fazer sem ninguém te proibir? Pega um café.")
    ws = [[round(a / SR + w.start, 2), round(a / SR + w.end, 2), w.word.strip(), round(w.probability, 2)] for s in segs for w in (s.words or [])]
    if ws: U.append({"ini": ws[0][0], "fim": ws[-1][1], "t": " ".join(w[2] for w in ws), "w": ws})
for i, u in enumerate(U):
    pm = np.mean([w[3] for w in u["w"]]); print(f"F{i:03d} {u['ini']:7.2f}-{u['fim']:7.2f} p={pm:.2f} | {u['t']}", flush=True)
json.dump(U, open(AN / "frases.json", "w"), ensure_ascii=False)
for p in sorted(RAW.glob("*.mp4")):
    d = info[p.name]["dur"]
    for k in range(8):
        tt = d * (k + 0.5) / 8; sh("ffmpeg", "-y", "-v", "error", "-ss", f"{tt:.1f}", "-i", p, "-frames:v", "1", "-vf", "scale=360:-2", FR / f"{p.stem}_{int(tt):04d}.jpg")
print(rc("copy", "/dados/r2711/an", "gdrive:_analises/r2711", "--exclude", "*.wav"), flush=True)
print("FIM-ANALISE", flush=True)
