import random, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
random.seed(int(sys.argv[2]) if len(sys.argv)>2 else 7)
W,H=1080,1920
YEL=(245,197,24); INK=(20,20,20)
src=Image.open(sys.argv[1]).convert('RGB')
sc=W/src.width; src=src.resize((W,int(src.height*sc)))
photo=Image.new('RGB',(W,H),(18,18,18)); OFF=int(sys.argv[4]) if len(sys.argv)>4 else 300; photo.paste(src,(0,OFF))
g=ImageOps.grayscale(photo); g=ImageEnhance.Contrast(g).enhance(1.25); g=ImageEnhance.Brightness(g).enhance(0.95)
base=Image.merge('RGB',[g.point(lambda v:min(255,int(v*1.0+4))),g,g.point(lambda v:int(v*0.96))])
# grain
noise=Image.effect_noise((W,H),18).convert('L')
base=Image.blend(base,Image.merge('RGB',[noise]*3),0.06)
def torn(y0,y1,x0=-30,x1=W+30,j=14):
    pts=[]; x=x0
    while x<x1: pts.append((x,y0+random.uniform(-j,j))); x+=random.uniform(18,46)
    pts.append((x1,y0+random.uniform(-j,j)))
    # right edge
    pts.append((x1,y1+random.uniform(-j,j)))
    x=x1
    while x>x0: pts.append((x,y1+random.uniform(-j*1.6,j*1.6))); x-=random.uniform(14,40)
    pts.append((x0,y1)); return pts
# paper with shadow, slight rotation
paper=Image.new('RGBA',(W+200,H),(0,0,0,0)); d=ImageDraw.Draw(paper)
pts=[(x+100,y) for x,y in torn(230,830)]
shadow=Image.new('RGBA',paper.size,(0,0,0,0)); ImageDraw.Draw(shadow).polygon([(x+10,y+14) for x,y in pts],fill=(0,0,0,150))
shadow=shadow.filter(ImageFilter.GaussianBlur(12))
d.polygon(pts,fill=YEL+(255,))
# paper fiber texture
tex=Image.effect_noise(paper.size,30).convert('L').point(lambda v:255 if v>140 else 0)
mask=paper.split()[3]
fiber=Image.new('RGBA',paper.size,(255,240,180,0)); fiber.putalpha(Image.eval(tex,lambda v:v//10))
paper=Image.alpha_composite(paper,Image.composite(fiber,Image.new('RGBA',paper.size,(0,0,0,0)),mask))
# text
font=lambda s:ImageFont.truetype('Anton.ttf',s)
lines=[("NEM TODO MUNDO",104),("TEM UM AVIÃO",168),("PRA FUGIR.",168)]
td=ImageDraw.Draw(paper); y=285
for t,s in lines:
    f=font(s); w=td.textlength(t,font=f); td.text(((W+200-w)/2,y),t,font=f,fill=INK); y+=s*1.02
comp=Image.alpha_composite(shadow,paper).rotate(-2.2,resample=Image.BICUBIC,center=((W+200)/2,500))
out=base.convert('RGBA'); out.alpha_composite(comp,(-100,0))
# small yellow torn tab bottom-left with handle
tab=Image.new('RGBA',(520,130),(0,0,0,0)); ImageDraw.Draw(tab).polygon(torn(10,115,0,520,7),fill=YEL+(255,))
ImageDraw.Draw(tab).text((40,28),"☕ @assumpcao_pedro".replace('☕ ',''),font=font(58),fill=INK)
tab=tab.rotate(1.5,resample=Image.BICUBIC,expand=True)
out.alpha_composite(tab,(40,1500))
out.convert('RGB').save(sys.argv[3] if len(sys.argv)>3 else 'capa.jpg',quality=92)
