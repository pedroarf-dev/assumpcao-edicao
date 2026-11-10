import json,subprocess,math,random
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
W,H,FPS=1080,1920,30
segs=json.load(open('segs.json'))
def mt(x):
    for s in segs:
        if s['a']-0.001<=x<=s['b']+0.001:return s['ns']+x-s['a']
    best=min(segs,key=lambda s:abs(s['a']-x));return best['ns']
PM='../cap/PermanentMarker.ttf';AN='../cap/Anton.ttf'
def tape(text,size=64,rot=-2,fg=(246,196,26),bg=(20,20,20,235)):
    f=ImageFont.truetype(PM,size);w=f.getbbox(text)[2];pad=30
    im=Image.new('RGBA',(w+pad*2,int(size*1.5)),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rectangle((0,0,im.width,im.height),fill=bg);d.text((pad,int(size*0.12)),text,font=f,fill=fg)
    return im.rotate(rot,expand=True,resample=Image.BICUBIC)
def stamp(l1,l2,rot):
    ink=(43,69,196);w,h=620,260
    im=Image.new('RGBA',(w,h),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rounded_rectangle((0,0,w,h),radius=40,fill=(246,240,226,235))
    for k in range(3):d.rounded_rectangle((8+k*4,8+k*4,w-8-k*4,h-8-k*4),radius=36,outline=ink+(255,),width=5 if k!=1 else 2)
    f1=ImageFont.truetype(AN,100);f2=ImageFont.truetype(AN,58)
    d.text((w/2,h*0.40),l1,font=f1,fill=ink+(255,),anchor='mm');d.text((w/2,h*0.76),l2,font=f2,fill=ink+(255,),anchor='mm')
    # textura de carimbo: falhas na tinta
    rng=np.random.default_rng(len(l1));a=np.array(im)
    ink_px=(a[...,2]>150)&(a[...,0]<120);holes=(rng.random((h,w))<0.14)&ink_px;a[holes]=[246,240,226,235]
    im=Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.6))
    bgc=Image.new('RGBA',(w,h),(255,255,255,0));return im.rotate(rot,expand=True,resample=Image.BICUBIC)
def plane(scale=1.0):
    s=180;im=Image.new('RGBA',(s*2,s),(0,0,0,0));d=ImageDraw.Draw(im)
    # avião de papel visto de lado, apontando para a direita
    P=lambda pts:[(x*s/100,y*s/100) for x,y in pts]
    d.polygon(P([(0,40),(195,48),(60,58)]),fill=(250,250,248,255))
    d.polygon(P([(60,58),(195,48),(70,80)]),fill=(214,214,210,255))
    d.polygon(P([(0,40),(60,58),(40,62)]),fill=(190,190,186,255))
    d.line(P([(0,40),(195,48),(70,80),(60,58),(195,48)]),fill=(60,60,60,255),width=3)
    sh=Image.new('RGBA',im.size,(0,0,0,0));sh.paste((0,0,0,90),(0,0),im);sh=sh.filter(ImageFilter.GaussianBlur(8))
    o=Image.new('RGBA',(im.width+20,im.height+30),(0,0,0,0));o.alpha_composite(sh,(14,24));o.alpha_composite(im,(0,0))
    return o.resize((int(o.width*scale),int(o.height*scale)),Image.LANCZOS)
PL=plane(1.9)
ease=lambda u:u*u*(3-2*u)
EV=[]
# (inicio, fim, função que desenha no quadro)
def add_tape(t0,t1,img,x,y):EV.append((t0,t1,'tape',img,x,y))
def add_stamp(t0,t1,img,x,y):EV.append((t0,t1,'stamp',img,x,y))
add_tape(0.0,2.6,tape('RIFA PRO FLAVINHO VIAJAR',62,-2),None,330)

add_tape(mt(29.6),mt(32.8),tape('TRIP MASTER',78,3),None,330)
add_stamp(mt(35.6),mt(41.4),stamp('ISRAEL','2027 · 1º SEMESTRE',-8),None,300)
add_stamp(mt(47.9),mt(53.0),stamp('???','2027 · 2º SEMESTRE',6),None,300)
add_stamp(mt(54.4),mt(60.6),stamp('ARGENTINA','2027 · 2º SEMESTRE',-5),None,300)
add_stamp(mt(60.9),mt(65.5),stamp('EUA','2028 · A VOLTA',7),None,300)
tm=mt(28.6);EV.append((tm,tm+2.8,'plane',PL,0,0))
add_stamp(mt(68.8),mt(72.3),stamp('TEXAS','DEU PT',-6),None,300)
add_tape(mt(75.1),mt(77.3),tape('MIDAS ÀS AVESSAS',70,-3),None,520)
src=subprocess.Popen(['ffmpeg','-v','error','-i','cat.mov','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
dst=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i','cat.mov','-map','0:v','-map','1:a','-vf','ass=post.ass:fontsdir=fonts,format=yuv420p','-c:v','libx264','-crf','19','-preset','medium','-c:a','aac','-b:a','160k','-af','loudnorm=I=-14:TP=-1.5','-movflags','+faststart','post-2026-11-05-humor.mp4'],stdin=subprocess.PIPE)
n=0;sz=W*H*3
while True:
    buf=src.stdout.read(sz)
    if len(buf)<sz:break
    t=n/FPS;n+=1
    act=[e for e in EV if e[0]<=t<e[1]]
    if not act:dst.stdin.write(buf);continue
    fr=Image.frombytes('RGB',(W,H),buf).convert('RGBA')
    for t0,t1,k,img,x,y in act:
        u=t-t0;dur=t1-t0
        if k=='plane':
            p=u/dur;e=ease(p);px=-PL.width+(W+PL.width*1.3)*e;py=1250-520*math.sin(math.pi*p)+40*math.sin(6*p)
            ang=-math.degrees(math.atan2(-360*math.pi*math.cos(math.pi*p),(W+PL.width*1.3)))*0.5
            im=PL.rotate(ang,expand=True,resample=Image.BICUBIC)
            # rastro tracejado
            d=ImageDraw.Draw(fr)
            for j in range(1,22,2):
                q=max(0,p-j*0.012);ee=ease(q);qx=-PL.width+(W+PL.width*1.3)*ee+20;qy=1250-520*math.sin(math.pi*q)+40*math.sin(6*q)+PL.height*0.45
                d.ellipse((qx-4,qy-4,qx+4,qy+4),fill=(255,255,255,170))
            fr.alpha_composite(im,(int(px),int(py)));continue
        # entrada: tape desliza/cresce; carimbo bate (escala 1.5->1 com tremida)
        a=min(1,u/0.18)*min(1,(dur-u)/0.18)
        if k=='stamp':
            sc=1.0+0.5*max(0,1-u/0.16)**2;jx=int(6*math.sin(u*80)*max(0,1-u/0.3))
        else:
            sc=0.85+0.15*ease(min(1,u/0.2));jx=0
        im=img.resize((max(1,int(img.width*sc)),max(1,int(img.height*sc))),Image.BICUBIC)
        if a<1:al=im.split()[3].point(lambda v:int(v*a));im.putalpha(al)
        xx=(W-im.width)//2+jx if x is None else x;fr.alpha_composite(im,(xx,y-im.height//2))
    dst.stdin.write(fr.convert('RGB').tobytes())
dst.stdin.close();dst.wait();print('frames',n)
