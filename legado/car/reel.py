import subprocess,random,importlib.util
spec=importlib.util.spec_from_file_location('p','postit.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
V31='../v31/post-2026-10-31.mp4';V30='../v30/post-2026-10-30.mp4';V30N='../v30n/post-pensando.mp4'
Y='#F6C41A';B='#141414'
C=[('slide01r.jpg',Y,[(V31,0.0,1.25,'Pera aí, pera aí, não passa não.')]),
   ('slide02.jpg',B,[('voz.mp3',0.78,5.92,'Parece que são mundos diferentes, mas todas falam da mesma coisa: como a gente vive junto.')]),
   ('slide03.jpg',Y,[(V31,59.2,68.5,'Nunca se esqueçam: política se discute sim, e não é só de quatro em quatro anos. Política se discute todo dia.')]),
   ('slide04.jpg',B,[(V31,33.5,39.0,'Eles deram voz a quem não tinha. Eles fizeram pessoas vir participar.')]),
   ('slide05.jpg',Y,[(V30,77.4,81.6,'Aonde tá o amor? Aonde tá a compreensão disso?')]),
   ('slide06.jpg',B,[('voz.mp3',10.40,15.45,'E a sociedade é onde tudo isso se encontra, no trabalho, na família, no grupo do zap.')]),
   ('slide07.jpg',Y,[(V30,81.55,84.5,'Cara, é momento de união, reunir forças.')]),
   ('slide08.jpg',B,[(V30,118.25,120.8,'Não é time, é uma luta.'),(V31,78.8,82.85,'Ah, e não vamo deixar nem o café e nem a nossa luta esfriar. Bora.')])]
parts=[]
for k,(img,bg,clips) in enumerate(C):
    # áudio da tela
    alist=[];t=0.15;chunks=[]
    for j,(src,a,b,txt) in enumerate(clips):
        fn=f'ra_{k}_{j}.wav';subprocess.run(['ffmpeg','-v','error','-y','-ss',str(a),'-t',str(b-a),'-i',src,'-vn','-ac','1','-ar','48000','-af','highpass=f=80,loudnorm=I=-16:TP=-1.5,afade=t=in:d=0.03,afade=t=out:st=%.2f:d=0.05'%(b-a-0.06),fn],check=True)
        alist.append(fn);d=b-a
        ws=txt.lower().split();n=len(ws);i=0;tt=t
        while i<n:
            kk=min(3,n-i);dur=d*kk/n;chunks.append((tt,tt+dur,[w.strip(',.:?') for w in ws[i:i+kk]]));tt+=dur;i+=kk
        t+=d+0.15
    D=t+0.35
    random.seed(k)
    ev=p.events(chunks,y=1185);full=p.HEAD+'\n'.join(ev)+'\n'
    if bg==Y: full=full.replace('Style: P,Inter Medium,56,&H00121212,&H00121212,&H001AC4F6,&H001AC4F6','Style: P,Inter Medium,56,&H00F4FAFC,&H00F4FAFC,&H00141414,&H00141414')
    open(f'r{k}.ass','w').write(full)
    # concatena áudios com pausas
    inputs=[];flt=''
    for j,fn in enumerate(alist): inputs+=['-i',fn]
    pre=0.15
    flt=''.join(f'[{j}:a]adelay={int((0.15 if j==0 else 0.15)*1000)}|{int(0.15*1000)}[a{j}];' for j in range(len(alist)))
    flt+=''.join(f'[a{j}]' for j in range(len(alist)))+f'concat=n={len(alist)}:v=0:a=1,apad=whole_dur={D:.2f}[aa]'
    subprocess.run(['ffmpeg','-v','error','-y']+inputs+['-filter_complex',flt,'-map','[aa]','-t',f'{D:.2f}',f'rA_{k}.wav'],check=True)
    vf=f"[0:v]scale=1080:1350,zoompan=z='min(zoom+0.0007,1.07)':d=1:s=1080x1350:fps=30[sl];color=c={bg}:s=1080x1920:r=30:d={D:.2f}[bg];[bg][sl]overlay=0:285:shortest=1,ass=r{k}.ass:fontsdir=fonts,format=yuv420p[v]"
    subprocess.run(['ffmpeg','-v','error','-y','-loop','1','-t',f'{D:.2f}','-i',img,'-i',f'rA_{k}.wav','-filter_complex',vf,'-map','[v]','-map','1:a','-t',f'{D:.2f}','-c:v','libx264','-preset','veryfast','-crf','18','-c:a','pcm_s16le','-ar','48000',f'rp_{k}.mov'],check=True)
    parts.append(f"file 'rp_{k}.mov'");print(k,round(D,1))
open('rlist.txt','w').write('\n'.join(parts)+'\n')
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i','rlist.txt','-af','loudnorm=I=-14:TP=-1.5:LRA=11','-c:v','libx264','-preset','medium','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-ar','48000','-movflags','+faststart','reel-carrossel.mp4'],check=True)
