import json, subprocess, docker, numpy as np, wave
from pathlib import Path
c = docker.from_env().containers.get("assumpcao-sync")
def rc(*args):
    cmd = ['sh', '-c', 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"$GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; exec rclone "$@"', 'x', *args]
    r = c.exec_run(cmd, demux=True); out = (r.output[0] or b"").decode()
    if r.exit_code: print("rclone erro", args[:2], (r.output[1] or b"").decode()[-300:], flush=True)
    return out
for pasta in ["01 Brutos/especial", "01 Brutos/padrao", "01 Brutos", "04 Acervo", "04 Acervo/Obras", "_analises"]:
    lst = json.loads(rc("lsjson", f"gdrive:{pasta}") or "[]")
    print(f"## {pasta}:", "; ".join(f"{x['Name']}{'/' if x['IsDir'] else ''} {x.get('Size',0)//1000}KB" for x in lst), flush=True)
rc("copy", "gdrive:01 Brutos/especial", "/dados/trial1311/raw", "--exclude", "*.{mp4,MP4,mov,MOV,m4v}")
rc("copy", "/dados/trial1311/an", "gdrive:_analises/trial-1311", "--exclude", "*.wav")
print("raw:", [p.name for p in Path("/dados/trial1311/raw").iterdir()])
# qualidade do áudio de cada fonte: nível de fala x fundo (percentis do envelope de 50 ms)
for w in sorted(Path("/dados/trial1311/an").glob("*.wav")):
    f = wave.open(str(w)); x = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
    n = len(x) // 800; e = np.sqrt((x[:n*800].reshape(n, 800) ** 2).mean(1)) + 1e-9
    db = 20 * np.log10(e); print(w.name, "fala(p90) %.1f dB, fundo(p10) %.1f dB, SNR ~%.1f dB" % (np.percentile(db, 90), np.percentile(db, 10), np.percentile(db, 90) - np.percentile(db, 10)), flush=True)
print("FIM-LISTA")
