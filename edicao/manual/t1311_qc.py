"""Transcreve as versões editadas e aponta trechos repetidos (n-gramas de 3+ palavras que reaparecem em até 25 s)."""
import json, re, subprocess
from pathlib import Path
from faster_whisper import WhisperModel
OUT = Path("/dados/trial1311/out")
m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=2)
norm = lambda w: re.sub(r"[^\wà-ú]", "", w.lower())
for v in "AB":
    f = OUT / f"Trial qualquer criança faz - {v}.mp4"
    segs, _ = m.transcribe(str(f), language="pt", word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
    ws = []
    print(f"===== {v} =====", flush=True)
    for s in segs:
        print(f"T {s.start:6.2f}-{s.end:6.2f} | {s.text.strip()}", flush=True)
        ws += [(w.start, w.end, norm(w.word)) for w in (s.words or []) if norm(w.word)]
    achados = set()
    for n in (5, 4, 3):
        for i in range(len(ws) - n):
            g = tuple(x[2] for x in ws[i:i+n])
            for j in range(i + n, len(ws) - n + 1):
                if ws[j][0] - ws[i][0] > 25: break
                if tuple(x[2] for x in ws[j:j+n]) == g and not any(abs(ws[i][0]-a) < 1 for a, _ in achados):
                    achados.add((ws[i][0], ws[j][0])); print(f"REPETE {v}: {' '.join(g)!r} em {ws[i][0]:.2f}s e {ws[j][0]:.2f}s", flush=True)
                    break
print("FIM-QC")
