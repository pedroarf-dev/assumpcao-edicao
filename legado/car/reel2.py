import subprocess,random,importlib.util,os
from PIL import Image,ImageOps
spec=importlib.util.spec_from_file_location('p','postit.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
Y='#F6C41A';B='#141414';VO='vo.mp3'
S=[('slide01r.jpg',Y,[(1.40,7.70,'Pera aí, não passa não. Política, arte, psicanálise e sociedade. O que que elas têm em comum?')]),
   ('slide02.jpg',B,[(9.30,14.75,'Parece que são mundos diferentes, mas todas falam da mesma coisa: como a gente vive junto.')]),
   ('slide03.jpg',Y,[(19.60,22.15,'A política decide as regras dessa convivência.'),(22.95,28.70,'Quem come, quem estuda, quem é ouvido. E não é só de quatro em quatro anos, é todo dia.')]),
   ('slide04.jpg',B,[(36.45,42.60,'A arte dá forma ao que a gente sente e ainda não sabe dizer. Ela dá voz a quem achava que não tinha.')]),
   ('slide05.jpg',Y,[(50.00,57.35,'A psicanálise escuta o que não é dito, o medo, o ódio, o desejo que move as nossas escolhas, inclusive o voto.')]),
   ('slide06.jpg',B,[(58.45,63.75,'E a sociedade é onde tudo se encontra, no trabalho, na família, no grupo de WhatsApp.')]),
   ('slide07.jpg',Y,[(64.55,66.50,'Separadas, elas enfraquecem.')]),
   ('slide08.jpg',B,[(94.35,100.15,'Juntas, viram voz. E você, qual dessas te move mais? Me conta aí e bora marcar um café.'),(100.65,102.20,'E não vamo deixar a luta esfriar não, hein?')])]
GAP=0.25
def still(img,bg,out):
    c=bg.lstrip('#');col=tuple(int(c[i:i+2],16) for i in (0,2,4))
    b=Image.new('RGB',(1080,1920),col);b.paste(Image.open(img).convert('RGB').resize((1080,1350)),(0,285));b.save(out,quality=95)
parts=[]
for k,(img,bg,clips) in enumerate(S):
    still(img,bg,f'st_{k}.jpg')
    t=0.2;chunks=[];alist=[]
    for j,(a,b,txt) in enumerate(clips):
        fn=f'vo_{k}_{j}.wav';d=b-a
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(a),'-t',str(d),'-i',VO,'-ac','1','-ar','48000','-af','highpass=f=80,afade=t=in:d=0.03,afade=t=out:st=%.2f:d=0.06'%(d-0.07),fn],check=True)
        alist.append(fn)
        ws=txt.lower().split();n=len(ws);i=0;tt=t
        while i<n:
            kk=min(3,n-i)
            for q in range(1,kk+1):
                if ws[i+q-1][-1] in ',.?:' and q<kk: kk=q;break
            dur=d*kk/n;chunks.append((tt,tt+dur,[w.strip(',.:?') for w in ws[i:i+kk]]));tt+=dur;i+=kk
        t+=d+GAP
    D=t+0.25
    random.seed(k);full=p.HEAD+'\n'.join(p.events(chunks,y=1185))+'\n'
    if bg==Y: full=full.replace('Style: P,Inter Medium,56,&H00121212,&H00121212,&H001AC4F6,&H001AC4F6','Style: P,Inter Medium,56,&H00F4FAFC,&H00F4FAFC,&H00141414,&H00141414')
    open(f'v{k}.ass','w').write(full)
    inp=[];fl=''
    for j,fn in enumerate(alist): inp+=['-i',fn];fl+=f'[{j}:a]adelay={int((0.2 if j==0 else GAP)*1000)}[a{j}];'
    fl+=''.join(f'[a{j}]' for j in range(len(alist)))+f'concat=n={len(alist)}:v=0:a=1,apad=whole_dur={D:.2f}[aa]'
    subprocess.run(['ffmpeg','-v','error','-y']+inp+['-filter_complex',fl,'-map','[aa]','-t',f'{D:.2f}',f'vA_{k}.wav'],check=True)
    vf=f"[0:v]scale=1080:1350,zoompan=z='min(zoom+0.0006,1.06)':d=1:s=1080x1350:fps=30[sl];color=c={bg}:s=1080x1920:r=30:d={D:.2f}[bgc];[bgc][sl]overlay=0:285:shortest=1,ass=v{k}.ass:fontsdir=fonts,format=yuv420p[v]"
    subprocess.run(['ffmpeg','-v','error','-y','-loop','1','-t',f'{D:.2f}','-i',img,'-i',f'vA_{k}.wav','-filter_complex',vf,'-map','[v]','-map','1:a','-t',f'{D:.2f}','-c:v','libx264','-preset','veryfast','-crf','18','-c:a','pcm_s16le','-ar','48000',f'vp_{k}.mov'],check=True)
    print(k,round(D,1));parts.append(f'vp_{k}.mov')
