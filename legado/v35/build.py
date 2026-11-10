import re,subprocess,json,random,importlib.util
F='raw.mp4'
cues=[]
for l in open('cues.txt'):
    n,a,b,t=l.rstrip('\n').split('|',3);cues.append(dict(n=int(n),a=float(a),b=float(b),t=t))
sil=[]
for l in open('sil.txt'):
    m=re.search(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)',l)
    if m: e,d=float(m.group(1)),float(m.group(2)); sil.append((e-d,e))
BW=[]
BLEEP=(-5,-4)
DRAMA={14:0.35,18:0.4,25:0.3}
iv=[]
for c in cues:
    a=c['a']-0.07;b=c['b']+0.12+DRAMA.get(c['n'],0);parts=[(a,b)]
    for s,e in sil:
        if s>a+0.1 and e<c['b']-0.05 and e-s>0.6:
            new=[]
            for x,y in parts:
                if s>x and e<y:new+=[(x,s+0.08),(e-0.08,y)]
                else:new.append((x,y))
            parts=new
    iv+=parts
cuts=[]
segs=[]
for a,b in iv:
    pts=[a]+[c for c in cuts if a<c<b]+[b]
    for x,y in zip(pts,pts[1:]):
        if y-x>0.04:segs.append([x,y])
segs.sort();m=[]
for s in segs:
    if m and s[0]<=m[-1][1]+0.001 and not any(abs(s[0]-c)<1e-6 for c in cuts):m[-1][1]=max(m[-1][1],s[1])
    else:m.append(s)
segs=m
inr=lambda a,b,R:R[0]-0.01<=a and b<=R[1]+0.01
z=1.0;out=[];t=0;prev=None
for a,b in segs:
    bw=any(inr(a,b,r) for r in BW);bl=inr(a,b,BLEEP)
    if prev is not None and a-prev>0.5: z=1.1 if z==1.0 else 1.0
    out.append(dict(a=a,b=b,bw=bw,bl=bl,z=1.2 if bw else z,ns=t));t+=b-a;prev=b
json.dump(out,open('segs.json','w'));print(len(out),'segs',round(t,1),'s')
G="hqdn3d=1.5:1.5:3:3,colortemperature=temperature=5000:mix=0.5,eq=contrast=1.12:saturation=1.05:gamma=1.08"
lst=open('seg/list.txt','w')
for i,s in enumerate(out):
    zz=s['z'];v=G+(",hue=s=0,eq=contrast=1.2" if s['bw'] else "")+f",crop=trunc(iw/{zz}/2)*2:trunc(ih/{zz}/2)*2:(iw-iw/{zz})/2:(ih-ih/{zz})*0.3,scale=1080:1920:flags=lanczos,fps=30,setsar=1"
    d=s['b']-s['a'];fade=f"afade=t=in:d=0.012,afade=t=out:st={max(0,d-0.015):.3f}:d=0.015"
    fn=f"seg/s{i:03d}.mov"
    if s['bl']:
        cmd=['ffmpeg','-v','error','-y','-ss',f"{s['a']:.3f}",'-i',F,'-f','lavfi','-i',f"sine=frequency=1000:sample_rate=48000:duration={d:.3f}",'-t',f"{d:.3f}",'-vf',v,'-filter_complex',f"[1:a]volume=0.25,{fade}[aa]",'-map','0:v','-map','[aa]','-c:v','libx264','-preset','veryfast','-crf','17','-c:a','pcm_s16le','-ar','48000','-ac','1',fn]
    else:
        af=("highpass=f=180,aecho=0.8:0.55:70|140:0.35|0.2," if s['bw'] else "")+fade
        cmd=['ffmpeg','-v','error','-y','-ss',f"{s['a']:.3f}",'-i',F,'-t',f"{d:.3f}",'-vf',v,'-af',af,'-c:v','libx264','-preset','veryfast','-crf','17','-c:a','pcm_s16le','-ar','48000','-ac','1',fn]
    subprocess.run(cmd,check=True);lst.write(f"file 's{i:03d}.mov'\n")
lst.close()
def mapt(x):
    for s in out:
        if s['a']-0.001<=x<=s['b']+0.001:return s['ns']+x-s['a']
    return None
spec=importlib.util.spec_from_file_location('p','postit.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
random.seed(7);chunks=[]
for c in cues:
    ws=c['t'].lower().split();tot=sum(len(w)+1 for w in ws);cur=c['a'];tm=[]
    for w in ws:d=(c['b']-c['a'])*(len(w)+1)/tot;tm.append((cur,cur+d));cur+=d
    i=0
    while i<len(ws):
        n=3
        for k in range(1,4):
            if i+k<=len(ws) and ws[i+k-1][-1] in ',.?!': n=k;break
        n=min(n,len(ws)-i);s=mapt(tm[i][0]+0.01) or mapt(tm[i][1]-0.01);e=mapt(tm[i+n-1][1]-0.01) or mapt(tm[i+n-1][0]+0.01)
        if s is not None and e is not None and e>s:chunks.append((s,e,[w.strip(',.') if w not in ('&%$#?',) else w for w in ws[i:i+n]]))
        i+=n
open('post.ass','w').write(p.HEAD+'\n'.join(p.events(chunks,y=940))+'\n')
