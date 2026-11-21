import json, os, re, glob, time, html, subprocess, urllib.request, urllib.parse, urllib.error
from datetime import datetime
import docker
from fastapi import FastAPI, Body
app = FastAPI()
TMP = '/dados/estudo'
PASTA = os.environ.get('PASTA', '05 Estudo')
UA = {'User-Agent': 'Mozilla/5.0 (assumpcao-estudo; uso pessoal)'}
TOK = 'export RCLONE_CONFIG_GDRIVE_TOKEN="{\\"access_token\\":\\"\\",\\"token_type\\":\\"Bearer\\",\\"refresh_token\\":\\"__R__GDRIVE_REFRESH\\",\\"expiry\\":\\"2000-01-01T00:00:00Z\\"}"; exec rclone "__R__@"'.replace('__R__', chr(36))
INSTR = ('Fale em português do Brasil. Use SOMENTE o que está nas fontes. Não invente dados, autores, exemplos ou conclusões que não estejam no texto; '
         'se algo não estiver nas fontes, diga que o texto não trata disso. Diferencie o que o estudo mostra do que é interpretação. Explique o método e os limites do estudo. '
         'No fim, levante 3 perguntas abertas que o tema provoca, sem dar resposta pronta. Tom de conversa, sem exagero e sem frases motivacionais.')

def rclone(*args):
    sync = docker.from_env().containers.get('assumpcao-sync')
    r = sync.exec_run(['sh', '-c', TOK, 'sh', *args], demux=True)
    out = (r.output[0] or b'').decode(errors='replace'); err = (r.output[1] or b'').decode(errors='replace')
    return r.exit_code, out, err

def get_json(url):
    for k in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(4 * (k + 1))
        except Exception:
            time.sleep(4 * (k + 1))
    return None

def abstract_de(w):
    ii = (w or {}).get('abstract_inverted_index') or {}; a = {}
    for k, v in ii.items():
        for i in v: a[i] = k
    return ' '.join(a[i] for i in sorted(a))

def openalex(art):
    oid = art.get('obra_id') or ''
    m = re.search(r'(W\d+)', oid)
    if m: return get_json('https://api.openalex.org/works/' + m.group(1))
    doi = art.get('doi') or ''
    link = art.get('link') or ''
    if not doi and 'doi.org/' in link: doi = link.split('doi.org/', 1)[1]
    doi = doi.replace('https://doi.org/', '').strip()
    if doi: return get_json('https://api.openalex.org/works/doi:' + urllib.parse.quote(doi))
    return None

def pdf_urls(w, art):
    us = []
    if w:
        b = w.get('best_oa_location') or {}
        us += [b.get('pdf_url')]
        us += [l.get('pdf_url') for l in (w.get('locations') or [])]
        us += [(w.get('open_access') or {}).get('oa_url')]
    l = art.get('link') or ''
    if l.lower().endswith('.pdf'): us.append(l)
    vis = []
    for u in us:
        if u and u not in vis: vis.append(u)
    return vis

def baixar_texto(urls):
    os.makedirs(TMP, exist_ok=True)
    for u in urls:
        f = TMP + '/a.pdf'
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                data = r.read(40 * 1024 * 1024 + 1)
            if len(data) > 40 * 1024 * 1024 or not data.startswith(b'%PDF'): continue
            open(f, 'wb').write(data)
            t = subprocess.run(['pdftotext', '-enc', 'UTF-8', f, '-'], capture_output=True, timeout=120).stdout.decode('utf-8', 'replace')
            if len(t.strip()) > 1500: return t, u
        except Exception:
            continue
        finally:
            if os.path.exists(f): os.remove(f)
    return None, None

def paragrafos(t, limite=150000):
    t = t.replace('\r', '').replace('\x0c', '\n\n')[:limite]
    t = re.sub(r'-\n(?=[a-zà-ú])', '', t)
    blocos = [re.sub(r'\s*\n\s*', ' ', b).strip() for b in re.split(r'\n\s*\n', t)]
    return ''.join('<p>%s</p>' % html.escape(b) for b in blocos if len(b) > 2)

def esc(x): return html.escape(str(x)) if x not in (None, '') else ''

ROTULOS = [('origem', 'Origem'), ('achado', 'Achado'), ('cena', 'Cena'), ('pergunta', 'Pergunta'), ('texto', 'Texto da ideia'), ('leitura', 'Leitura'),
           ('encaixe', 'Onde encaixa'), ('o_que_diz', 'O que diz'), ('ligacao', 'Ligação'), ('trecho', 'Você disse'), ('confirma', 'Confirma'),
           ('complica', 'Complica'), ('frase', 'Frase que pode entrar'), ('cuidado', 'Cuidado'), ('ideia', 'A ideia, simples'), ('exemplo', 'Exemplo para falar'),
           ('cuidados', 'Cuidados'), ('cena_pauta', 'Cena'), ('link', 'Link de origem')]

