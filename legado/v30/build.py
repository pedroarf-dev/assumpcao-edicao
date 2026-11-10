import re,subprocess,json,os
F="/mnt/user-data/uploads/Projetos Claude/Pedro Assumpção/Videos/01 Brutos/2026-10-30 boicote ao proprio pais.mp4"
cues=[]
for l in open('cues.txt'):
    n,a,b,t=l.rstrip('\n').split('|',3);cues.append(dict(n=int(n),a=float(a),b=float(b),t=t))
sil=[]
for l in open('sil.txt'):
    m=re.search(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)',l)
    if m: e,d=float(m.group(1)),float(m.group(2)); sil.append((e-d,e))
BW=[(20.80,23.85),(108.7,113.05),(133.10,135.50),(165.70,168.80)]
DRAMA={17:0.55,42:0.55,38:0.35}   # pausa mantida depois do cue n
POP=[(9,10,'DEMITIR QUEM FEZ O L'),(12,13,'NÃO CONSUMIR DE QUEM VOTOU 13'),(15,17,'COZINHEIROS DO BEM · RS'),(18,18,'ÁGUA DOS GUARANI KAIOWÁ'),(31,32,'DILMA → BICICLETA'),(33,33,'HADDAD → SALA DE AULA')]
# intervalos de fala
iv=[]
for c in cues:
    a=c['a']-0.06;b=c['b']+0.10+DRAMA.get(c['n'],0)
    parts=[(a,b)]
    for s,e in sil:
        if s>a+0.1 and e<c['b']-0.05 and e-s>0.35:
            new=[]
            for x,y in parts:
                if s>x and e<y: new+= [(x,s+0.06),(e-0.06,y)]
                else: new.append((x,y))
            parts=new
    iv+=parts
# split at BW edges
cuts=sorted(set([x for r in BW for x in r]))
segs=[]
for a,b in iv:
    pts=[a]+[c for c in cuts if a<c<b]+[b]
    for x,y in zip(pts,pts[1:]):
        if y-x>0.05: segs.append([x,y])
# merge overlaps
segs.sort();m=[]
for s in segs:
    if m and s[0]<=m[-1][1]+0.001 and not any(abs(s[0]-c)<1e-6 for c in cuts): m[-1][1]=max(m[-1][1],s[1])
    else: m.append(s)
segs=m
isbw=lambda a,b:any(r[0]-0.01<=a and b<=r[1]+0.01 for r in BW)
z=1.0;out=[];t=0;prev=None
for a,b in segs:
    bw=isbw(a,b)
    if prev is not None and (a-prev>0.5): z=1.12 if z==1.0 else 1.0
    out.append(dict(a=a,b=b,bw=bw,z=1.18 if bw else z,ns=t));t+=b-a;prev=b
json.dump(out,open('segs.json','w'));print(len(out),'segs, final',round(t,1),'s')
G="colortemperature=temperature=5800:mix=0.3,eq=contrast=1.08:saturation=1.08:gamma=0.97,unsharp=5:5:0.6,vignette=angle=PI/6"
lst=open('seg/list.txt','w')
for i,s in enumerate(out):
    zz=s['z'];v=G+(",hue=s=0,eq=contrast=1.18" if s['bw'] else "")+f",crop=trunc(iw/{zz}/2)*2:trunc(ih/{zz}/2)*2:(iw-iw/{zz})/2:(ih-ih/{zz})*0.35,scale=1080:1920:flags=lanczos,fps=30,setsar=1"
    d=s['b']-s['a'];af=f"afade=t=in:d=0.012,afade=t=out:st={max(0,d-0.015):.3f}:d=0.015"
    if s['bw']: af="highpass=f=180,aecho=0.8:0.55:70|140:0.35|0.2,"+af
    fn=f"seg/s{i:03d}.mp4"
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f"{s['a']:.3f}",'-i',F,'-t',f"{d:.3f}",'-vf',v,'-af',af,'-c:v','libx264','-preset','veryfast','-crf','17','-c:a','pcm_s16le','-ar','48000','-ac','1',fn.replace('.mp4','.mov')],check=True)
    lst.write(f"file 's{i:03d}.mov'\n")
lst.close()
# legenda + pop-ups no tempo novo
def mapt(x):
    for s in out:
        if s['a']-0.001<=x<=s['b']+0.001: return s['ns']+x-s['a']
    return None
def f(x):h=int(x//3600);mm=int(x%3600//60);ss=x%60;return f"{h}:{mm:02d}:{ss:05.2f}"
Y='{\\c&H0018C5F5&}';W='{\\c&H00FFFFFF&}'
L=["[Script Info]","ScriptType: v4.00+","PlayResX: 720","PlayResY: 1280","WrapStyle: 0","","[V4+ Styles]",
"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
"Style: K,Lato Black,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,5,2,2,60,60,360,1",
"Style: T,Lilita One,46,&H00F4FAFC,&H00FFFFFF,&H00121212,&H00121212,0,0,0,0,100,100,1,-2,3,12,0,8,50,50,250,1","","[Events]",
"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
cm={c['n']:c for c in cues}
for c in cues:
    ws=c['t'].split();tot=sum(len(w)+1 for w in ws);cur=c['a'];tm=[]
    for w in ws: d=(c['b']-c['a'])*(len(w)+1)/tot;tm.append((cur,cur+d));cur+=d
    for i in range(0,len(ws),4):
        ch=ws[i:i+4]
        for j,w in enumerate(ch):
            s,e=tm[i+j];ns,ne=mapt(s+0.02),mapt(e-0.02)
            if ns is None or ne is None or ne<=ns: 
                ns=mapt(s) or mapt(e)
                if ns is None: continue
                ne=ns+0.15
            txt=' '.join((Y+x+W) if k==j else x for k,x in enumerate(ch))
            L.append(f"Dialogue: 0,{f(ns)},{f(ne)},K,,0,0,0,,{txt}")
for a,b,txt in POP:
    s=mapt(cm[a]['a']);e=mapt(cm[b]['b'])
    L.append(f"Dialogue: 1,{f(s)},{f(e)},T,,0,0,0,,{{\\fad(120,120)\\frz-2}}{txt}")
open('k30.ass','w').write('\n'.join(L)+'\n')
