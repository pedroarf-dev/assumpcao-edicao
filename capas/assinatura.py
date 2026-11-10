import math, subprocess, os
import numpy as np
from PIL import Image,ImageOps,ImageFilter,ImageDraw
src='/mnt/user-data/uploads/Projetos Claude/Pedro Assumpção/Videos/01 Brutos/PXL_20261110_143542641.PORTRAIT.jpg'
im=ImageOps.exif_transpose(Image.open(src)).convert('L').crop((600,1250,2450,2900)).resize((740,660),Image.LANCZOS)
bg=im.filter(ImageFilter.GaussianBlur(120)); a=np.array(im,float); b=np.array(bg,float)
ink=((b-a)>30).astype('uint8')*255
mask=Image.fromarray(ink).filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7)).filter(ImageFilter.MedianFilter(7)).filter(ImageFilter.GaussianBlur(1.2))
mask.save('ink.png')
path=[(105,510),(108,300),(110,135),(140,108),(200,215),(265,322),(320,215),(370,115),(420,210),(470,302),(530,200),(590,105),(600,330),(615,560),(675,545),(470,568),(255,588)]
def dens(p,step=2):
    o=[]
    for (x0,y0),(x1,y1) in zip(p,p[1:]):
        n=max(1,int(math.hypot(x1-x0,y1-y0)/step)); o+=[(x0+(x1-x0)*i/n,y0+(y1-y0)*i/n) for i in range(n)]
    return o+[p[-1]]
P=dens(path); N=len(P)
COL={'laranja':(232,112,52),'branco':(245,245,242),'preto':(20,20,22)}
FPS=30; DUR=1.1; HOLD=0.6; frames=int((DUR+HOLD)*FPS)
os.makedirs('fr',exist_ok=True)
def ease(t): return 1-(1-t)**2.2
for cor,rgb in COL.items():
    for f in range(frames):
        t=min(1,f/(DUR*FPS)); k=max(2,int(ease(t)*N))
        rv=Image.new('L',(740,660),0); d=ImageDraw.Draw(rv)
        for x,y in P[:k]: d.ellipse((x-38,y-38,x+38,y+38),fill=255)
        al=Image.fromarray((np.array(mask,float)*np.array(rv,float)/255).astype('uint8'))
        fr=Image.new('RGBA',(740,660),rgb+(0,)); fr.putalpha(al); fr=fr.resize((370,330),Image.LANCZOS); fr.save(f'fr/{cor}_{f:03d}.png')
    subprocess.run(['ffmpeg','-v','error','-y','-framerate',str(FPS),'-i',f'fr/{cor}_%03d.png','-c:v','prores_ks','-profile:v','4444','-pix_fmt','yuva444p10le',f'assinatura-{cor}.mov'],check=True)
    subprocess.run(['ffmpeg','-v','error','-y','-framerate',str(FPS),'-i',f'fr/{cor}_%03d.png','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','1M',f'assinatura-{cor}.webm'],check=True)
    Image.open(f'fr/{cor}_{frames-1:03d}.png').save(f'assinatura-{cor}.png')
