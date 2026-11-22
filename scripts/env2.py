import numpy as np, glob
from scipy.signal import correlate
exec(open('/home/user/work/scripts/env.py').read().split('for v,f in')[0])
a=env("/home/user/work/voix/cyril.m4a")
for f in sorted(glob.glob("/home/user/work/sep/htdemucs/*/vocals.wav")):
    b=env(f); fps=SR/HOP; r=[]
    for s in (7,12,17,22):
        seg=a[int(s*fps):int((s+5)*fps)]
        if len(b)<=len(seg): continue
        c=correlate(b,seg,"valid")/len(seg); k=np.argmax(c); r.append(f"{k/fps-s:+.1f}({c[k]:.2f})")
    print(f.split('/')[-2], r)
