import re,subprocess,json,random
SRC={'p1':'p1.mp4','p2':'p2.mp4'};SIL={'p1':'sil1.txt','p2':'sil2.txt'}
cues=[]
for l in open('cues.txt'):
    s,n,a,b,t=l.rstrip('\n').split('|',4);cues.append(dict(s=s,n=int(n),a=float(a),b=float(b),t=t))
sil={}
for k,f in SIL.items():
    sil[k]=[]
    for l in open(f):
        m=re.search(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)',l)
        if m:e,d=float(m.group(1)),float(m.group(2));sil[k].append((e-d,e))
BW={('p1',19)}
EXTRA={('p1',18):0.35,('p2',24):1.2}   # pausa dramática / gole final
segs=[]
for c in cues:
    a=c['a']-0.07;b=c['b']+0.12+EXTRA.get((c['s'],c['n']),0)
    parts=[(a,b)]
    for s,e in sil[c['s']]:
        if s>a+0.1 and e<c['b']-0.05 and e-s>0.45:
            new=[]
            for x,y in parts:
                if s>x and e<y:new+=[(x,s+0.08),(e-0.08,y)]
                else:new.append((x,y))
            parts=new
    for x,y in parts: segs.append(dict(src=c['s'],a=x,b=y,bw=(c['s'],c['n']) in BW,n=c['n']))
# merge contíguos da mesma fonte e mesmo bw
m=[]
for s in segs:
    if m and m[-1]['src']==s['src'] and m[-1]['bw']==s['bw'] and s['a']<=m[-1]['b']+0.001: m[-1]['b']=max(m[-1]['b'],s['b'])
    else:m.append(s)
z=1.0;t=0;prev=None
for s in m:
    if prev and (s['src']!=prev['src'] or s['a']-prev['b']>0.5): z=1.1 if z==1.0 else 1.0
    s['z']=1.2 if s['bw'] else z;s['ns']=t;t+=s['b']-s['a'];prev=s
json.dump(m,open('segs.json','w'));print(len(m),'segs',round(t,1),'s')
G="hqdn3d=2:2:4:4,colortemperature=temperature=4800:mix=0.6,eq=contrast=1.18:saturation=1.06:gamma=0.98,vignette=angle=PI/6"
lst=open('seg/list.txt','w')
for i,s in enumerate(m):
    zz=s['z'];v=G+(",hue=s=0,eq=contrast=1.18" if s['bw'] else "")+f",crop=trunc(iw/{zz}/2)*2:trunc(ih/{zz}/2)*2:(iw-iw/{zz})/2:(ih-ih/{zz})*0.35,scale=1080:1920:flags=lanczos,fps=30,setsar=1"
    d=s['b']-s['a'];af=("highpass=f=180,aecho=0.8:0.55:70|140:0.35|0.2," if s['bw'] else "")+f"afade=t=in:d=0.012,afade=t=out:st={max(0,d-0.015):.3f}:d=0.015"
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f"{max(0,s['a']):.3f}",'-i',SRC[s['src']],'-t',f"{d:.3f}",'-vf',v,'-af',af,'-c:v','libx264','-preset','veryfast','-crf','17','-c:a','pcm_s16le','-ar','48000','-ac','1',f"seg/s{i:03d}.mov"],check=True)
    lst.write(f"file 's{i:03d}.mov'\n")
lst.close()
def mapt(src,x):
    for s in m:
        if s['src']==src and s['a']-0.001<=x<=s['b']+0.001:return s['ns']+x-s['a']
def f(x):h=int(x//3600);mm=int(x%3600//60);ss=x%60;return f"{h}:{mm:02d}:{ss:05.2f}"
Y='{\\c&H0018C5F5&}';W='{\\c&H00FFFFFF&}'
L=["[Script Info]","ScriptType: v4.00+","PlayResX: 720","PlayResY: 1280","WrapStyle: 0","","[V4+ Styles]",
"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
"Style: K,Lato Black,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,5,2,2,60,60,360,1","","[Events]",
"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for c in cues:
    ws=c['t'].split();tot=sum(len(w)+1 for w in ws);cur=c['a'];tm=[]
    for w in ws:d=(c['b']-c['a'])*(len(w)+1)/tot;tm.append((cur,cur+d));cur+=d
    for i in range(0,len(ws),4):
        ch=ws[i:i+4]
        for j,w in enumerate(ch):
            s,e=tm[i+j];ns,ne=mapt(c['s'],s+0.02),mapt(c['s'],e-0.02)
            if ns is None or ne is None or ne<=ns:
                ns=mapt(c['s'],s) or mapt(c['s'],e)
                if ns is None:continue
                ne=ns+0.15
            L.append(f"Dialogue: 0,{f(ns)},{f(ne)},K,,0,0,0,,"+' '.join((Y+x+W) if k==j else x for k,x in enumerate(ch)))
ev=[]
for l in L:
    if l.startswith('Dialogue:'):
        p=l.split(',',9);ev.append([p[1],p[2],l])
def sec(t):h,m,x=t.split(':');return int(h)*3600+int(m)*60+float(x)
ev.sort(key=lambda e:sec(e[0]))
for i in range(len(ev)-1):
    a,b=sec(ev[i][1]),sec(ev[i+1][0])
    if 0<b-a<0.4 or b<a: ev[i][1]=ev[i+1][0]
out=[l for l in L if not l.startswith('Dialogue:')]
for st,en,l in ev:
    p=l.split(',',9);p[1]=st;p[2]=en;out.append(','.join(p))
open('k.ass','w').write('\n'.join(out)+'\n')
