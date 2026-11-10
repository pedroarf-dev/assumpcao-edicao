import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OR=(232,112,52); INK=(40,40,44); S=4
F=ImageFont.truetype('/tmp/fnt/fontsource-fraunces-5.3.0/files/fraunces-latin-300-normal.woff',40)
def dens(pts,step):
    out=[]
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        n=max(2,int(math.hypot(x1-x0,y1-y0)/step)); out+=[(x0+(x1-x0)*i/n,y0+(y1-y0)*i/n) for i in range(n)]
    return out+[pts[-1]]
def L(d,pts,w,seed,amp):
    random.seed(seed); p=dens(pts,amp*0.25); ph=random.uniform(0,6); ph2=random.uniform(0,6); n=len(p)
    q=[(x+amp*0.3*math.sin(i*0.05+ph), y+amp*0.3*math.cos(i*0.04+ph2)) for i,(x,y) in enumerate(p)]
    for i in range(len(q)-1):
        t=i/max(1,n-2); taper=min(1,t*6,(1-t)*6); ww=max(1,int(w*(0.5+0.5*taper)))
        d.line([q[i],q[i+1]],fill=OR,width=ww); d.ellipse((q[i][0]-ww/2,q[i][1]-ww/2,q[i][0]+ww/2,q[i][1]+ww/2),fill=OR)
def arc(cx,cy,rx,ry,a0,a1,n=50): return [(cx+rx*math.cos(math.radians(a0+(a1-a0)*i/n)),cy+ry*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)]
def lampada(d,cx,cy,r,w,a):
    by=cy-r*.1
    L(d,arc(cx,by,r*.55,r*.6,135,405),w,1,a)                       # bulbo
    L(d,[(cx-r*.38,by+r*.43),(cx-r*.3,by+r*.75)],w,2,a); L(d,[(cx+r*.38,by+r*.43),(cx+r*.3,by+r*.75)],w,3,a)
    L(d,[(cx-r*.32,by+r*.78),(cx+r*.32,by+r*.78)],w,4,a); L(d,[(cx-r*.24,by+r*.92),(cx+r*.24,by+r*.92)],w,5,a)
    L(d,arc(cx,by+r*.05,r*.11,r*.2,200,520,30),w,6,a)               # filamento em gota
    L(d,[(cx,by+r*.25),(cx,by+r*.75)],w,7,a)
    for k,an in enumerate((-160,-125,-90,-55,-20)):                 # raios
        ra=math.radians(an); L(d,[(cx+math.cos(ra)*r*.78,by+math.sin(ra)*r*.82),(cx+math.cos(ra)*r*1.02,by+math.sin(ra)*r*1.06)],w,10+k,a)
def barco(d,cx,cy,r,w,a):
    lt,rt=(cx-r*1.05,cy+r*.05),(cx+r*1.05,cy-r*.02); bl,br=(cx-r*.55,cy+r*.72),(cx+r*.55,cy+r*.72); c=(cx,cy+r*.32)
    L(d,[lt,rt],w,30,a); L(d,[lt,bl,br,rt],w,31,a)
    L(d,[lt,c,rt],w,32,a); L(d,[bl,c,br],w,33,a)
    ap=(cx,cy-r*.95); L(d,[(cx-r*.42,cy+r*.03),ap,(cx+r*.42,cy+r*.0)],w,34,a); L(d,[ap,c],w,35,a)
def flor_real(size):
    m=Image.open('m_flor_clean.png').convert('L'); m=m.crop(m.getbbox())
    m=m.filter(ImageFilter.GaussianBlur(1.2)).point(lambda v:255 if v>110 else 0)
    k=size/max(m.size); m=m.resize((int(m.width*k),int(m.height*k)),Image.LANCZOS)
    lay=Image.new('RGBA',m.size,OR+(0,)); lay.putalpha(m); return lay
W=1200; im=Image.new('RGB',(W*S,520*S),(250,249,246)); d=ImageDraw.Draw(im)
lampada(d,200*S,190*S,100*S,6*S,9*S); barco(d,1000*S,190*S,100*S,6*S,9*S)
im=im.resize((W,520),Image.LANCZOS); fl=flor_real(230); im.paste(fl,(600-fl.width//2,190-fl.height//2-5),fl)
d=ImageDraw.Draw(im)
for i,k in enumerate(['pensamento','arte','sociedade']):
    tw=d.textlength(k,font=F); d.text((200+i*400-tw/2,380),k,font=F,fill=INK)
im.save('marcas5.jpg',quality=92)
c=Image.open('capa3.jpg'); d=ImageDraw.Draw(c); d.rectangle((960,1580,1050,1660),fill=c.getpixel((900,1600)))
out=[]
for k in ['pensamento','arte','sociedade']:
    cc=c.copy()
    if k=='arte': lay=flor_real(80); cc.paste(lay,(990-lay.width//2,1610-lay.height//2),lay); lay.save('marca-arte.png')
    else:
        lay=Image.new('RGBA',(160*S,160*S),(0,0,0,0)); (lampada if k=='pensamento' else barco)(ImageDraw.Draw(lay),80*S,80*S,34*S,2.4*S,3*S)
        lay=lay.resize((160,160),Image.LANCZOS); lay.save(f'marca-{k}.png'); cc.paste(lay,(910,1530),lay)
    out.append(cc.crop((0,240,1080,1680)).resize((360,480)))
row=Image.new('RGB',(3*370,480),(255,255,255))
for i,o in enumerate(out): row.paste(o,(i*375,0))
row.save('marcas5-capa.jpg',quality=88)
