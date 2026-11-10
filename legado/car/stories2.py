import subprocess
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter
W,H=1080,1920;FPS=30
F='../cap/PermanentMarker.ttf'
def tape(lines,size=54,rot=-2):
    f=ImageFont.truetype(F,size);pad=28
    ws=[f.getbbox(l)[2] for l in lines];lh=int(size*1.35)
    im=Image.new('RGBA',(max(ws)+pad*2,lh*len(lines)+pad),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rectangle((0,0,im.width,im.height),fill=(20,20,20,240))
    for i,l in enumerate(lines): d.text((pad,pad//2+i*lh),l,font=f,fill=(246,196,26))
    return im.rotate(rot,expand=True,resample=Image.BICUBIC)
def enc(out,D):
    return subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i','pad2.wav','-map','0:v','-map','1:a','-t',str(D),'-af',f'afade=t=in:d=0.5,afade=t=out:st={D-1}:d=1,volume=0.8','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',out],stdin=subprocess.PIPE)
def ease(u): return u*u*(3-2*u)
# Story 1: as pinturas (3 gromelôs em sequência, movimento lento)
arts=['gf1.jpg','gf2.jpg','gf3.jpg'];seg=2.6;f=0.5;D=seg*3+0.4
T=tape(['as pinturas do vídeo','são minhas 🎨'.replace(' 🎨','')],56,-2);T2=tape(['série gromelô visual'],44,1.5)
imgs=[Image.open(a).convert('RGB') for a in arts]
def kb(src,z):
    w,h=W/z,H/z;return src.resize((W,H),Image.BICUBIC,box=((W-w)/2,(H-h)/2,(W+w)/2,(H+h)/2))
p=enc('story-grom-1.mp4',D)
for i in range(int(D*FPS)):
    t=i/FPS;k=min(2,int(t//seg));u=(t-k*seg)/seg
    fr=kb(imgs[k],1.03+0.08*u)
    if k<2 and t>(k+1)*seg-f:
        a=ease((t-((k+1)*seg-f))/f);fr=Image.blend(fr,kb(imgs[k+1],1.03),a)
    fr=fr.convert('RGBA');fr.alpha_composite(T,((W-T.width)//2,230));fr.alpha_composite(T2,((W-T2.width)//2,230+T.height+20));p.stdin.write(fr.convert('RGB').tobytes())
p.stdin.close();p.wait()
# Story 2: bicicleta inteira em fundo branco + pergunta
BG=(246,244,238);art=Image.open('grom/n4.jpg').convert('RGB');art=ImageOps.expand(art,border=int(art.width*0.025),fill=(255,255,255))
s1=980/art.width;s0=s1*1.25;D=6.0
T=tape(['política, arte, psicanálise','ou sociedade:'],50,-1.5);Q=tape(['qual te move mais? 👇'.replace(' 👇','')],60,2)
p=enc('story-grom-2.mp4',D)
for i in range(int(D*FPS)):
    t=i/FPS;e=1-(1-min(1,t/3.5))**3;s=s0+(s1-s0)*e
    w,h=int(art.width*s),int(art.height*s);fr=Image.new('RGB',(W,H),BG)
    fr.paste(art.resize((w,h),Image.BILINEAR),((W-w)//2,(H-h)//2));fr=fr.convert('RGBA')
    fr.alpha_composite(T,((W-T.width)//2,300));fr.alpha_composite(Q,((W-Q.width)//2,1420))
    p.stdin.write(fr.convert('RGB').tobytes())
p.stdin.close();p.wait()
