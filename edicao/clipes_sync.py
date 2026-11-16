"""Copia os clipes de apoio (ex.: gerados no Google Flow) do Drive para o VPS, a cada 2 min.
Drive: 04 Acervo/Clipes IA  ->  /dados/clipes  (clipe .mp4 + manifesto <id>.json). Usa o rclone do contêiner assumpcao-sync."""
import time
import docker
PASTA = "gdrive:04 Acervo/Clipes IA"
def rc(cs, *args):
    cmd = ['sh', '-c', 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"$GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; exec rclone "$@"', 'x', *args]
    r = cs.exec_run(cmd, demux=True); return r.exit_code, (r.output[1] or b"").decode()[-200:]
criada = False
while True:
    try:
        cs = docker.from_env().containers.get("assumpcao-sync")
        if not criada: print("mkdir", rc(cs, "mkdir", PASTA)[0], flush=True); criada = True
        code, err = rc(cs, "copy", PASTA, "/dados/clipes", "--include", "*.{mp4,MP4,mov,MOV,json}")
        print("clipes ok" if code == 0 else f"clipes erro {code}: {err}", time.strftime("%H:%M"), flush=True)
    except Exception as e:
        print("erro:", e, flush=True)
    time.sleep(120)
