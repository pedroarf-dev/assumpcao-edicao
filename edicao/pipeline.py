"""Robô de edição do @assumpcao_pedro.

Para cada vídeo bruto:
  1. corta pausas e respirações (Auto-Editor), mantendo margem para pausas dramáticas;
  2. transcreve em português (faster-whisper) e gera .srt, .txt e .json com tempos;
  3. renderiza uma versão com legenda na tela (padrão fixo) e a vinheta final (assinatura + som);
  4. salva um quadro de prévia.

Uso:  python pipeline.py ENTRADA.mp4 PASTA_SAIDA [--sem-vinheta] [--sem-legenda]
"""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MARCA = Path(os.environ.get("MARCA", "/dados/marca"))
CFG = json.loads((AQUI.parent / "config.json").read_text()) if (AQUI.parent / "config.json").exists() else {}
MODELO = CFG.get("modelo_whisper") or os.environ.get("WHISPER_MODEL", "small")
CACHE = Path(os.environ.get("HF_HOME", "/tmp")).parent
RNN_URL = "https://raw.githubusercontent.com/richardpl/arnndn-models/master/sh.rnnn"
MARGEM = os.environ.get("CORTE_MARGEM", "0.25s,0.35s")   # antes,depois de cada fala
LIMIAR = os.environ.get("CORTE_LIMIAR", "audio:threshold=0.035")


