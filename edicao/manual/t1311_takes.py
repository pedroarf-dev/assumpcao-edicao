"""Transcrição por frase (VAD -> cada trecho de fala transcrito sozinho) para achar takes repetidos que o Whisper junta."""
import json, re, wave, difflib
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.vad import get_speech_timestamps, VadOptions
AN = Path("/dados/trial1311/an"); SR = 16000
f = wave.open(str(AN / "principal1311.wav")); x = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
OFF = json.load(open(AN / "sync.json"))["offsets"]["principal1311.mp4"]["lag_s"]   # t_ref = t_pixel + OFF
ts = get_speech_timestamps(x, VadOptions(min_silence_duration_ms=350, speech_pad_ms=120, threshold=0.45))
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=2)
U = []
for t in ts:
    a, b = t["start"], t["end"]
    if (b - a) / SR < 0.3: continue
    segs, _ = m.transcribe(x[a:b], language="pt", word_timestamps=True, vad_filter=False, condition_on_previous_text=False, beam_size=5)
    ws = [[round(a / SR + w.start + OFF, 2), round(a / SR + w.end + OFF, 2), w.word.strip()] for s in segs for w in (s.words or [])]
    if not ws: continue
    U.append({"ini": ws[0][0], "fim": ws[-1][1], "t": " ".join(w[2] for w in ws), "w": ws})
norm = lambda s: re.sub(r"[^\wà-ú ]", "", s.lower()).split()
for i, u in enumerate(U):
    u["drop"] = None
    a = norm(u["t"])
    for j in range(i + 1, min(i + 6, len(U))):
        v = U[j]
        if v["ini"] - u["fim"] > 40: break
        b = norm(v["t"]); k = min(len(a), len(b), 6)
        if k >= 2 and difflib.SequenceMatcher(None, a[:k], b[:k]).ratio() >= 0.7:
            u["drop"] = f"refeito em {v['ini']:.1f}s"; break
for u in U:
    print(f"{'XX' if u['drop'] else '  '} {u['ini']:7.2f}-{u['fim']:7.2f} | {u['t']}" + (f"   <- {u['drop']}" if u['drop'] else ""), flush=True)
json.dump(U, open(AN / "frases.json", "w"), ensure_ascii=False, indent=0)
print("FIM-TAKES")
