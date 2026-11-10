"""Vigia a pasta de entrada e roda o pipeline em cada vídeo novo, um por vez.

Entrada:  /dados/entrada   (cópia da 01 Brutos)
Saída:    /dados/prontos   (vai para 02 Prontos)
Usados:   /dados/usados    (bruto já processado)
"""
import os, shutil, subprocess, time
from pathlib import Path

ENT, PRO, USA = (Path(os.environ.get(k, d)) for k, d in
                 (("ENTRADA", "/dados/entrada"), ("PRONTOS", "/dados/prontos"), ("USADOS", "/dados/usados")))
VIDEO = {".mp4", ".mov", ".m4v", ".mkv"}
ESPERA = int(os.environ.get("INTERVALO", "60"))

for p in (ENT, PRO, USA):
    p.mkdir(parents=True, exist_ok=True)


def estavel(p, s=10):
    """Só processa quando o arquivo parou de crescer (upload terminado)."""
    a = p.stat().st_size; time.sleep(s); return p.exists() and p.stat().st_size == a


while True:
    for f in sorted(ENT.iterdir()):
        if f.suffix.lower() not in VIDEO or not estavel(f):
            continue
        print("processando", f.name, flush=True)
        r = subprocess.run(["python", "/app/edicao/pipeline.py", str(f), str(PRO)])
        destino = USA if r.returncode == 0 else ENT / "_erro"
        destino.mkdir(exist_ok=True)
        shutil.move(str(f), destino / f.name)
    time.sleep(ESPERA)
