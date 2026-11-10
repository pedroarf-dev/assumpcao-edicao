import numpy as np, wave, subprocess
sr=48000
def load(f):
    w=wave.open(f); return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
A={'a1':load('a1.wav'),'a2':load('a2.wav')}
def clip(src,t,pre=0.02,dur=0.7):
    x=A[src]; i=int((t-pre)*sr); y=x[i:i+int(dur*sr)].copy()
    n=int(0.01*sr); y[:n]*=np.linspace(0,1,n); m=int(0.15*sr); y[-m:]*=np.linspace(1,0,m)
    return y/ (np.abs(y).max()+1e-9)
def save(y,f):
    y=np.clip(y,-1,1); w=wave.open(f,'w'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((y*32767*0.89).astype(np.int16).tobytes()); w.close()
def mix(parts,total):
    out=np.zeros(int(total*sr))
    for y,t,g in parts:
        i=int(t*sr); n=min(len(y),len(out)-i); out[i:i+n]+=y[:n]*g
    return out/np.abs(out).max()
# catálogo para ouvir: eventos mais fortes/típicos
cat=[('a1',2.13),('a1',20.0),('a1',64.93),('a1',74.07),('a1',75.12),('a1',31.6),('a1',39.25),('a1',84.74),('a2',5.77),('a2',3.75)]
gap=np.zeros(int(0.8*sr)); seq=[]
for s,t in cat: seq+= [clip(s,t,dur=0.9),gap]
save(np.concatenate(seq),'catalogo.wav')
# 3 assinaturas
cafe=mix([(clip('a1',2.13,dur=0.9),0,1.0),(clip('a1',75.12,dur=0.5),0.0,0.35)],1.0)
tum=mix([(clip('a1',75.12,dur=0.5),0,0.8),(clip('a1',75.12,dur=0.6),0.16,1.0)],0.9)
caneta=mix([(clip('a2',5.77,dur=0.3),0,0.6),(clip('a1',74.07,dur=0.8),0.12,1.0)],1.0)
for n,y in [('A-cafe',cafe),('B-tum',tum),('C-caneta',caneta)]: save(y,n+'.wav')
