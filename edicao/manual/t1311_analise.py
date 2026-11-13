"""Trial 13/11 — etapa de análise: junta os brutos, acha a palma, transcreve o áudio externo, tira quadros."""
import json, os, shutil, subprocess, glob
from pathlib import Path
import numpy as np

B = Path("/dados/trial1311"); RAW = B / "raw"; AN = B / "an"; FR = AN / "frames"
for p in (RAW, AN, FR): p.mkdir(parents=True, exist_ok=True)

def sh(*c, cap=False):
    r = subprocess.run([str(x) for x in c], capture_output=True, text=True)
    if r.returncode: print("ERRO", c[:3], r.stderr[-400:], flush=True)
    return r.stdout if cap else r.returncode

# 1) brutos já baixados pelo sync -> raw (fica a cópia "especial")
for f in glob.glob("/dados/entrada/*1311*"):
    n = Path(f).name
    if n.startswith("padrao__"): os.remove(f); print("removido duplicado", n); continue
    shutil.move(f, RAW / n.split("__", 1)[-1]); print("movido", n)
for f in glob.glob("/dados/usados/*1311*"):
    n = Path(f).name.split("__", 1)[-1]
    if not (RAW / n).exists(): shutil.copy(f, RAW / n); print("copiado de usados", n)

# 2) arquivos que não são vídeo (áudio do BOYALINK) e listagem das pastas, via rclone do sync
import docker
c = docker.from_env().containers.get("assumpcao-sync")
def rc(*args):
    cmd = ['sh', '-c', 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"$GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; shift; exec rclone "$@"', 'x', *args]
    r = c.exec_run(cmd, demux=True); out = (r.output[0] or b"").decode(); err = (r.output[1] or b"").decode()
    if r.exit_code: print("rclone erro", args[:2], err[-300:], flush=True)
    return out
for pasta in ["01 Brutos/especial", "01 Brutos/padrao", "01 Brutos", "04 Acervo", "04 Acervo/Obras"]:
    try:
        lst = json.loads(rc("lsjson", f"gdrive:{pasta}") or "[]")
        print(f"## {pasta}:", "; ".join(f"{x['Name']}{'/' if x['IsDir'] else ''} {x.get('Size',0)//1000}KB" for x in lst), flush=True)
    except Exception as e: print("lsjson falhou", pasta, e)
rc("copy", "gdrive:01 Brutos/especial", "/dados/trial1311/raw", "--exclude", "*.{mp4,MP4,mov,MOV,m4v}")
print("raw:", [(p.name, p.stat().st_size // 1000) for p in RAW.iterdir()], flush=True)

# 3) metadados
info = {}
for p in sorted(RAW.iterdir()):
    j = json.loads(sh("ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", p, cap=True) or "{}")
    v = next((s for s in j.get("streams", []) if s["codec_type"] == "video"), None)
    a = next((s for s in j.get("streams", []) if s["codec_type"] == "audio"), None)
    rot = 0
    if v:
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd: rot = sd["rotation"]
        rot = rot or int((v.get("tags") or {}).get("rotate", 0))
    info[p.name] = {"dur": float(j.get("format", {}).get("duration", 0)),
                    "video": v and f"{v['width']}x{v['height']} {v.get('codec_name')} {v.get('r_frame_rate')} rot={rot}",
                    "audio": a and f"{a.get('codec_name')} {a.get('sample_rate')}Hz ch={a.get('channels')}"}
print("INFO", json.dumps(info, ensure_ascii=False), flush=True)

# 4) áudio de cada arquivo em wav 16 kHz mono + palma
SR = 16000
def wav(p):
    o = AN / (p.stem + ".wav")
    sh("ffmpeg", "-y", "-v", "error", "-i", p, "-vn", "-ac", "1", "-ar", SR, o); return o
def ler(o):
    import wave
    w = wave.open(str(o)); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
audios = {}
for p in sorted(RAW.iterdir()):
    if info[p.name]["audio"]: audios[p.name] = ler(wav(p))
def env(x, hop=160):  # envelope 10 ms
    n = len(x) // hop; return np.abs(x[:n * hop]).reshape(n, hop).max(1)
palmas = {}
for n, x in audios.items():
    e = env(x[: SR * 25]); i = int(e.argmax()); palmas[n] = {"t": i / 100, "pico": float(e[i]), "media": float(e.mean())}
print("PALMAS", json.dumps(palmas), flush=True)
# referência = arquivo que não é vídeo (áudio externo) se houver; senão o maior
ext = [n for n in audios if not info[n]["video"]]
ref = ext[0] if ext else max(audios, key=lambda n: info[n]["dur"])
off = {}
er = env(audios[ref])
for n, x in audios.items():
    e = env(x)
    # correlação dos envelopes (diferenças, para realçar ataques) nos primeiros 60 s
    a = np.diff(er[:6000]); b = np.diff(e[:6000]); a = a - a.mean(); b = b - b.mean()
    cc = np.correlate(a, b, "full"); lag = int(cc.argmax()) - (len(b) - 1)
    off[n] = {"lag_s": lag / 100, "por_palma_s": round(palmas[ref]["t"] - palmas[n]["t"], 2)}
print("REF", ref, "OFFSETS (somar ao tempo do arquivo para virar tempo da referência)", json.dumps(off), flush=True)
json.dump({"info": info, "palmas": palmas, "ref": ref, "offsets": off}, open(AN / "sync.json", "w"), indent=1)

# 5) transcrição da referência com palavras
from faster_whisper import WhisperModel
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=2)
segs, _ = m.transcribe(str(AN / (Path(ref).stem + ".wav")), language="pt", word_timestamps=True, vad_filter=True,
                       vad_parameters={"min_silence_duration_ms": 400}, condition_on_previous_text=False)
dados = []
for s in segs:
    dados.append({"ini": round(s.start, 2), "fim": round(s.end, 2), "t": s.text.strip(),
                  "w": [[round(w.start, 2), round(w.end, 2), w.word.strip(), round(w.probability, 2)] for w in (s.words or [])]})
    print(f"SEG {s.start:7.2f}-{s.end:7.2f} | {s.text.strip()}", flush=True)
json.dump(dados, open(AN / "transcricao.json", "w"), ensure_ascii=False, indent=0)

# 6) quadros de cada câmera
for p in sorted(RAW.iterdir()):
    if not info[p.name]["video"]: continue
    d = info[p.name]["dur"]
    for k in range(8):
        t = d * (k + 0.5) / 8
        sh("ffmpeg", "-y", "-v", "error", "-ss", f"{t:.1f}", "-i", p, "-frames:v", "1", "-vf", "scale=360:-2", FR / f"{p.stem}_{int(t):04d}.jpg")
rc("copy", "/dados/trial1311/an", "gdrive:_analises/trial-1311", "--exclude", "*.wav")
print("FIM-ANALISE", flush=True)