# gromelôs: dissolve do slide -> obra (zoom lento) -> próximo slide
def fit(src,out):
    im=ImageOps.exif_transpose(Image.open(src)).convert('RGB');im=ImageOps.fit(im,(1080,1920),Image.LANCZOS,centering=(0.5,0.45));im.save(out,quality=95)
def trans(prev,art,nxt,out,hold=1.6,f=0.45):
    D=f+hold+f
    fc=(f"[1:v]scale=1188:2112,zoompan=z='min(zoom+0.0009,1.1)':d=1:s=1080x1920:fps=30,trim=duration={D},setpts=PTS-STARTPTS,format=yuv420p[g];"
        f"[0:v]fps=30,format=yuv420p,trim=duration={D}[p];[2:v]fps=30,format=yuv420p,trim=duration={D}[n];"
        f"[p][g]xfade=transition=fade:duration={f}:offset=0.01[pg];[pg][n]xfade=transition=fade:duration={f}:offset={f+hold:.2f},trim=duration={D}[v]")
    subprocess.run(['ffmpeg','-v','error','-y','-loop','1','-t',str(D+1),'-i',prev,'-loop','1','-t',str(D+1),'-i',art,'-loop','1','-t',str(D+1),'-i',nxt,'-f','lavfi','-t',str(D),'-i','anullsrc=r=48000:cl=mono','-filter_complex',fc,'-map','[v]','-map','3:a','-t',str(D),'-c:v','libx264','-preset','veryfast','-crf','18','-c:a','pcm_s16le','-ar','48000',out],check=True)
for i in (1,2,3): fit(f'grom/n{i}.jpg',f'gf{i}.jpg')
trans('st_0.jpg','gf1.jpg','st_1.jpg','gt1.mov')
trans('st_3.jpg','gf2.jpg','st_4.jpg','gt2.mov')
trans('st_4.jpg','gf3.jpg','st_5.jpg','gt3.mov')
# fechamento: bicicleta em panorâmica + tag
im=Image.open('grom/n4.jpg').convert('RGB');h=1920;w=int(im.width*h/im.height);im.resize((w,h),Image.LANCZOS).save('bike.jpg',quality=95)
ns={};src=open('../cap/capa7.py').read();i=src.index('def add_tag');j=src.index('\nif cfg',i)
os.chdir('../cap');exec(src[i:j],ns)
tag=Image.new('RGB',(700,200),(0,0,0));ns['add_tag'](tag,20,40,size=60);os.chdir('../car')
tag.save('tagonly.png')
# tag com fundo transparente: recria com máscara pela cor preta
tg=Image.open('tagonly.png').convert('RGBA');px=tg.load()
for yy in range(tg.height):
    for xx in range(tg.width):
        r,g,b,a=px[xx,yy]
        if r<8 and g<8 and b<8: px[xx,yy]=(0,0,0,0)
tg.save('tag.png')
D=3.6;f=0.45
fc=(f"[1:v]crop=1080:1920:'(iw-1080)*min(t/{D-0.6},1)':0,fps=30,format=yuv420p,trim=duration={D}[bk];"
    f"[0:v]fps=30,format=yuv420p,trim=duration={D}[p];[p][bk]xfade=transition=fade:duration={f}:offset=0.01[pb];"
    f"[2:v]format=rgba,fade=t=in:st={D-1.4}:d=0.4:alpha=1[tg];[pb][tg]overlay=(W-w)/2:1560:enable='gte(t,{D-1.4})',trim=duration={D}[v]")
subprocess.run(['ffmpeg','-v','error','-y','-loop','1','-t',str(D+1),'-i','st_7.jpg','-loop','1','-t',str(D+1),'-i','bike.jpg','-loop','1','-t',str(D+1),'-i','tag.png','-f','lavfi','-t',str(D),'-i','anullsrc=r=48000:cl=mono','-filter_complex',fc,'-map','[v]','-map','3:a','-t',str(D),'-c:v','libx264','-preset','veryfast','-crf','18','-c:a','pcm_s16le','-ar','48000','gt4.mov'],check=True)
order=['vp_0.mov','gt1.mov','vp_1.mov','vp_2.mov','vp_3.mov','gt2.mov','vp_4.mov','gt3.mov','vp_5.mov','vp_6.mov','vp_7.mov','gt4.mov']
open('vlist.txt','w').write('\n'.join(f"file '{o}'" for o in order)+'\n')
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i','vlist.txt','-af','loudnorm=I=-14:TP=-1.5:LRA=11','-c:v','libx264','-preset','medium','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-ar','48000','-movflags','+faststart','reel-carrossel-v2.mp4'],check=True)
