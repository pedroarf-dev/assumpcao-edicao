import sys
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont
F='/tmp/fnt/fontsource-fraunces-5.3.0/files/'
W,H=1080,1920
src=ImageOps.exif_transpose(Image.open(sys.argv[1])).convert('RGB')
w,h=src.size; im=src.crop((0,300,w,300+int(w*16/9))).resize((W,H),Image.LANCZOS)
im=ImageEnhance.Color(im).enhance(1.25); im=ImageEnhance.Brightness(im).enhance(1.02); im=ImageEnhance.Contrast(im).enhance(1.0)
d=ImageDraw.Draw(im); INK=(34,34,38); OR=(232,112,52)
d.text((90,330),'Talento',font=ImageFont.truetype(F+'fraunces-latin-300-normal.woff',132),fill=INK)
d.text((90,480),'não existe',font=ImageFont.truetype(F+'fraunces-latin-300-italic.woff',132),fill=OR)
d.line([(92,660),(240,660)],fill=INK,width=3)
d.text((90,690),'pensamento',font=ImageFont.truetype(F+'fraunces-latin-300-normal.woff',34),fill=(70,70,74))
d.ellipse((986,1610,1014,1638),outline=OR,width=4)
d.text((90,1605),'@assumpcao_pedro',font=ImageFont.truetype(F+'fraunces-latin-300-normal.woff',30),fill=(60,60,64))
im.save('capa3-cor.jpg',quality=92)
# simulação de grid xadrez 3x3 com capas disponíveis + obras do grid real
pb=Image.open('capa3.jpg').crop((0,240,1080,1680)).resize((300,400)); cr=im.crop((0,240,1080,1680)).resize((300,400))
g=Image.new('RGB',(3*300+8,3*400+8),(255,255,255))
for i in range(9):
    r,c=divmod(i,3); g.paste(pb if i%2==0 else cr,(c*304,r*404))
g.save('grid-xadrez.jpg',quality=85)
