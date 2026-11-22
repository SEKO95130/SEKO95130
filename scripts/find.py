import numpy as np, glob, sys
sys.path.insert(0,'/home/user/work/scripts')
from scipy.signal import correlate
exec(open('/home/user/work/scripts/sync.py').read().split('pairs=')[0])
a=load("/home/user/work/voix/cyril.m4a")
for f in sorted(glob.glob("/home/user/work/A-roll/*.MOV")):
    b=load(f)
    res=[]
    for s in (7,13,18):
        seg=a[int(s*SR):int((s+4)*SR)]
        if len(b)<len(seg): continue
        c=correlate(b,seg,mode="valid",method="fft")
        e=np.sqrt(np.convolve(b**2,np.ones(len(seg)),"valid")*np.sum(seg**2))+1e-9
        n=np.abs(c)/e;k=np.argmax(n);res.append(f"{k/SR-s:+.2f}({n[k]:.2f})")
    print(f.split('/')[-1],res)
