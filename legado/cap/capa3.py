import random, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
# uso: capa2.py foto.jpg saida.jpg "LINHA1|LINHA2|LINHA3" [seed] [offset_foto]
src_path,out_path,text=sys.argv[1],sys.argv[2],sys.argv[3]
random.seed(int(sys.argv[4]) if len(sys.argv)>4 else 3)
OFF=int(sys.argv[5]) if len(sys.argv)>5 else 330
W,H=1080,1920; YEL=(245,197,24); INK=(22,22,22)
import os
FONT=os.environ.get('FONT','PermanentMarker.ttf'); FILL=tuple(int(x) for x in os.environ.get('FILL','22,22,22').split(',')); STROKE=tuple(int(x) for x in os.environ.get('STROKE','22,22,22').split(',')); SW=float(os.environ.get('SW','0.025'))
src=Image.open(src_path).convert('RGB'); sc=W/src.width; src=src.resize((W,int(src.height*sc)))
photo=Image.new('RGB',(W,H),(18,18,18)); photo.paste(src,(0,OFF))
g=ImageEnhance.Contrast(ImageOps.grayscale(photo)).enhance(1.25)
base=Image.merge('RGB',[g.point(lambda v:min(255,v+5)),g,g.point(lambda v:int(v*.95))])
base=Image.blend(base,Image.merge('RGB',[Image.effect_noise((W,H),18).convert('L')]*3),0.06).convert('RGBA')
def torn(y0,y1,x0,x1,j=14):
    pts=[];x=x0
    while x<x1: pts.append((x,y0+random.uniform(-j,j))); x+=random.uniform(18,46)
    pts+= [(x1,y0+random.uniform(-j,j)),(x1,y1+random.uniform(-j,j))]; x=x1
    while x>x0: pts.append((x,y1+random.uniform(-j*1.6,j*1.6))); x-=random.uniform(14,40)
    return pts+[(x0,y1)]
lines=[l for l in text.split('|') if l]
# medir altura total aproximada
sizes=[]
for i,l in enumerate(lines):
    base_s=min(int(os.environ.get('MAXS','170')),int(int(os.environ.get('K','1500'))/max(len(l),1)))
    sizes.append(int(base_s*random.uniform(0.92,1.08)))
total=sum(int(s*1.22) for s in sizes)
y0=240; y1=y0+total+110
paper=Image.new('RGBA',(W+200,H),(0,0,0,0))
pts=[(x+100,y) for x,y in torn(y0,y1,-30,W+30)]
sh=Image.new('RGBA',paper.size,(0,0,0,0)); ImageDraw.Draw(sh).polygon([(x+10,y+14) for x,y in pts],fill=(0,0,0,150)); sh=sh.filter(ImageFilter.GaussianBlur(12))
ImageDraw.Draw(paper).polygon(pts,fill=YEL+(255,))
comp=Image.alpha_composite(sh,paper).rotate(random.uniform(-2.5,-1),resample=Image.BICUBIC,center=((W+200)/2,(y0+y1)/2))
base.alpha_composite(comp,(-100,0))
# texto à mão: cada linha com rotação, tamanho e deslocamento próprios
y=y0+45
for i,(l,s) in enumerate(zip(lines,sizes)):
    f=ImageFont.truetype(FONT,s)
    tmp=Image.new('RGBA',(W*2,int(s*2.1)),(0,0,0,0)); d=ImageDraw.Draw(tmp)
    x=40
    for ch in l:  # letra a letra, com jitter vertical e de tamanho
        fs=ImageFont.truetype(FONT,int(s*random.uniform(.94,1.06)))
        lt=Image.new('RGBA',(int(s*1.6),int(s*2)),(0,0,0,0)); ImageDraw.Draw(lt).text((int(s*.2),int(s*.3)),ch,font=fs,fill=FILL,stroke_width=max(3,int(s*SW)),stroke_fill=STROKE); lt=lt.rotate(random.uniform(-8,8),resample=Image.BICUBIC); tmp.alpha_composite(lt,(int(x-s*.2),int(s*.1+random.uniform(-8,8))))
        x+=d.textlength(ch,font=fs)+random.uniform(-4,1)+max(3,int(s*SW))
    tmp=tmp.crop((0,0,int(x)+60,tmp.height))
    if i==len(lines)-1:  # sublinhado de pincel
        dd=ImageDraw.Draw(tmp); w=tmp.width
        pts2=[(50+t*(w-110)/20, tmp.height-22+math.sin(t/3)*4+random.uniform(-3,3)) for t in range(21)]
        dd.line(pts2,fill=STROKE,width=22,joint='curve'); dd.line(pts2,fill=FILL,width=12,joint='curve')
    bb=tmp.getbbox(); tmp=tmp.crop((bb[0]-10,bb[1]-10,bb[2]+10,bb[3]+10))
    if tmp.width>960: r=960/tmp.width; tmp=tmp.resize((960,int(tmp.height*r)),Image.LANCZOS)
    rot=random.uniform(-5,3)
    tmp=tmp.rotate(rot,resample=Image.BICUBIC,expand=True)
    xpos=int((W-tmp.width)/2+random.uniform(-40,40))
    base.alpha_composite(tmp,(max(10,xpos),int(y)))
    y+=max(int(s*1.12),tmp.height-int(s*.15))
base.convert('RGB').save(out_path,quality=92)
