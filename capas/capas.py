import sys, math, random
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont, ImageFilter
F='/tmp/fnt/'
def font(n,s): return ImageFont.truetype(F+n,s)
CAV=lambda s: font('fontsource-caveat-5.3.0/files/caveat-latin-700-normal.woff',s)
CAV4=lambda s: font('fontsource-caveat-5.3.0/files/caveat-latin-400-normal.woff',s)
FRA=lambda s: font('fontsource-fraunces-5.3.0/files/fraunces-latin-300-normal.woff',s)
FRAI=lambda s: font('fontsource-fraunces-5.3.0/files/fraunces-latin-300-italic.woff',s)
W,H=1080,1920
src=ImageOps.exif_transpose(Image.open(sys.argv[1])).convert('RGB')
def bw(im,bright=1.08,contrast=0.92):
    g=ImageOps.grayscale(im); g=ImageEnhance.Contrast(g).enhance(contrast); g=ImageEnhance.Brightness(g).enhance(bright)
    g=g.point(lambda v: int(28+v*0.89))  # lift blacks
    return g.convert('RGB')
def crop916(im,top):
    w,h=im.size; ch=int(w*16/9); return im.crop((0,top,w,top+ch)).resize((W,H),Image.LANCZOS)
ORANGE=(232,112,52); GREEN=(92,150,70); INK=(34,34,38); YEL=(240,196,60)
def wobble(d,pts,color,width,seed=1):
    random.seed(seed); q=[(x+random.uniform(-3,3),y+random.uniform(-3,3)) for x,y in pts]
    d.line(q,fill=color,width=width,joint='curve')
def circle_pts(cx,cy,rx,ry,a0=0,a1=360,n=60):
    return [(cx+rx*math.cos(math.radians(a)),cy+ry*math.sin(math.radians(a))) for a in [a0+(a1-a0)*i/n for i in range(n+1)]]
def tag(d,x,y,col=INK):
    d.text((x,y),'@assumpcao_pedro',font=FRA(30),fill=col)

# ---------- 1: P&B + toque de gromelô ----------
im=bw(crop916(src,520)); d=ImageDraw.Draw(im)
# lampada desenhada acima da cabeça
cx,cy=520,660
wobble(d,circle_pts(cx,cy,62,72,140,400),ORANGE,7,2)
wobble(d,[(cx-28,cy+62),(cx-24,cy+100),(cx+24,cy+100),(cx+28,cy+62)],ORANGE,7,3)
wobble(d,[(cx-22,cy+114),(cx+22,cy+114)],ORANGE,6,4); wobble(d,[(cx-14,cy+128),(cx+14,cy+128)],ORANGE,6,5)
for a in (-150,-115,-65,-30):
    r1,r2=88,120; wobble(d,[(cx+r1*math.cos(math.radians(a)),cy+r1*math.sin(math.radians(a))),(cx+r2*math.cos(math.radians(a)),cy+r2*math.sin(math.radians(a)))],YEL,6,a)
wobble(d,[(cx-18,cy+40),(cx-8,cy+10),(cx+2,cy+40),(cx+12,cy+10),(cx+20,cy+40)],ORANGE,5,9)
d.text((90,250),'talento',font=CAV(150),fill=INK)
d.text((90,390),'não existe?',font=CAV(150),fill=INK)
tag(d,90,1600,(60,60,64))
im.save('/home/claude/capas/capa1.jpg',quality=92)

# ---------- 2: folha de caderno ----------
pap=Image.new('RGB',(W,H),(246,241,228)); d=ImageDraw.Draw(pap)
for y in range(150,H,62): d.line([(0,y),(W,y)],fill=(170,190,215),width=2)
d.line([(120,0),(120,H)],fill=(214,120,120),width=3)
ph=bw(crop916(src,900).crop((60,200,1020,1640)),1.05,0.95).resize((760,1140),Image.LANCZOS)
fr=Image.new('RGB',(ph.width+36,ph.height+36),(252,252,250)); fr.paste(ph,(18,18))
fr=fr.rotate(-3,expand=True,resample=Image.BICUBIC,fillcolor=(246,241,228))
sh=Image.new('RGBA',fr.size,(0,0,0,0)); ImageDraw.Draw(sh).rectangle((12,12,fr.width-12,fr.height-12),fill=(0,0,0,60)); sh=sh.filter(ImageFilter.GaussianBlur(14))
px,py=200,600
pap.paste(sh,(px+10,py+16),sh); pap.paste(fr,(px,py))
tp=Image.new('RGBA',(220,64),(235,225,190,190)).rotate(4,expand=True); pap.paste(tp,(px+300,py-34),tp)
d=ImageDraw.Draw(pap)
d.text((170,262),'talento não existe?',font=CAV(108),fill=INK)
wobble(d,[(175,400),(420,392),(700,404),(900,396)],ORANGE,6,7)
d.text((180,420),'(ou só falta amparo)',font=CAV4(64),fill=(70,70,90))
tag(d,180,525,(70,70,90))
pap.save('/home/claude/capas/capa2.jpg',quality=92)

# ---------- 3: respiro ----------
im=bw(crop916(src,300),1.1,0.9); d=ImageDraw.Draw(im)
d.text((90,330),'Talento',font=FRA(132),fill=INK)
d.text((90,480),'não existe',font=FRAI(132),fill=ORANGE)
d.line([(92,660),(240,660)],fill=INK,width=3)
d.text((90,690),'pensamento',font=FRA(34),fill=(70,70,74))
d.ellipse((1000-14,1610,1000+14,1638),outline=ORANGE,width=4)  # marca do eixo
tag(d,90,1605,(60,60,64))
im.save('/home/claude/capas/capa3.jpg',quality=92)

# prévia lado a lado com corte 3:4
row=Image.new('RGB',(3*360+40,640+60+480+20),(255,255,255))
for i in range(3):
    c=Image.open(f'/home/claude/capas/capa{i+1}.jpg')
    row.paste(c.resize((360,640)),(i*370,0))
    g=c.crop((0,240,1080,1680)).resize((360,480)); row.paste(g,(i*370,700))
row.save('/home/claude/capas/prev.jpg',quality=85)
