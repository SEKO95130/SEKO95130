import numpy as np, subprocess, sys
from scipy.signal import correlate, butter, sosfilt
SR=8000
def load(p):
    r=subprocess.run(["ffmpeg","-loglevel","error","-i",p,"-map","0:a:0","-ac","1","-ar",str(SR),"-f","f32le","-"],capture_output=True)
    x=np.frombuffer(r.stdout,np.float32).astype(float)
    x=sosfilt(butter(4,[200,3000],"band",fs=SR,output="sos"),x)
    return x
pairs=[("cyril","Cyril interview"),("geoffroy","Geoffroy interwiew"),("marwin","Marwin interview"),("coach","Coach cergy"),("dan","Dan")]
for v,m in pairs:
    a=load(f"/home/user/work/voix/{v}.m4a"); b=load(f"/home/user/work/A-roll/{m}.MOV")
    c=correlate(b,a,mode="full",method="fft")
    na=np.sqrt(np.sum(a**2)*np.sum(b**2))
    k=np.argmax(np.abs(c)); lag=(k-(len(a)-1))/SR
    # lag>0: voice t=0 corresponds to video t=lag
    print(f"{v}: voice_t0 = video_t {lag:+.3f}s  score={abs(c[k])/na:.3f}  voice={len(a)/SR:.1f}s video={len(b)/SR:.1f}s")
print("--- windowed check")
for v,m in pairs:
    a=load(f"/home/user/work/voix/{v}.m4a"); b=load(f"/home/user/work/A-roll/{m}.MOV")
    out=[]
    for s in np.arange(0,len(a)/SR-4,3):
        seg=a[int(s*SR):int((s+4)*SR)]
        c=correlate(b,seg,mode="valid",method="fft")
        e=np.sqrt(np.convolve(b**2,np.ones(len(seg)),"valid")*np.sum(seg**2))+1e-9
        n=np.abs(c)/e; k=np.argmax(n)
        out.append(f"{s:.0f}->{k/SR - s:+.2f}({n[k]:.2f})")
    print(v," ".join(out))
