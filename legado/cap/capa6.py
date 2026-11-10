import sys,os,math,random,json
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter
cfg=json.loads(sys.argv[1]); out=sys.argv[2]
random.seed(cfg.get('seed',3)); np.random.seed(cfg.get('seed',3))
W,H=1080,1920
BG=tuple(cfg.get('bg',[246,196,26]))
TF=cfg.get('tfont','fx/titan-one.ttf'); SF=cfg.get('sfont','fx/gochi-hand.ttf')
def cut(mask,eps=0.012,jit=0.006):
    a=np.array(mask); cs,hier=cv2.findContours((a>110).astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
    o=np.zeros_like(a); s=max(a.shape)
    if hier is None: return mask
    for i,c in enumerate(cs):
        p=cv2.approxPolyDP(c,eps*cv2.arcLength(c,True)/4+1.2,True).astype(np.float32)
        p+=np.random.uniform(-jit*s,jit*s,p.shape).astype(np.float32)
        cv2.fillPoly(o,[p.astype(np.int32)],255 if hier[0][i][3]<0 else 0)
    return Image.fromarray(o)
def glyph(ch,size):
    f=ImageFont.truetype(TF,size); pad=size
    im=Image.new('L',(size*2+pad,size*2+pad),0); d=ImageDraw.Draw(im)
    d.text((pad//2,pad//2),ch,font=f,fill=255)
    bb=im.getbbox()
    if not bb: return None,f.getlength(ch)
    g=im.crop(bb)
    g=g.resize((int(g.width*random.uniform(.92,1.04)*cfg.get('sx',.92)),int(g.height*random.uniform(.95,1.07)*cfg.get('sy',1.12))),Image.LANCZOS)
    g=g.rotate(random.uniform(-5,5),resample=Image.BICUBIC,expand=True)
    g=cut(g)
    return g,f.getlength(ch)
def line(text,size,maxw,taper=0.08):
    S=size; canvas=Image.new('L',(int(S*len(text)*1.3)+S,int(S*2)),0)
    x=S//4; base=int(S*1.4); n=len(text)
    for i,ch in enumerate(text):
        k=1+taper*(i/(max(n-1,1))-.5)  # cresce da esquerda pra direita
        s=int(S*k*random.uniform(.9,1.1))
        g,adv=glyph(ch,s)
        if g is not None:
            y=base-g.height+int(random.uniform(-.05,.05)*S)
            canvas.paste(255,(int(x),y),g)
            x+=g.width*random.uniform(cfg.get('ov0',.93),cfg.get('ov1',1.0))   # leve sobreposição
        else: x+=adv*.8
    canvas=canvas.crop(canvas.getbbox())
    sc=min(maxw/canvas.width, cfg.get('maxh',330)/canvas.height)
    canvas=canvas.resize((int(canvas.width*sc),int(canvas.height*sc)),Image.LANCZOS)
    return canvas
def stroke(w,h,thick):
    im=Image.new('L',(w+40,h+thick*2+40),0); d=ImageDraw.Draw(im)
    top=[];bot=[]
    for i in range(41):
        t=i/40; x=20+t*w; y=20+thick+ (1-t)*h + random.uniform(-2,2)
        th=thick*(0.55+0.45*math.sin(math.pi*min(1,t*1.15)))
        top.append((x,y-th/2)); bot.append((x,y+th/2+random.uniform(-1.5,1.5)))
    d.polygon(top+bot[::-1],fill=255); return cut(im,eps=.004,jit=.002)
cv=Image.new('RGB',(W,H),BG)
def put(mask,color,x,y,shadow=None):
    if shadow:
        sh=Image.new('RGB',mask.size,shadow); cv.paste(sh,(x+shadow_off,y+shadow_off),mask)
    lay=Image.new('RGB',mask.size,color); cv.paste(lay,(x,y),mask)
shadow_off=cfg.get('shoff',12)
# bloco do título
lines=cfg['title']; maxw=cfg.get('maxw',900)
blocks=[line(t,cfg.get('size',230),maxw) for t in lines]
gap=cfg.get('gap',-8)
bw=max(b.width for b in blocks)+80; bh=sum(b.height for b in blocks)+gap*(len(blocks)-1)+60
blk=Image.new('L',(bw,bh),0); y=30
for b in blocks:
    blk.paste(255,((bw-b.width)//2+random.randint(-14,14),y),b); y+=b.height+gap
blk=blk.rotate(cfg.get('tilt',4),resample=Image.BICUBIC,expand=True)
blk=blk.crop(blk.getbbox())
Y0=cfg.get('y0',430)
bx=(W-blk.width)//2
put(blk,tuple(cfg['tcolor']),bx,Y0,tuple(cfg['shadow']) if cfg.get('shadow') else None)
Y=Y0+blk.height-10
# sublinhado de pincel
if cfg.get('ucolor'):
    st=stroke(int(blk.width*.72),int(blk.width*.07),46)
    put(st,tuple(cfg['ucolor']),bx+int(blk.width*.2),Y); Y+=st.height+60
# subtítulo manuscrito
f=ImageFont.truetype(SF,cfg.get('ssize',88))
sub=Image.new('L',(W*2,600),0); d=ImageDraw.Draw(sub); yy=10
for t in cfg['sub']:
    x=10
    for ch in t:
        fs=ImageFont.truetype(SF,int(cfg.get('ssize',88)*random.uniform(.95,1.05)))
        d.text((x,yy+random.randint(-3,3)),ch,font=fs,fill=255,stroke_width=cfg.get('sstroke',3),stroke_fill=255); x+=fs.getlength(ch)+random.uniform(1,5)
    yy+=int(cfg.get('ssize',88)*1.1)
sub=sub.crop(sub.getbbox()).rotate(cfg.get('tilt',4)*.9,resample=Image.BICUBIC,expand=True); sub=sub.crop(sub.getbbox())
if cfg.get('subbox'):
    bxim=Image.new('L',(sub.width+60,sub.height+40),255); bxim=cut(bxim,eps=.01,jit=.004)
    put(bxim,tuple(cfg['subbox']),(W-bxim.width)//2,Y-20)
    put(sub,tuple(cfg['scolor']),(W-sub.width)//2,Y)
else:
    put(sub,tuple(cfg['scolor']),(W-sub.width)//2+20,Y)
# textura leve de papel
n=np.random.normal(0,5,(H,W,1)); a=np.clip(np.array(cv).astype(float)+n,0,255).astype(np.uint8)
Image.fromarray(a).save(out,quality=93)
