import math, random
from PIL import Image, ImageDraw, ImageFont
OR=(232,112,52); INK=(40,40,44)
F=ImageFont.truetype('/tmp/fnt/fontsource-fraunces-5.3.0/files/fraunces-latin-300-normal.woff',40)
S=4
def marca(d,kind,cx,cy,r,w):
    if kind=='pensamento':
        d.arc((cx-r,cy-r,cx+r,cy+r),start=-60,end=250,fill=OR,width=w)
    elif kind=='arte':
        random.seed(3); pts=[]
        for i in range(40):
            t=i/39; x=cx-r*1.2+t*2.4*r; y=cy+math.sin(t*14)*r*0.55*(1-abs(t-.5)) + random.uniform(-r*.08,r*.08)
            pts.append((x,y))
        d.line(pts,fill=OR,width=w,joint='curve')
    else:
        rr=r*0.62
        d.ellipse((cx-rr*1.9-rr,cy-rr,cx-rr*1.9+rr*1.0+ rr*0,cy+rr),outline=OR,width=w) if False else None
        d.ellipse((cx-rr*2+0,cy-rr,cx,cy+rr),outline=OR,width=w)
        d.ellipse((cx,cy-rr,cx+rr*2,cy+rr),outline=OR,width=w)
W=1200; im=Image.new('RGB',(W*S,520*S),(250,249,246)); d=ImageDraw.Draw(im)
for i,k in enumerate(['pensamento','arte','sociedade']):
    cx=(200+i*400)*S; marca(d,k,cx,200*S,90*S,9*S)
im=im.resize((W,520),Image.LANCZOS); d=ImageDraw.Draw(im)
for i,k in enumerate(['pensamento','arte','sociedade']):
    tw=d.textlength(k,font=F); d.text((200+i*400-tw/2,360),k,font=F,fill=INK)
im.save('marcas.jpg',quality=92)
# no canto da capa
c=Image.open('capa3.jpg'); big=Image.new('RGB',(1080*S,1920*S)); 
c2=c.copy(); d=ImageDraw.Draw(c2); d.rectangle((960,1580,1050,1660),fill=c.getpixel((900,1600)))
lay=Image.new('RGBA',(200*S,200*S),(0,0,0,0)); dl=ImageDraw.Draw(lay); 
out=[]
for k in ['pensamento','arte','sociedade']:
    cc=c2.copy(); lay=Image.new('RGBA',(160*S,120*S),(0,0,0,0)); dl=ImageDraw.Draw(lay); marca(dl,k,80*S,60*S,22*S,4*S)
    lay=lay.resize((160,120),Image.LANCZOS); cc.paste(lay,(920,1564),lay); out.append(cc.crop((0,240,1080,1680)).resize((360,480)))
row=Image.new('RGB',(3*370,480),(255,255,255))
for i,o in enumerate(out): row.paste(o,(i*375,0))
row.save('marcas-capa.jpg',quality=88)
