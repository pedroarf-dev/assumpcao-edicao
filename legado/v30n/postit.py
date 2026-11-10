# gera eventos ASS com cada palavra numa caixinha amarela (post-it), 2-3 palavras por tela
from PIL import ImageFont
import random
F=ImageFont.truetype('fonts/InterMedium.ttf',39)
HEAD="""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: P,Inter Medium,56,&H00121212,&H00121212,&H001AC4F6,&H001AC4F6,0,0,0,0,100,100,0,0,3,7,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
def f(x):h=int(x//3600);m=int(x%3600//60);s=x%60;return f"{h}:{m:02d}:{s:05.2f}"
def events(chunks,y=330,gap=19):
    """chunks: list of (start,end,[words])"""
    out=[]
    for s,e,ws in chunks:
        widths=[F.getlength(w) for w in ws];tot=sum(widths)+gap*(len(ws)-1)
        if tot>560:  # quebra em 2 linhas
            half=len(ws)//2 or 1;lines=[ws[:half],ws[half:]]
        else: lines=[ws]
        for li,line in enumerate(lines):
            wl=[F.getlength(w) for w in line];t=sum(wl)+gap*(len(line)-1);x=360-t/2
            for w,ww in zip(line,wl):
                r=random.uniform(-2.5,2.5)
                out.append(f"Dialogue: 0,{f(s)},{f(e)},P,,0,0,0,,{{\\an5\\pos({x+ww/2:.0f},{y+li*84})\\frz{r:.1f}}}{w}")
                x+=ww+gap
    return out
if __name__=='__main__':
    random.seed(2)
    open('postit.ass','w').write(HEAD+'\n'.join(events([(0,5,'mesmo perdendo, quer'.split())]))+'\n')
