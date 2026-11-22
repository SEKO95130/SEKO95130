import numpy as np, subprocess
from scipy.signal import correlate
SR=16000; HOP=160
def env(p):
    r=subprocess.run(["ffmpeg","-loglevel","error","-i",p,"-map","0:a:0","-ac","1","-ar",str(SR),"-af","highpass=f=200,lowpass=f=3500","-f","f32le","-"],capture_output=True)
    x=np.frombuffer(r.stdout,np.float32)
    n=len(x)//HOP; e=np.log(np.sqrt((x[:n*HOP].reshape(n,HOP)**2).mean(1))+1e-4)
    e=e-np.convolve(e,np.ones(50)/50,"same")  # remove slow trend
    return (e-e.mean())/(e.std()+1e-9)
for v,f in [("cyril","/home/user/work/sep/htdemucs/Cyril_interview_44/vocals.wav"),("coach","/home/user/work/sep/htdemucs/Coach_cergy_44/vocals.wav"),("geoffroy","/home/user/work/sep/htdemucs/Geoffroy_interwiew_44/vocals.wav")]:
    a=env(f"/home/user/work/voix/{v}.m4a"); b=env(f)
    c=correlate(b,a,"full")/min(len(a),len(b)); k=np.argmax(c); lag=(k-(len(a)-1))*HOP/SR
    top=np.sort(c)[-5:]
    print(v,f"lag {lag:+.2f}s peak {c[k]:.3f} median {np.median(np.abs(c)):.3f}")
a=env("/home/user/work/voix/cyril.m4a"); b=env("/home/user/work/sep/htdemucs/Cyril_interview_44/vocals.wav")
fps=SR/HOP
for s in range(6,26,4):
    seg=a[int(s*fps):int((s+5)*fps)]
    c=correlate(b,seg,"valid")/len(seg); k=np.argmax(c)
    print(s, f"{k/fps - s:+.2f} {c[k]:.2f}")
