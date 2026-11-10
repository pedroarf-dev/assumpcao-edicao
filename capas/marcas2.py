import math, random
from PIL import Image, ImageDraw, ImageFont
OR=(232,112,52); INK=(40,40,44); S=4
F=ImageFont.truetype('/tmp/fnt/fontsource-fraunces-5.3.0/files/fraunces-latin-300-normal.woff',40)
def L(d,pts,w,seed=0,j=0.02):
    random.seed(seed); d.line([(x+random.uniform(-j,j)*S*40,y+random.uniform(-j,j)*S*40) for x,y in pts],fill=OR,width=w,joint='curve')
def arc(cx,cy,rx,ry,a0,a1,n=40): return [(cx+rx*math.cos(math.radians(a0+(a1-a0)*i/n)),cy+ry*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)]
def lampada(d,cx,cy,r,w):
    L(d,arc(cx,cy-r*.25,r*.7,r*.75,140,400),w,1)
    L(d,[(cx-r*.42,cy+r*.28),(cx-r*.34,cy+r*.62),(cx+r*.34,cy+r*.62),(cx+r*.42,cy+r*.28)],w,2)
    L(d,[(cx-r*.3,cy+r*.78),(cx+r*.3,cy+r*.78)],w,3); L(d,[(cx-r*.18,cy+r*.93),(cx+r*.18,cy+r*.93)],w,4)
    L(d,[(cx-r*.2,cy+r*.25),(cx-r*.1,cy-r*.15),(cx,cy+r*.15),(cx+r*.1,cy-r*.15),(cx+r*.2,cy+r*.25)],w,5)
def flor(d,cx,cy,r,w):
    fy=cy-r*.35
    for k in range(5):
        a=math.radians(-90+k*72); px,py=cx+math.cos(a)*r*.38,fy+math.sin(a)*r*.38
        pts=arc(px,py,r*.24,r*.24,0,360)
        L(d,pts,w,10+k)
    L(d,arc(cx,fy,r*.12,r*.12,0,360),w,20)
    L(d,[(cx,fy+r*.62),(cx+r*.05,cy+r*.4),(cx-r*.02,cy+r*1.0)],w,21)
    L(d,[(cx+r*.02,cy+r*.55),(cx+r*.35,cy+r*.35),(cx+r*.1,cy+r*.62)],w,22)
def barco(d,cx,cy,r,w):
    L(d,[(cx-r,cy+r*.15),(cx+r,cy+r*.15),(cx+r*.62,cy+r*.62),(cx-r*.62,cy+r*.62),(cx-r,cy+r*.15)],w,30)
    L(d,[(cx-r*.55,cy+r*.15),(cx,cy-r*.75),(cx+r*.55,cy+r*.15)],w,31)
    L(d,[(cx,cy-r*.75),(cx,cy+r*.15)],w,32)
fns={'pensamento':lampada,'arte':flor,'sociedade':barco}
W=1200; im=Image.new('RGB',(W*S,520*S),(250,249,246)); d=ImageDraw.Draw(im)
for i,k in enumerate(fns): fns[k](d,(200+i*400)*S,190*S,100*S,8*S)
im=im.resize((W,520),Image.LANCZOS); d=ImageDraw.Draw(im)
for i,k in enumerate(fns):
    tw=d.textlength(k,font=F); d.text((200+i*400-tw/2,380),k,font=F,fill=INK)
im.save('marcas2.jpg',quality=92)
c=Image.open('capa3.jpg'); d=ImageDraw.Draw(c); d.rectangle((960,1580,1050,1660),fill=c.getpixel((900,1600)))
out=[]
for k in fns:
    cc=c.copy(); lay=Image.new('RGBA',(160*S,160*S),(0,0,0,0)); fns[k](ImageDraw.Draw(lay),80*S,80*S,34*S,3*S)
    lay=lay.resize((160,160),Image.LANCZOS); cc.paste(lay,(910,1530),lay); out.append(cc.crop((0,240,1080,1680)).resize((360,480)))
row=Image.new('RGB',(3*370,480),(255,255,255))
for i,o in enumerate(out): row.paste(o,(i*375,0))
row.save('marcas2-capa.jpg',quality=88)
