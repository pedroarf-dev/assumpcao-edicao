import json,random,math,sys
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter
W,H=1080,1350;YEL=(246,196,26);BLK=(20,20,20);WHT=(250,248,242)
cfg={'sx':.92,'sy':1.12,'ov0':.93,'ov1':1.0,'maxh':170}
ns={'cfg':cfg,'random':random,'np':np,'cv2':cv2,'Image':Image,'ImageDraw':ImageDraw,'ImageFont':ImageFont,'ImageFilter':ImageFilter,'math':math,'TF':'fx/lilita-one.ttf'}
src=open('capa6.py').read()
for fn in ['def cut','def glyph','def line']:
    i=src.index(fn);j=src.index('\ndef ',i+5);exec(src[i:j],ns)
tagsrc=open('capa7.py').read();i=tagsrc.index('def add_tag');j=tagsrc.index('\nif cfg',i);exec(tagsrc[i:j],ns)
BODY=ImageFont.truetype('../v30/fonts/InterMedium.ttf',46)
def wrap(d,t,f,maxw):
    out=[];cur=''
    for w in t.split():
        if d.textlength((cur+' '+w).strip(),font=f)<=maxw:cur=(cur+' '+w).strip()
        else:out.append(cur);cur=w
    out.append(cur);return out
def title(img,lines,y,color,shadow=None,size=150,maxw=900):
    for t in lines:
        g=ns['line'](t,size,maxw).rotate(random.uniform(-2,2),resample=Image.BICUBIC,expand=True)
        x=(W-g.width)//2
        if shadow:
            s=Image.new('RGBA',g.size,shadow+(255,));s.putalpha(g);img.alpha_composite(s,(x+8,y+8))
        c=Image.new('RGBA',g.size,color+(255,));c.putalpha(g);img.alpha_composite(c,(x,y));y+=g.height-4
    return y
def body(img,text,y,color,maxw=880,box=None):
    d=ImageDraw.Draw(img)
    for para in text.split('\n'):
        for l in wrap(d,para,BODY,maxw):
            w=d.textlength(l,font=BODY);x=(W-w)/2
            if box: d.rectangle((x-10,y-4,x+w+10,y+58),fill=box)
            d.text((x,y),l,font=BODY,fill=color);y+=66
        y+=22
    return y
def num(img,n,color):
    d=ImageDraw.Draw(img);f=ImageFont.truetype('Anton.ttf',40);d.text((70,60),f'{n:02d}',font=f,fill=color)
slides=json.load(open(sys.argv[1]))
random.seed(3)
for i,s in enumerate(slides):
    bg=YEL if s.get('bg','y')=='y' else BLK
    img=Image.new('RGBA',(W,H),bg+(255,))
    if bg==YEL:
        n=np.random.normal(0,4,(H,W,1));a=np.clip(np.array(img.convert('RGB')).astype(float)+n,0,255).astype(np.uint8);img=Image.fromarray(a).convert('RGBA')
    tc=BLK if bg==YEL else YEL
    if s.get('white'): tc=WHT
    y=s.get('y',260)
    if s.get('kicker'):
        y=body(img,s['kicker'],y,BLK if bg==YEL else WHT)+10
    y=title(img,s['title'],y,tc,BLK if (bg==YEL and tc==WHT) else None,size=s.get('size',150))
    if s.get('body'): body(img,s['body'],y+40,BLK if bg==YEL else WHT,box=None)
    import os
    V=os.environ.get('VIDEO')
    if i>0 and not V: num(img,i+1,BLK if bg==YEL else YEL)
    rgb=img.convert('RGB')
    if not V or i==0: ns['add_tag'](rgb,60,H-150,size=40)
    rgb.save(f"../car/{'v' if V else ''}slide{i+1:02d}.jpg",quality=93)
