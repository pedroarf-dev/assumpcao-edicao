"""Biblioteca de psicanálise — fase 2, piloto com 10 livros (custo zero de IA).
Baixa um PDF por vez (rclone via assumpcao-sync), extrai o texto (pdftotext; OCR em português se for escaneado),
indexa por página num SQLite FTS5 local e apaga o PDF. Mede tempo e tamanho. Só lê o Drive."""
import json, os, random, re, sqlite3, subprocess, time
from pathlib import Path
import docker

B = Path("/dados/biblioteca"); TMP = B / "tmp"; TMP.mkdir(parents=True, exist_ok=True)
DBF = B / "indice.db"; REL = B / "piloto.json"
N = int(os.environ.get("N_LIVROS", "10")); MAX_MB = int(os.environ.get("MAX_MB", "60"))
cs = docker.from_env().containers.get("assumpcao-sync")

def rc(*args):
    cmd = ['sh', '-c', 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"$GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; exec rclone "$@"', 'x', *args]
    r = cs.exec_run(cmd, demux=True); return r.exit_code, (r.output[0] or b"").decode(), (r.output[1] or b"").decode()

def run(*c, timeout=None):
    return subprocess.run([str(x) for x in c], capture_output=True, text=True, timeout=timeout)

# ---------- escolha dos 10 (sem duplicados por md5; mistura de tamanhos) ----------
ls = json.load(open(B / "lsjson.json"))
print("lsjson:", len(ls), "itens; chaves:", sorted(ls[0].keys()), flush=True)
vistos, pdfs = set(), []
for x in sorted(ls, key=lambda x: len(x.get("Path", ""))):
    if x.get("IsDir") or not x.get("Name", "").lower().endswith(".pdf"): continue
    md5 = (x.get("Hashes") or {}).get("md5") or x.get("ID")
    if md5 in vistos: continue
    vistos.add(md5); pdfs.append(x)
mb = lambda x: x.get("Size", 0) / 1e6
random.seed(1311)
faixas = [([p for p in pdfs if 0.3 <= mb(p) < 8], 5), ([p for p in pdfs if 8 <= mb(p) < 25], 3), ([p for p in pdfs if 25 <= mb(p) <= MAX_MB], 2)]
escolha = []
for lista, q in faixas: escolha += random.sample(lista, min(q, len(lista)))
escolha = escolha[:N]
print("PDFs únicos:", len(pdfs), "| escolhidos:", len(escolha), flush=True)
for p in escolha: print(f"  {mb(p):6.1f} MB | {p['Path'][:110]}", flush=True)

# ---------- índice ----------
con = sqlite3.connect(DBF)
con.execute("create table if not exists livros (id text primary key, caminho text, arquivo text, mb real, paginas int, escaneado int, chars int, seg_texto real, seg_ocr real, indexado_em text)")
con.execute("create virtual table if not exists paginas using fts5(texto, livro unindexed, pagina unindexed, tokenize=\"unicode61 remove_diacritics 2\")")
con.commit()

rel = []
for p in escolha:
    fid, nome = p["ID"], p["Name"]
    if con.execute("select 1 from livros where id=?", (fid,)).fetchone(): print("já indexado:", nome, flush=True); continue
    for f in TMP.iterdir(): f.unlink()
    t0 = time.time(); code, o, e = rc("backend", "copyid", "gdrive:", fid, str(TMP) + "/", "--tpslimit", "5")
    arqs = list(TMP.glob("*"))
    if code != 0 or not arqs: print("FALHA download:", nome, e[-200:], flush=True); rel.append({"arquivo": nome, "erro": "download"}); continue
    pdf = arqs[0]; t_dl = time.time() - t0
    info = run("pdfinfo", pdf).stdout; m = re.search(r"Pages:\s+(\d+)", info); npag = int(m.group(1)) if m else 0
    t0 = time.time(); txt = run("pdftotext", "-layout", pdf, "-").stdout; t_txt = time.time() - t0
    pags = txt.split("\f")
    chars = sum(len(x.strip()) for x in pags)
    escaneado = npag > 0 and chars / max(npag, 1) < 150
    t_ocr = 0.0
    if escaneado:
        t0 = time.time()
        side = TMP / "ocr.txt"
        r = run("ocrmypdf", "-l", "por", "--force-ocr", "--jobs", "2", "--output-type", "none", "--sidecar", side, pdf, "-", timeout=3 * 3600)
        t_ocr = time.time() - t0
        if side.exists():
            pags = side.read_text(errors="ignore").split("\f"); chars = sum(len(x.strip()) for x in pags)
        else:
            print("OCR falhou:", nome, r.stderr[-300:], flush=True)
    n_idx = 0
    for i, t in enumerate(pags, 1):
        t = re.sub(r"[ \t]+", " ", t).strip()
        if len(t) < 20: continue
        con.execute("insert into paginas(texto, livro, pagina) values (?,?,?)", (t, fid, i)); n_idx += 1
    con.execute("insert or replace into livros values (?,?,?,?,?,?,?,?,?,datetime('now'))", (fid, p["Path"], nome, round(mb(p), 1), npag, int(escaneado), chars, round(t_txt, 1), round(t_ocr, 1)))
    con.commit(); pdf.unlink(missing_ok=True)
    amostra = next((re.sub(r"\s+", " ", t)[:160] for t in pags[len(pags) // 2:] if len(t.strip()) > 200), "")
    r = {"arquivo": nome, "mb": round(mb(p), 1), "paginas": npag, "escaneado": bool(escaneado), "chars": chars, "pag_indexadas": n_idx,
         "seg_download": round(t_dl, 1), "seg_texto": round(t_txt, 1), "seg_ocr": round(t_ocr, 1),
         "seg_por_pag_ocr": round(t_ocr / npag, 2) if escaneado and npag else None, "amostra": amostra}
    rel.append(r); print("LIVRO", json.dumps(r, ensure_ascii=False), flush=True)
    json.dump(rel, open(REL, "w"), ensure_ascii=False, indent=1)

# ---------- busca de teste ----------
con.execute("insert into paginas(paginas) values ('optimize')"); con.commit()
testes = ["sublimação", "pulsão de morte", "objeto transicional", "angustia", "criatividade"]
for q in testes:
    rows = con.execute("select l.arquivo, p.pagina, snippet(paginas, 0, '[', ']', '…', 12) from paginas p join livros l on l.id = p.livro where paginas match ? order by rank limit 3", ('"' + q + '"',)).fetchall()
    print("BUSCA", q, "->", len(rows), flush=True)
    for a, pg, s in rows: print("   ", a[:50], "| p.", pg, "|", re.sub(r"\s+", " ", s)[:140], flush=True)
tot = con.execute("select count(*), sum(paginas), sum(escaneado) from livros").fetchone()
resumo = {"livros": tot[0], "paginas": tot[1], "escaneados": tot[2], "indice_mb": round(DBF.stat().st_size / 1e6, 1), "itens": rel}
json.dump(resumo, open(REL, "w"), ensure_ascii=False, indent=1)
print("RESUMO", json.dumps({k: v for k, v in resumo.items() if k != "itens"}), flush=True)
print("FIM-PILOTO", flush=True)
