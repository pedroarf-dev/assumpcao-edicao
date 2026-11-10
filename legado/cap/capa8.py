# capa "mancha": foto inteira + mancha de tinta amarela translúcida + título recortado
import sys,json,math,random
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance,ImageOps,ImageFont
cfg=json.loads(sys.argv[1]);out=sys.argv[2]
exec(open('capa6.py').read().split("cv=Image.new")[0].split("cfg=json.loads")[0])  # imports only
random.seed(cfg.get('seed',3));np.random.seed(cfg.get('seed',3))
W,H=1080,1920;YEL=(246,196,26)
# reaproveita funções de letra do capa6
src=open('capa6.py').read()
ns={'cfg':cfg,'random':random,'np':np,'Image':Image,'ImageDraw':ImageDraw,'ImageFont':ImageFont,'ImageFilter':ImageFilter,'math':math}
import cv2;ns['cv2']=cv2
for fn in ['def cut','def glyph','def line']:
    i=src.index(fn);j=src.index('\ndef ',i+5) if '\ndef ' in src[i+5:] else len(src)
    exec(src[i:j],ns)
TF=cfg.get('tfont','fx/lilita-one.ttf');ns['TF']=TF
# foto
ph=ImageOps.exif_transpose(Image.open(cfg['photo'])).convert('RGB')
sc=max(W/ph.width,H/ph.height);ph=ph.resize((int(ph.width*sc),int(ph.height*sc)),Image.LANCZOS)
ox=(ph.width-W)//2;oy=int((ph.height-H)*cfg.get('oy',0.5));ph=ph.crop((ox,oy,ox+W,oy+H))
if cfg.get('gray'): ph=ImageEnhance.Contrast(ImageOps.grayscale(ph)).enhance(1.2).convert('RGB')
else: ph=ImageEnhance.Contrast(ph).enhance(1.06)
cv=ph.convert('RGBA')
# mancha: várias pinceladas largas com borda seca
m=Image.new('L',(W,H),0);d=ImageDraw.Draw(m)
cx,cy=cfg.get('mx',520),cfg.get('my',520);ang=math.radians(cfg.get('mang',-10))
for k in range(cfg.get('strokes',5)):
    L=random.uniform(780,1050);th=random.uniform(150,240)
    ox2=random.uniform(-60,60);oy2=(k-2)*random.uniform(95,125)
    pts=[]
    for side in (1,-1):
        seq=[]
        for i in range(31):
            t=i/30;x=-L/2+t*L;taper=math.sin(math.pi*min(1,max(0,t*1.08-0.04)))**0.5
            y=side*th/2*taper+random.uniform(-14,14)
            seq.append((x,y))
        pts+=seq if side==1 else seq[::-1]
    P=[(cx+ox2+x*math.cos(ang)-(y+oy2)*math.sin(ang), cy+x*math.sin(ang)+(y+oy2)*math.cos(ang)) for x,y in pts]
    d.polygon(P,fill=255)
# textura de pincel seco: riscos horizontais na direção do traço
a=np.array(m).astype(float)/255
streak=np.random.rand(H,W);streak=cv2.GaussianBlur(streak,(0,0),sigmaX=40,sigmaY=1.2)
streak=(streak-streak.min())/(streak.max()-streak.min())
M=Image.fromarray((streak*255).astype(np.uint8)).rotate(cfg.get('mang',-10),resample=Image.BICUBIC)
s2=np.array(M).astype(float)/255
edge=cv2.GaussianBlur(a,(0,0),6)
alpha=np.clip(edge*1.6-0.3,0,1)*(0.55+0.45*s2)
alpha=np.where(edge>0.97,np.maximum(alpha,0.78),alpha)*cfg.get('opac',0.88)
lay=Image.new('RGBA',(W,H),YEL+(0,));lay.putalpha(Image.fromarray((alpha*255).astype(np.uint8)))
cv.alpha_composite(lay)
# título
ys=cfg.get('ty',300)
for i,(t,col) in enumerate(cfg['title']):
    g=ns['line'](t,cfg.get('size',170),cfg.get('maxw',800))
    g=g.rotate(cfg.get('mang',-10)*-0.5+random.uniform(-1.5,1.5),resample=Image.BICUBIC,expand=True)
    x=cfg.get('tx',90)+random.randint(-10,25)
    if col=='white':
        sh=Image.new('RGBA',g.size,(18,18,18,255));sh.putalpha(g);cv.alpha_composite(sh,(x+9,ys+9))
        w=Image.new('RGBA',g.size,(252,250,244,255));w.putalpha(g);cv.alpha_composite(w,(x,ys))
    else:
        b=Image.new('RGBA',g.size,(18,18,18,255));b.putalpha(g);cv.alpha_composite(b,(x,ys))
    ys+=g.height+cfg.get('gap',-6)

def add_tag(img,x=60,y=1540,size=50,rot=2.5):
    import random as _r
    from PIL import Image,ImageDraw,ImageFont,ImageFilter
    f=ImageFont.truetype('Anton.ttf',size);t='@assumpcao_pedro'
    w=int(ImageDraw.Draw(img).textlength(t,font=f));W2,H2=w+60,size+46
    def torn(x0,y0,x1,y1,j):
        top=[];xx=x0
        while xx<x1: top.append((xx,y0+_r.uniform(-j,j)));xx+=_r.uniform(6,16)
        top.append((x1,y0+_r.uniform(-j,j)))
        right=[(x1+_r.uniform(-j,j),yy) for yy in (y0+(y1-y0)*k/4 for k in range(1,4))]
        bot=[];xx=x1
        while xx>x0: bot.append((xx,y1+_r.uniform(-j,j)));xx-=_r.uniform(6,16)
        bot.append((x0,y1+_r.uniform(-j,j)))
        left=[(x0+_r.uniform(-j,j),yy) for yy in (y1-(y1-y0)*k/4 for k in range(1,4))]
        return top+right+bot+left
    lay=Image.new('RGBA',(W2+40,H2+40),(0,0,0,0));d=ImageDraw.Draw(lay)
    sh=Image.new('RGBA',lay.size,(0,0,0,0));ImageDraw.Draw(sh).polygon(torn(20,24,W2+20,H2+24,5),fill=(0,0,0,110))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    d.polygon(torn(16,16,W2+24,H2+24,7),fill=(248,246,238,255))
    d.polygon(torn(22,22,W2+18,H2+18,5),fill=(246,196,26,255))
    d.text((48,24),t,font=f,fill=(18,18,18,255))
    lay=lay.rotate(rot,resample=Image.BICUBIC,expand=True)
    base=img.convert('RGBA');base.alpha_composite(lay,(x,y));img.paste(base.convert('RGB'))


if cfg.get('tag',1):
    tmp=cv.convert('RGB');add_tag(tmp,cfg.get('tagx',60),cfg.get('tagy',300));cv=tmp.convert('RGBA')
cv.convert('RGB').save(out,quality=92)
