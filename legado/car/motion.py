import subprocess
from PIL import Image,ImageOps,ImageFilter
W,H=1080,1920;FPS=30
def enc(out,D):
    return subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-f','lavfi','-t',str(D),'-i','anullsrc=r=48000:cl=mono','-map','0:v','-map','1:a','-t',str(D),'-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','pcm_s16le','-ar','48000',out],stdin=subprocess.PIPE)
def ease(u): return u*u*(3-2*u)
def kb(src,z0,z1,dx,dy,u):
    # source-space crop box, smooth sub-pixel
    z=z0+(z1-z0)*u;w,h=W/z,H/z
    cx=W/2+dx*u;cy=H/2+dy*u
    cx=min(max(cx,w/2),W-w/2);cy=min(max(cy,h/2),H-h/2)
    return src.resize((W,H),Image.BICUBIC,box=(cx-w/2,cy-h/2,cx+w/2,cy+h/2))
def trans(prev,art,nxt,out,moves,hold=1.6,f=0.45):
    D=f+hold+f;N=int(round(D*FPS))
    P=Image.open(prev).convert('RGB');A=Image.open(art).convert('RGB');Nx=Image.open(nxt).convert('RGB')
    z0,z1,dx,dy=moves;p=enc(out,D)
    for i in range(N):
        t=i/FPS;u=t/D
        fr=kb(A,z0,z1,dx,dy,u)
        if t<f:
            a=ease(t/f);pz=kb(P,1.0,1.06,0,0,a)   # slide anterior avança enquanto sai
            fr=Image.blend(pz,fr,a)
        elif t>D-f:
            a=ease((t-(D-f))/f);nz=kb(Nx,1.06,1.0,0,0,a)  # próximo slide assenta
            fr=Image.blend(fr,nz,a)
        p.stdin.write(fr.tobytes())
    p.stdin.close();p.wait()
trans('st_0.jpg','gf1.jpg','st_1.jpg','gt1.mov',(1.04,1.16,0,-40))
trans('st_3.jpg','gf2.jpg','st_4.jpg','gt2.mov',(1.16,1.04,30,0))
trans('st_4.jpg','gf3.jpg','st_5.jpg','gt3.mov',(1.04,1.14,0,40))
# fechamento: fundo branco quente, borda branca + sombra suave
D=4.2;N=int(D*FPS);BG=(246,244,238)
art=Image.open('grom/n4.jpg').convert('RGB');art=ImageOps.expand(art,border=int(art.width*0.025),fill=(255,255,255))
prev=Image.open('st_7.jpg').convert('RGB');tag=Image.open('tag.png').convert('RGBA')
s_end=980/art.width;s_start=H*1.15/art.height
fw,fh=int(art.width*s_end),int(art.height*s_end);fy=(H-fh)//2-60
sh=Image.new('L',(W,H),0);sh.paste(255,((W-fw)//2+8,fy+14,(W+fw)//2+8,fy+fh+14));sh=sh.filter(ImageFilter.GaussianBlur(22))
shadow=Image.new('RGB',(W,H),(150,148,142))
p=enc('gt4.mov',D)
for i in range(N):
    t=i/FPS;u=min(1,max(0,(t-0.2)/(D-1.3)));e=1-(1-u)**3;s=s_start*(s_end/s_start)**e
    w,h=int(art.width*s),int(art.height*s);fr=Image.new('RGB',(W,H),BG)
    m=sh.point(lambda v:int(v*0.45*e));fr=Image.composite(shadow,fr,m) if e>0.05 else fr
    fr.paste(art.resize((w,h),Image.BILINEAR if i<N-30 else Image.LANCZOS),((W-w)//2,(H-h)//2-60))
    if t<0.45: fr=Image.blend(prev,fr,ease(t/0.45))
    if t>D-1.2:
        al=min(1,(t-(D-1.2))/0.4);tg=tag.copy();tg.putalpha(tg.split()[3].point(lambda v:int(v*al)))
        fr=fr.convert('RGBA');fr.alpha_composite(tg,((W-tg.width)//2,fy+fh+40));fr=fr.convert('RGB')
    p.stdin.write(fr.tobytes())
p.stdin.close();p.wait()