def sh(*cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def duracao(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def normalizar(entrada, saida_dir, base):
    """Aplica a rotação do celular e deixa tudo em 1080x1920, 30 fps (o Auto-Editor perde a rotação)."""
    norm = saida_dir / f"{base} - vertical.mp4"
    af = "highpass=f=80"
    if CFG.get("limpar_voz", True):
        rnn = CACHE / "sh.rnnn"
        if not rnn.exists():
            try:
                import urllib.request; urllib.request.urlretrieve(RNN_URL, rnn)
            except Exception as e:
                print("aviso: sem modelo de limpeza de voz:", e, flush=True)
        if rnn.exists():
            af += f",arnndn=m='{rnn.as_posix()}':mix=0.85"
    af += (",acompressor=threshold=-20dB:ratio=2.5:attack=5:release=150"
           f",loudnorm=I={CFG.get('loudness_lufs', -14)}:TP=-1.5:LRA=11")
    sh("ffmpeg", "-y", "-v", "error", "-i", entrada,
       "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
       "-af", af, "-ar", "48000",
       "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "192k", norm)
    return norm


def cortar(entrada, saida_dir, base):
    entrada = normalizar(entrada, saida_dir, base)
    cortado = saida_dir / f"{base} - cortado.mp4"
    try:
        sh("auto-editor", entrada, "--edit", LIMIAR, "--margin", MARGEM,
           "--no-open", "-o", cortado)
    except subprocess.CalledProcessError:
        # vídeo sem fala (ex.: timelapse do ateliê): segue sem cortar
        print("aviso: nada para cortar; usando o bruto inteiro", flush=True)
        shutil.copy(entrada, cortado)
        return cortado
    # projeto para o Premiere, para ajustar cortes à mão
    try:
        sh("auto-editor", entrada, "--edit", LIMIAR, "--margin", MARGEM,
           "--export", "premiere", "--no-open", "-o", saida_dir / f"{base} - premiere.xml")
    except subprocess.CalledProcessError:
        print("aviso: exportação para Premiere falhou; seguindo", flush=True)
    return cortado


def fmt(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def transcrever(video, saida_dir, base):
    from faster_whisper import WhisperModel
    modelo = WhisperModel(MODELO, device="cpu", compute_type="int8")
    # mesmas opções anti-alucinação do transcritor do VPS (v2, 12/11)
    segs, _ = modelo.transcribe(str(video), language="pt", word_timestamps=True, vad_filter=True,
                                vad_parameters={"min_silence_duration_ms": 500},
                                condition_on_previous_text=False, hallucination_silence_threshold=2.0)
    segs = list(segs)
    dados = [{"ini": s.start, "fim": s.end, "texto": s.text.strip(),
              "palavras": [{"ini": w.start, "fim": w.end, "p": w.word.strip()} for w in (s.words or [])]}
             for s in segs]
    (saida_dir / f"{base} - transcricao.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    (saida_dir / f"{base} - transcricao.txt").write_text("\n".join(d["texto"] for d in dados), encoding="utf-8")
    srt = []
    for i, d in enumerate(dados, 1):
        srt += [str(i), f"{fmt(d['ini'])} --> {fmt(d['fim'])}", d["texto"], ""]
    (saida_dir / f"{base} - legenda.srt").write_text("\n".join(srt), encoding="utf-8")
    return dados


def ass_legenda(dados, caminho):
    """Legenda padrão: branca com contorno, palavra falada em amarelo placa (#FFCC00), 2–4 palavras por tela."""
    def t(x):
        h, r = divmod(x, 3600); m, s = divmod(r, 60)
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"
    linhas = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
              "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
              "Style: L,DejaVu Sans,74,&H00FFFFFF,&H0000CCFF,&H00101010,&H00000000,1,0,0,0,100,100,0,0,1,5,0,2,80,80,560,1",
              "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for d in dados:
        ps = d["palavras"] or [{"ini": d["ini"], "fim": d["fim"], "p": d["texto"]}]
        for i in range(0, len(ps), 3):
            grupo = ps[i:i + 3]
            for j, w in enumerate(grupo):
                txt = " ".join(("{\\c&H00CCFF&}" + g["p"] + "{\\c&HFFFFFF&}") if k == j else g["p"]
                               for k, g in enumerate(grupo))
                fim = grupo[j + 1]["ini"] if j + 1 < len(grupo) else w["fim"]
                linhas.append(f"Dialogue: 0,{t(w['ini'])},{t(max(fim, w['ini'] + 0.05))},L,,0,0,0,,{txt}")
    Path(caminho).write_text("\n".join(linhas), encoding="utf-8")


def renderizar(video, dados, saida_dir, base, com_legenda=True, com_vinheta=True):
    final = saida_dir / f"{base} - final.mp4"
    dur = duracao(video)
    filtros, entradas, mapa_a = [], ["-i", str(video)], "0:a"
    v = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    if CFG.get("zoom_alternado", True) and len(dados) > 1:
        z = CFG.get("zoom", 1.12); cy = CFG.get("zoom_centro_y", 0.36)
        trechos = "+".join(f"between(t,{d['ini']:.2f},{dados[i+1]['ini'] if i+1 < len(dados) else d['fim']:.2f})"
                           for i, d in enumerate(dados) if i % 2 == 1)
        cond = trechos.replace("t,", "in/30,")
        v += (f",zoompan=z='if({cond},{z},1)':x='iw/2-iw/zoom/2':y='(ih-ih/zoom)*{cy}'"
              f":d=1:s=1080x1920:fps=30")
    if com_legenda and dados:
        ass = saida_dir / f"{base}.ass"; ass_legenda(dados, ass)
        v += f",subtitles='{ass.as_posix()}'"
    filtros.append(v + "[v0]")
    ultimo = "[v0]"
    assin, som = MARCA / "assinatura-amarelo.mov", MARCA / "som-assinatura-padrao.wav"
    if com_vinheta and assin.exists() and som.exists():
        ini = max(0.0, dur - 1.8)
        entradas += ["-itsoffset", f"{ini:.2f}", "-i", str(assin), "-i", str(som)]
        filtros.append(f"[1:v]scale=300:-1[ass];{ultimo}[ass]overlay=x=W-w-70:y=H-h-260:eof_action=repeat[v1]")
        ultimo = "[v1]"
        ms = int(ini * 1000)
        # baixa o áudio do vídeo 0,3 s antes da coroa e entra a caneta
        filtros.append(f"[0:a]volume='if(gte(t,{ini - 0.3:.2f}),0.55,1)':eval=frame[a0];"
                       f"[2:a]adelay={ms}|{ms}[a1];[a0][a1]amix=inputs=2:normalize=0:duration=first[a]")
        mapa_a = "[a]"
    sh("ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", ";".join(filtros),
       "-map", ultimo, "-map", mapa_a, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final)
    sh("ffmpeg", "-y", "-v", "error", "-ss", f"{min(2.0, dur / 2):.2f}", "-i", final,
       "-frames:v", "1", "-vf", "scale=540:-1", saida_dir / f"{base} - previa.jpg")
    return final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada"); ap.add_argument("saida")
    ap.add_argument("--sem-vinheta", action="store_true"); ap.add_argument("--sem-legenda", action="store_true")
    ap.add_argument("--sem-transcricao", action="store_true")
    ap.add_argument("--estilo", default="padrao", choices=["natural", "padrao", "especial"])
    a = ap.parse_args()
    entrada = Path(a.entrada); base = entrada.stem
    if "__" in base and base.split("__", 1)[0] in ("natural", "padrao", "especial"):
        base = base.split("__", 1)[1]   # tira o prefixo de estilo posto pelo sync
    destino = Path(a.saida) / base
    # trabalha numa pasta à parte e só move para "prontos" no fim (o sync não pega arquivo pela metade)
    saida = Path(os.environ.get("TRABALHO", str(Path(a.saida).parent / "trabalho"))) / base
    if saida.exists(): shutil.rmtree(saida)
    saida.mkdir(parents=True, exist_ok=True)
    cortado = cortar(entrada, saida, base)
    dados = [] if a.sem_transcricao else transcrever(cortado, saida, base)
    renderizar(cortado, dados, saida, base, not a.sem_legenda, not a.sem_vinheta)
    (saida / "PRONTO.txt").write_text(
        f"bruto: {entrada.name}\nestilo: {a.estilo}\nduração bruto: {duracao(entrada):.1f}s\nduração cortado: {duracao(cortado):.1f}s\n",
        encoding="utf-8")
    for f in list(saida.glob("* - vertical.mp4")) + list(saida.glob("*.ass")):
        f.unlink()   # intermediários
    if destino.exists(): shutil.rmtree(destino)
    shutil.move(str(saida), str(destino))
    print("ok:", destino, flush=True)


if __name__ == "__main__":
    sys.exit(main())
