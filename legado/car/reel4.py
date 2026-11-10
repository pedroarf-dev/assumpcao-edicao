import subprocess,random,importlib.util,os
from PIL import Image,ImageOps
spec=importlib.util.spec_from_file_location('p','postit.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
Y='#F6C41A';B='#141414';VO='vo.mp3'
V2='varios.mp3'
S=[('vslide01.jpg',Y,[(VO,1.40,6.52,'Pera aí, não passa não. Política, arte, psicanálise e sociedade.'),(V2,10.60,12.10,'O que elas têm em comum?')]),
   ('vslide02.jpg',B,[(VO,9.30,14.75,'Parece que são mundos diferentes, mas todas falam da mesma coisa: como a gente vive junto.')]),
   ('vslide03.jpg',Y,[(VO,19.60,22.15,'A política decide as regras dessa convivência.'),(VO,22.95,28.70,'Quem come, quem estuda, quem é ouvido. E não é só de quatro em quatro anos, é todo dia.')]),
   ('vslide04.jpg',B,[(VO,36.45,42.60,'A arte dá forma ao que a gente sente e ainda não sabe dizer. Ela dá voz a quem achava que não tinha.')]),
   ('vslide05.jpg',Y,[(V2,0.05,8.55,'Então, e a psicanálise? Ela escuta o que não é dito. O medo, o ódio, o desejo, tudo isso que move nossas escolhas, inclusive nosso voto.')]),
   ('vslide06.jpg',B,[(VO,58.45,63.75,'E a sociedade é onde tudo se encontra, no trabalho, na família, no grupo de WhatsApp.')]),
   ('vslide07.jpg',Y,[(V2,13.72,15.80,'Separadas, elas enfraquecem.')]),
   ('vslide08.jpg',B,[(V2,17.42,19.15,'Juntas, viram voz.'),(V2,21.10,23.75,'E você, qual dessas te move mais?'),(V2,24.28,25.30,'Me conta aí.'),(V2,39.88,43.40,'E olha, bora marcar um café e não vamo deixar essa luta esfriar, não.')])]
GAP=0.25
def still(img,bg,out):
    c=bg.lstrip('#');col=tuple(int(c[i:i+2],16) for i in (0,2,4))
    b=Image.new('RGB',(1080,1920),col);b.paste(Image.open(img).convert('RGB').resize((1080,1350)),(0,285));b.save(out,quality=95)
parts=[]
for k,(img,bg,clips) in enumerate(S):
    still(img,bg,f'st_{k}.jpg')
    t=0.2;chunks=[];alist=[]
    for j,(src,a,b,txt) in enumerate(clips):
        fn=f'vo_{k}_{j}.wav';d=b-a
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(a),'-t',str(d),'-i',src,'-ac','1','-ar','48000','-af','highpass=f=80,loudnorm=I=-18:TP=-2:LRA=7,aresample=48000,afade=t=in:d=0.03,afade=t=out:st=%.2f:d=0.06'%(d-0.07),fn],check=True)
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
