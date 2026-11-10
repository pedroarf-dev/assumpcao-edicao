import random, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
# capa4.py foto saida "TITULO" "SUBTITULO|LINHA2" "RODAPE" [seed] [foto_y] [cor_bloco]
src,out,title,sub,foot=sys.argv[1:6]
random.seed(int(sys.argv[6]) if len(sys.argv)>6 else 4)
PY_=int(sys.argv[7]) if len(sys.argv)>7 else 420
BLK=tuple(int(x) for x in (sys.argv[8] if len(sys.argv)>8 else '20,20,20').split(','))
W,H=1080,1920; YEL=(246,196,26); WHT=(250,248,242)
HEAD=os.environ.get('HEAD','Knewave.ttf'); SUB='Knewave.ttf'
# foto colorida, quente
im=Image.open(src).convert('RGB'); sc=W/im.width; im=im.resize((W,int(im.height*sc)))
r,g,b=im.split(); r=r.point(lambda v:min(255,int(v*1.06))); b=b.point(lambda v:int(v*.92)); im=Image.merge('RGB',(r,g,b))
im=ImageEnhance.Contrast(im).enhance(1.08)
canvas=Image.new('RGB',(W,H),BLK); canvas.paste(im,(0,PY_)); canvas=canvas.convert('RGBA')
def torn_edge(y,down=True,j=10):
    pts=[];x=-20
    while x<W+20: pts.append((x,y+random.uniform(-j,j))); x+=random.uniform(10,34)
    return pts
def block(y0,y1,top_edge,bot_edge):
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    top=torn_edge(y0) if top_edge else [(-20,y0),(W+20,y0)]
    bot=torn_edge(y1) if bot_edge else [(W+20,y1),(-20,y1)]
    if bot_edge: bot=bot[::-1]
    # papel branco rasgado por baixo (borda branca irregular)
    if bot_edge:
        wb=[(x,y+random.uniform(8,26)) for x,y in bot]
        d.polygon(top+wb,fill=WHT+(255,))
    if top_edge:
        wt=[(x,y-random.uniform(8,26)) for x,y in top]
        d.polygon(wt+bot,fill=WHT+(255,))
    d.polygon(top+bot,fill=BLK+(255,))
    sh=lay.filter(ImageFilter.GaussianBlur(6)); sh=Image.eval(sh.split()[3],lambda a:int(a*.5))
    shadow=Image.new('RGBA',(W,H),(0,0,0,0)); shadow.putalpha(sh)
    canvas.alpha_composite(shadow,(0,8)); canvas.alpha_composite(lay)
def rough(mask):
    n=Image.effect_noise(mask.size,60).convert('L').filter(ImageFilter.GaussianBlur(1.2))
    m=ImageChops.multiply(mask.filter(ImageFilter.GaussianBlur(1.5)),Image.eval(n,lambda v:min(255,v*2)))
    return m.point(lambda v:255 if v>90 else 0)
def lettering(text,font,size,fill,maxw,jit=5):
    tmp=Image.new('L',(W*3,int(size*1.6)),0); d=ImageDraw.Draw(tmp); x=20
    for ch in text:
        fs=ImageFont.truetype(font,int(size*random.uniform(.93,1.07)))
        lt=Image.new('L',(int(size*1.4),int(size*1.6)),0); ImageDraw.Draw(lt).text((int(size*.15),int(size*.05)),ch,font=fs,fill=255)
        lt=lt.rotate(random.uniform(-jit,jit),resample=Image.BICUBIC)
        tmp.paste(255,(int(x-size*.15),int(random.uniform(-6,6))),lt)
        x+=d.textlength(ch,font=fs)+random.uniform(-3,3)
    bb=tmp.getbbox(); tmp=tmp.crop(bb)
    if tmp.width>maxw: tmp=tmp.resize((maxw,int(tmp.height*maxw/tmp.width)),Image.LANCZOS)
    m=tmp
    layer=Image.new('RGBA',m.size,fill+(0,)); layer.putalpha(m); return layer
# bloco do topo
block(-40,PY_+90,False,True)
y=150
for i,line in enumerate(title.split('|')):
    L=lettering(line,HEAD,260,WHT,980)
    L=L.rotate(random.uniform(-2.5,1.5),resample=Image.BICUBIC,expand=True)
    canvas.alpha_composite(L,((W-L.width)//2,y)); y+=L.height+10
for line in sub.split('|'):
    L=lettering(line,SUB,110,YEL,820,jit=4)
    L=L.rotate(random.uniform(-3,2),resample=Image.BICUBIC,expand=True)
    canvas.alpha_composite(L,((W-L.width)//2,y)); y+=L.height+6
d=ImageDraw.Draw(canvas)
import math
cx,cy,R=930,120,52
pts=[(cx+(R if i%2==0 else R*.42)*math.cos(math.pi/2+i*math.pi/5)*-1,cy-(R if i%2==0 else R*.42)*math.sin(math.pi/2+i*math.pi/5)) for i in range(10)]
d.polygon(pts,fill=YEL)
sw=[(160+t*760, y+22+18*math.sin(t*3.0)-t*10) for t in [i/60 for i in range(61)]]
d.line(sw,fill=WHT,width=12,joint='curve')
# faixa de baixo
if foot:
    block(1700,1960,True,False)
    L=lettering(foot,HEAD,125,WHT,760)
    canvas.alpha_composite(L,((W-L.width)//2,1752))
canvas.convert('RGB').save(out,quality=92)
