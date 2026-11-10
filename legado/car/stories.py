import subprocess,random,importlib.util
spec=importlib.util.spec_from_file_location('p','postit.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
SRC='../v31/post-2026-10-31.mp4'
S=[('story-car-1.mp4','slide01.jpg','#F6C41A',0.0,1.25,4.5,'Pera aí, pera aí, não passa não.','NOVO POST NO PERFIL'),
   ('story-car-2.mp4','slide04.jpg','#141414',33.5,39.0,0,'Eles deram voz a quem não tinha. Eles fizeram pessoas vir participar.','ARRASTA O POST PRO LADO'),
   ('story-car-3.mp4','slide03.jpg','#F6C41A',59.2,68.5,0,'Nunca se esqueçam: política se discute sim, e não é só de quatro em quatro anos. Política se discute todo dia.','TEM MAIS NO PERFIL')]
for out,img,bg,a,b,hold,txt,tag in S:
    d=b-a;D=max(d+0.6,hold)
    ws=txt.lower().split();n=len(ws);chunks=[];i=0;t=0.15
    while i<n:
        k=min(3,n-i);dur=d*k/n;chunks.append((t,t+dur,[w.strip(',.:') for w in ws[i:i+k]]));t+=dur;i+=k
    random.seed(1)
    ev=p.events(chunks,y=1185)
    head=p.HEAD.replace('[Events]','Style: T,Lilita One,40,&H00121212,&H00FFFFFF,&H001AC4F6,&H001AC4F6,0,0,0,0,100,100,1,-2,3,12,0,8,50,50,95,1\n\n[Events]')
    ev.append(f"Dialogue: 1,0:00:00.00,0:01:00.00,T,,0,0,0,,{{\\fad(200,0)}}{tag}")
    full=head+'\n'.join(ev)+'\n'
    if bg=='#F6C41A':
        full=full.replace('Style: P,Inter Medium,56,&H00121212,&H00121212,&H001AC4F6,&H001AC4F6','Style: P,Inter Medium,56,&H00F4FAFC,&H00F4FAFC,&H00141414,&H00141414')
        full=full.replace('Style: T,Lilita One,40,&H00121212,&H00FFFFFF,&H001AC4F6,&H001AC4F6','Style: T,Lilita One,40,&H001AC4F6,&H00FFFFFF,&H00141414,&H00141414')
    open('st.ass','w').write(full)
    vf=f"[1:v]scale=1080:1350,zoompan=z='min(zoom+0.0006,1.06)':d=1:s=1080x1350:fps=30[sl];color=c={bg}:s=1080x1920:r=30:d={D:.2f}[bg];[bg][sl]overlay=0:285:shortest=1,ass=st.ass:fontsdir=fonts[v]"
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(a),'-t',str(d),'-i',SRC,'-loop','1','-t',f'{D:.2f}','-i',img,'-filter_complex',vf+f";[0:a]apad=whole_dur={D:.2f},afade=t=out:st={D-0.3:.2f}:d=0.3[aa]",'-map','[v]','-map','[aa]','-t',f'{D:.2f}','-c:v','libx264','-preset','medium','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',out],check=True)
    print(out,round(D,1))