@app.get('/saude')
def saude():
    c, o, e = rclone('lsf', 'gdrive:', '--dirs-only', '--max-depth', '1')
    return {'ok': c == 0, 'pastas': o.split('\n')[:20], 'erro': e[:200]}

@app.post('/estudo')
def estudo(p: dict = Body(...)):
    ini = time.time()
    titulo = (p.get('titulo') or 'Sem título').strip()
    nome = 'Base – ' + re.sub(r'[\\/:*?"<>|\n]+', ' ', titulo)[:90].strip()
    arts = p.get('artigos') or []
    base = p.get('base') or {}
    partes = ['<html><head><meta charset="utf-8"></head><body>',
              '<h1>%s</h1>' % esc(nome),
              '<p><b>Instrução para colar no NotebookLM:</b></p><p style="background:#FFF4C4;padding:8px">%s</p>' % esc(INSTR),
              '<p><i>Gerado em %s · %d fonte(s)</i></p>' % (datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC'), len(arts))]
    res = []
    for n, a in enumerate(arts, 1):
        w = openalex(a)
        tit = a.get('titulo') or (w or {}).get('title') or 'Artigo'
        autores = a.get('autores') or ', '.join(x['author']['display_name'] for x in (w or {}).get('authorships', [])[:4] if x.get('author'))
        ano = a.get('ano') or (w or {}).get('publication_year') or 's/d'
        doi = a.get('doi') or (w or {}).get('doi') or ''
        link = a.get('link') or a.get('url') or doi or ''
        texto, fonte_pdf = baixar_texto(pdf_urls(w, a))
        resumo = a.get('resumo') or abstract_de(w)
        partes.append('<h2>Fonte %d · %s</h2>' % (n, esc(tit)))
        partes.append('<p><b>Autores:</b> %s<br><b>Ano:</b> %s<br><b>Link:</b> %s<br><b>DOI:</b> %s</p>' % (esc(autores), esc(ano), esc(link), esc(doi) or '—'))
        if texto:
            partes.append('<p><i>Texto completo (acesso aberto: %s)</i></p>' % esc(fonte_pdf))
            partes.append(paragrafos(texto))
        else:
            partes.append('<p><b>⚠️ Só o resumo — o áudio vai ficar raso.</b></p>')
            partes.append('<p>%s</p>' % (esc(resumo) or '(sem resumo disponível)'))
        res.append({'titulo': tit, 'completo': bool(texto)})
    if not arts:
        partes.append('<p><b>⚠️ Sem artigo ligado ainda — só a base abaixo.</b></p>')
    linhas = ['<li><b>%s:</b> %s</li>' % (r, esc(base[k])) for k, r in ROTULOS if base.get(k)]
    fontes = base.get('fontes') or []
    if linhas or fontes:
        partes.append('<h2>Base (pauta, pílula ou ideia)</h2><ul>%s</ul>' % ''.join(linhas))
        if fontes:
            partes.append('<p><b>Fontes citadas:</b></p><ul>%s</ul>' % ''.join('<li>%s %s</li>' % (esc(f.get('titulo')), esc(f.get('url'))) for f in fontes))
    partes.append('</body></html>')
    os.makedirs(TMP, exist_ok=True)
    arq = '%s/pedido-%s.html' % (TMP, p.get('id', int(time.time())))
    open(arq, 'w', encoding='utf-8').write(''.join(partes))
    try:
        c, o, e = rclone('copyto', arq, 'gdrive:%s/%s.html' % (PASTA, nome), '--drive-import-formats', 'html', '--drive-export-formats', 'html', '--log-level', 'ERROR')
        if c != 0: return {'ok': False, 'erro': 'upload falhou: ' + e[:300]}
        c, o, e = rclone('lsjson', 'gdrive:' + PASTA, '--files-only', '--no-modtime', '--drive-export-formats', 'html')
        lst = json.loads(o or '[]')
        cand = [x for x in lst if x.get('Name', '').rsplit('.', 1)[0] == nome or x.get('Name') == nome or x.get('Name') in (nome + '.docx', nome + '.html')]
        if not cand: return {'ok': False, 'erro': 'Doc não encontrado depois do upload', 'nomes': [x.get('Name') for x in lst][:20]}
        did = cand[-1]['ID']
        return {'ok': True, 'link': 'https://docs.google.com/document/d/%s/edit' % did, 'nome': nome, 'artigos': res, 'segundos': round(time.time() - ini, 1)}
    finally:
        if os.path.exists(arq): os.remove(arq)
