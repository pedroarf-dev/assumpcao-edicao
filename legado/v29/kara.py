import sys
OFF=float(sys.argv[1])
def t(s):
    h,m,r=s.split(':');sec,ms=r.split(',');return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
def f(x):
    x=max(0,x);h=int(x//3600);m=int(x%3600//60);s=x%60;return f"{h}:{m:02d}:{s:05.2f}"
Y='{\\c&H0018C5F5&}';W='{\\c&H00FFFFFF&}'
out=["[Script Info]","ScriptType: v4.00+","PlayResX: 720","PlayResY: 1280","WrapStyle: 0","","[V4+ Styles]",
"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
"Style: K,Lato Black,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,5,2,2,60,60,360,1","","[Events]",
"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for line in open('srt.txt'):
    tm,txt=line.rstrip('\n').split('|');a,b=[t(x.strip())-OFF for x in tm.split('-->')]
    ws=txt.split();tot=sum(len(w)+1 for w in ws);cur=a;times=[]
    for w in ws:
        d=(b-a)*(len(w)+1)/tot;times.append((cur,cur+d));cur+=d
    for i in range(0,len(ws),4):
        ch=ws[i:i+4]
        for j,w in enumerate(ch):
            s,e=times[i+j]
            txt2=' '.join((Y+x+W) if k==j else x for k,x in enumerate(ch))
            out.append(f"Dialogue: 0,{f(s)},{f(e)},K,,0,0,0,,{txt2}")
open('karaoke.ass','w').write('\n'.join(out)+'\n')
