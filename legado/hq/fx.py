import cv2,numpy as np,subprocess,sys
W,H=1080,1920
cap=cv2.VideoCapture('src.mp4');frames=[]
while True:
    ok,f=cap.read()
    if not ok:break
    frames.append(f)
rng=np.random.default_rng(3)
paper=(np.full((H,W,3),(232,240,246),np.uint8)).astype(np.float32)
noise=cv2.GaussianBlur(rng.normal(0,9,(H,W)).astype(np.float32),(0,0),2.5)
paper=np.clip(paper+noise[...,None],0,255).astype(np.uint8)
Y=np.array([26,196,246],np.float32);K=np.array([20,20,20],np.float32);Wt=np.array([238,244,246],np.float32)
yy,xx=np.mgrid[0:H,0:W]
def dots(g,cell=10):
    # halftone: circles radius by darkness
    cy=(yy%cell)-cell/2;cx=(xx%cell)-cell/2;d=np.sqrt(cx*cx+cy*cy)
    gs=cv2.resize(cv2.resize(g,(W//cell,H//cell),interpolation=cv2.INTER_AREA),(W,H),interpolation=cv2.INTER_NEAREST)
    r=(1-gs/255.0)*cell*0.62
    return d<r
def hq(f):
    s=f
    for _ in range(2):s=cv2.bilateralFilter(s,9,60,60)
    g=cv2.cvtColor(s,cv2.COLOR_BGR2GRAY)
    e=cv2.adaptiveThreshold(cv2.medianBlur(g,7),255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,4)
    # 3 tons: preto, amarelo (meio), branco
    out=np.empty_like(f,dtype=np.float32)
    out[:]=Wt;out[g<170]=Y;out[g<85]=K
    hd=dots(g.astype(np.float32),11)&(g<170)&(g>=85)
    out[hd]=out[hd]*0.55
    out[e==0]=K
    return out.astype(np.uint8)
def sketch(f,i):
    g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
    inv=255-g;bl=cv2.GaussianBlur(inv,(0,0),3+ (i%2))
    sk=cv2.divide(g,255-bl,scale=256)
    sk=np.clip((sk.astype(np.float32)-150)*2.6,0,255)
    # traço tremido (boiling): pequeno deslocamento por pose
    M=np.float32([[1,0,rng.normal(0,1.5)],[0,1,rng.normal(0,1.5)]])
    sk=cv2.warpAffine(sk,M,(W,H),borderMode=cv2.BORDER_REPLICATE)
    col=cv2.resize(cv2.resize(f,(W//24,H//24),interpolation=cv2.INTER_AREA),(W,H),interpolation=cv2.INTER_CUBIC).astype(np.float32)
    hsv=cv2.cvtColor(col.astype(np.uint8),cv2.COLOR_BGR2HSV).astype(np.float32);hsv[...,1]=np.clip(hsv[...,1]*1.8,0,255);col=cv2.cvtColor(hsv.astype(np.uint8),cv2.COLOR_HSV2BGR).astype(np.float32)
    base=paper.astype(np.float32)*0.72+col*0.28
    return np.clip(base*(sk[...,None]/255.0),0,255).astype(np.uint8)
mode=sys.argv[1]
p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-crf','18','-preset','veryfast','-pix_fmt','yuv420p',f'{mode}.mp4'],stdin=subprocess.PIPE)
hold=None
for i,f in enumerate(frames):
    if mode=='hq': o=hq(f) if i%2==0 or hold is None else hold   # 15 qps: cara de HQ animada
    else: o=sketch(f,i//3) if i%3==0 or hold is None else hold     # 10 qps: cara de desenho à mão
    hold=o;p.stdin.write(o.tobytes())
p.stdin.close();p.wait()
