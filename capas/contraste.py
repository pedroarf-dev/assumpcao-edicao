import sys
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont
F='/tmp/fnt/fontsource-fraunces-5.3.0/files/'
W,H=1080,1920
src=ImageOps.exif_transpose(Image.open(sys.argv[1])).convert('RGB')
w,h=src.size; im=src.crop((0,300,w,300+int(w*16/9))).resize((W,H),Image.LANCZOS)
g=ImageOps.grayscale(im)
g=ImageOps.autocontrast(g,cutoff=(2,1))
lut=[int(255*((v/255)**1.6)) for v in range(256)]   # escurece meios-tons
g=g.point(lut); g=ImageEnhance.Contrast(g).enhance(1.35)
# vinheta lateral para simular luz de janela
grad=Image.linear_gradient('L').rotate(90).resize((W,H)); grad=grad.point(lambda v:int(150+105*(v/255)))
g=Image.composite(g,Image.new('L',(W,H),0),grad)
im=g.convert('RGB'); d=ImageDraw.Draw(im); OR=(232,112,52)
d.text((90,330),'Talento',font=ImageFont.truetype(F+'fraunces-latin-300-normal.woff',132),fill=(20,20,22))
d.text((90,480),'não existe',font=ImageFont.truetype(F+'fraunces-latin-300-italic.woff',132),fill=OR)
d.line([(92,660),(240,660)],fill=(20,20,22),width=3)
d.text((90,690),'pensamento',font=ImageFont.truetype(F+'fraunces-latin-300-normal.woff',34),fill=(40,40,44))
lamp=Image.open('marca-pensamento.png'); im.paste(lamp,(910,1530),lamp)
d.text((90,1605),'@assumpcao_pedro',font=ImageFont.truetype(F+'fraunces-latin-300-normal.woff',30),fill=(230,230,230))
im.save('capa3-contraste.jpg',quality=92)
a=Image.open('capa3.jpg').resize((360,640)); b=im.resize((360,640))
r=Image.new('RGB',(730,640),(255,255,255)); r.paste(a,(0,0)); r.paste(b,(370,0)); r.save('contraste-comparar.jpg',quality=88)
