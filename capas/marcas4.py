import math, random
from PIL import Image, ImageDraw, ImageFont
OR=(232,112,52); INK=(40,40,44); S=4
F=ImageFont.truetype('/tmp/fnt/fontsource-fraunces-5.3.0/files/fraunces-latin-300-normal.woff',40)
def dens(pts,step):
    out=[]
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        n=max(2,int(math.hypot(x1-x0,y1-y0)/step))
        out+= [(x0+(x1-x0)*i/n,y0+(y1-y0)*i/n) for i in range(n)]
    return out+[pts[-1]]
def L(d,pts,w,seed,amp):
    random.seed(seed); p=dens(pts,amp*0.25); ph=random.uniform(0,6); ph2=random.uniform(0,6)
    n=len(p); q=[(x+amp*0.35*math.sin(i*0.05+ph), y+amp*0.35*math.cos(i*0.04+ph2)) for i,(x,y) in enumerate(p)]
    for i in range(len(q)-1):
        t=i/max(1,n-2); taper=min(1,t*6,(1-t)*6)
        ww=max(1,int(w*(0.45+0.55*taper)*(0.9+0.15*math.sin(i*0.03+ph))))
        d.line([q[i],q[i+1]],fill=OR,width=ww)
        d.ellipse((q[i][0]-ww/2,q[i][1]-ww/2,q[i][0]+ww/2,q[i][1]+ww/2),fill=OR)
def arc(cx,cy,rx,ry,a0,a1,n=40): return [(cx+rx*math.cos(math.radians(a0+(a1-a0)*i/n)),cy+ry*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)]
def lampada(d,cx,cy,r,w,a):
    L(d,arc(cx+r*.03,cy-r*.28,r*.66,r*.74,128,392),w,1,a)
    L(d,[(cx-r*.38,cy+r*.24),(cx-r*.32,cy+r*.6),(cx+r*.3,cy+r*.63),(cx+r*.4,cy+r*.2)],w,2,a)
    L(d,[(cx-r*.33,cy+r*.79),(cx+r*.27,cy+r*.76)],w,3,a); L(d,[(cx-r*.16,cy+r*.95),(cx+r*.2,cy+r*.93)],w,4,a)
    L(d,[(cx-r*.22,cy+r*.22),(cx-r*.12,cy-r*.2),(cx,cy+r*.1),(cx+r*.1,cy-r*.22),(cx+r*.18,cy+r*.2)],w,5,a)
def flor(d,cx,cy,r,w,a):
    fy=cy-r*.33
    for k in range(5):
        an=-90+k*72+random.uniform(-8,8); rad=math.radians(an)
        pts=[(cx+math.cos(rad-0.55)*r*.12,fy+math.sin(rad-0.55)*r*.12)]+[(cx+math.cos(rad)*r*(.12+.5*math.sin(math.pi*t/8))+math.cos(rad+math.pi/2)*r*.27*math.sin(2*math.pi*t/8) ,fy+math.sin(rad)*r*(.12+.5*math.sin(math.pi*t/8))+math.sin(rad+math.pi/2)*r*.27*math.sin(2*math.pi*t/8)) for t in range(9)]
        L(d,pts,w,10+k,a)
    L(d,arc(cx,fy,r*.1,r*.11,20,380),w,20,a)
    L(d,[(cx+r*.02,fy+r*.18),(cx+r*.08,cy+r*.35),(cx-r*.03,cy+r*1.0)],w,21,a)
    L(d,[(cx+r*.05,cy+r*.5),(cx+r*.3,cy+r*.28),(cx+r*.42,cy+r*.3),(cx+r*.12,cy+r*.62)],w,22,a)
def barco(d,cx,cy,r,w,a):
    L(d,[(cx-r*1.02,cy+r*.12),(cx+r*.98,cy+r*.18),(cx+r*.6,cy+r*.62),(cx-r*.58,cy+r*.6),(cx-r*.95,cy+r*.18)],w,30,a)
    L(d,[(cx-r*.52,cy+r*.14),(cx+r*.03,cy-r*.78),(cx+r*.56,cy+r*.16)],w,31,a)
    L(d,[(cx+r*.02,cy-r*.7),(cx-r*.02,cy+r*.15)],w,32,a)
fns={'pensamento':lampada,'arte':flor,'sociedade':barco}
W=1200; im=Image.new('RGB',(W*S,520*S),(250,249,246)); d=ImageDraw.Draw(im)
for i,k in enumerate(fns): random.seed(i); fns[k](d,(200+i*400)*S,190*S,100*S,6*S,9*S)
im=im.resize((W,520),Image.LANCZOS); d=ImageDraw.Draw(im)
for i,k in enumerate(fns):
    tw=d.textlength(k,font=F); d.text((200+i*400-tw/2,380),k,font=F,fill=INK)
im.save('marcas4.jpg',quality=92)
c=Image.open('capa3.jpg'); d=ImageDraw.Draw(c); d.rectangle((960,1580,1050,1660),fill=c.getpixel((900,1600)))
out=[]
for i,k in enumerate(fns):
    cc=c.copy(); lay=Image.new('RGBA',(160*S,160*S),(0,0,0,0)); random.seed(i); fns[k](ImageDraw.Draw(lay),80*S,80*S,34*S,2.4*S,3*S)
    lay=lay.resize((160,160),Image.LANCZOS); lay.save(f'marca-{k}.png'); cc.paste(lay,(910,1530),lay); out.append(cc.crop((0,240,1080,1680)).resize((360,480)))
row=Image.new('RGB',(3*370,480),(255,255,255))
for i,o in enumerate(out): row.paste(o,(i*375,0))
row.save('marcas4-capa.jpg',quality=88)
