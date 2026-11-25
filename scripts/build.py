"""House of Basketball — Cergy interview edit. Builds shots, audio mix, graphics, final render.
usage: python3 build.py [shots|audio|render-preview|render-final|all-preview]"""
import json, math, os, subprocess, sys, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(__file__))
import timeline as TL

W, H, FPS = 1080, 1920, 30
ROOT = "/home/user/work"
SRC = f"{ROOT}/A-roll"
B = f"{ROOT}/build"
os.makedirs(f"{B}/shots", exist_ok=True)
SR = 48000
GOLD = (212, 152, 43)
WHITE = (255, 255, 255)
F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_XBOLD = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
LOGO = f"{ROOT}/brand/logo_house.png"
DIP = 0.3  # dip-to-black between parts (0.15 out + 0.15 in)
XF = 8  # frames of cross-dissolve between shots inside a part


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(" ".join(cmd)); print(r.stderr[-3000:]); raise SystemExit(1)
    return r


@functools.lru_cache(None)
def probe(src):
    p = f"{SRC}/{src}.MOV"
    j = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,color_transfer,r_frame_rate:stream_side_data=rotation",
                        "-of", "json", p]).stdout)["streams"][0]
    w, h = j["width"], j["height"]
    rot = 0
    for sd in j.get("side_data_list", []):
        rot = sd.get("rotation", 0)
    if abs(rot) == 90:
        w, h = h, w
    return dict(path=p, w=w, h=h, hdr=j.get("color_transfer") == "arib-std-b67")


# ---------------------------------------------------------------- timeline flatten
def nframes(d):
    return int(round(d * FPS))


def build_timeline():
    """returns shots (with absolute start), gfx events (absolute), dialog clips, dips, zones"""
    shots, gfx, dialog, dips, zones = [], [], [], [], []
    t = 0
    zoom_i = {}
    for pi, part in enumerate(TL.PARTS):
        if pi > 0:
            dips.append(t)
        for sh in part:
            sh = dict(sh)
            if sh["kind"] == "dialog":
                who = sh["who"]
                sh["dur"] = sh["vout"] - sh["vin"]
                if "broll" not in sh:
                    k = zoom_i.get(who, 0); zoom_i[who] = k + 1
                    z = TL.ZOOMS[who][k % len(TL.ZOOMS[who])]
                    sh.update(src=TL.RUSH[who], tin=sh["vin"] + TL.OFF[who], zoom=(z, *TL.FACE[who]), anchor=TL.FACE_ANCHOR)
                else:
                    br = sh["broll"]
                    sh.update(src=br["src"], tin=br["tin"], zoom=br.get("zoom"), speed=br.get("speed", 1))
                    if br.get("band"): sh["band"] = br["band"]
                dialog.append(dict(who=who, vin=sh["vin"], vout=sh["vout"], at=t, text=sh["text"]))
                sh["amb"] = -30  # room tone under the voice, smooths the cuts
            elif sh["kind"] == "q":
                who = sh["who"]
                sh.update(src=TL.RUSH[who], tin=max(0.0, sh["bg_t"] + TL.OFF[who]), blur=True,
                          zoom=(1.0, *TL.FACE[who]), amb=-30)
                gfx.append(dict(type="question", t0=t, t1=t + sh["dur"], text=sh["text"]))
            n = nframes(sh["dur"])
            sh["n"] = n
            sh["start"] = t
            for g in sh.get("gfx", []):
                g = dict(g); g["t0"] += t; g["t1"] += t
                gfx.append(g)
            if sh.get("vo"):
                zones.append((t, t + n / FPS))
            sh["part"] = pi
            shots.append(sh)
            t += n / FPS
        part_shots = [x for x in shots if x["part"] == pi]
        for x in part_shots[:-1]:
            x["xf"] = True
    return shots, gfx, dialog, dips, zones, t


# ---------------------------------------------------------------- video shots
TONEMAP = ("zscale=w={w}:h={h}:f=lanczos:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
GRADE = "eq=contrast=1.06:saturation=1.10:brightness=0.005"


def even(x):
    return int(x) // 2 * 2


def shot_filter(sh):
    if sh["kind"] == "black":
        return None
    info = probe(sh["src"])
    sw, shh = info["w"], info["h"]
    if sh.get("band"):
        # landscape footage (phone screen recording): sharp 16:9 band centred on a blurred fill
        x, y, w, h = sh["band"]
        fh = even(W * h / w)
        sp = sh.get("speed", 1)
        return (f"crop={w}:{h}:{x}:{y},fps={FPS},split[a][b];"
                f"[a]scale=-2:{H}:flags=bicubic,crop={W}:{H},gblur=sigma=30,eq=brightness=-0.18:saturation=0.8[bg];"
                f"[b]scale={W}:{fh}:flags=lanczos,unsharp=5:5:0.8,{GRADE}[fg];"
                f"[bg][fg]overlay=0:(H-h)/2,format=yuv420p")
    fc = []
    if sh.get("delogo"):
        x, y, w, h = sh["delogo"]
        fc.append(f"delogo=x={x}:y={y}:w={w}:h={h}")
    z, cx, cy = sh.get("zoom") or (1.0, 0.5, 0.5)
    cw = sw / z; ch = cw * 16 / 9
    if ch > shh:
        ch = shh; cw = ch * 9 / 16
    x = min(max(cx * sw - cw / 2, 0), sw - cw)
    y = min(max(cy * shh - ch * sh.get("anchor", 0.40), 0), shh - ch)
    if z > 1.001 or abs(cw - sw) > 2 or abs(ch - shh) > 2:
        fc.append(f"crop={even(cw)}:{even(ch)}:{even(x)}:{even(y)}")
    if info["hdr"]:
        fc.append(TONEMAP.format(w=W, h=H))
    else:
        fc.append(f"scale={W}:{H}:flags=lanczos,format=yuv420p")
        if sh.get("lowres") or sw < 1000:
            fc.append("unsharp=5:5:0.5")
    sp = sh.get("speed", 1)
    if sp != 1:
        fc.append(f"setpts=PTS/{sp}")
    fc.append(f"fps={FPS}")
    if sh.get("kb"):
        z0, z1 = sh["kb"]; d = sh["n"] / FPS
        fc.append(f"scale=w='2*trunc({W}*({z0}+({z1}-{z0})*min(t/{d},1))/2)':h=-2:eval=frame:flags=bicubic,crop={W}:{H}")
    if sh.get("bright"):
        fc.append(f"eq=brightness={sh['bright']}:gamma=1.12")
    if sh.get("blur"):
        fc.append("gblur=sigma=28,eq=brightness=-0.10:saturation=0.75")
    fc.append(GRADE)
    fc.append("format=yuv420p")
    return ",".join(fc)


def render_shot(i, sh, crf):
    out = f"{B}/shots/{i:03d}.mkv"
    key = json.dumps({k: v for k, v in sh.items() if k not in ("gfx", "start")}, sort_keys=True, default=str) + f"crf{crf}"
    if os.path.exists(out) and os.path.exists(out + ".key") and open(out + ".key").read() == key:
        return out
    n = sh["n"] + (XF if sh.get("xf") else 0)
    enc = ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-x264-params", "keyint=30"]
    if sh["kind"] == "black":
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}",
               "-frames:v", str(n), *enc, out]
    else:
        info = probe(sh["src"])
        sp = sh.get("speed", 1)
        need = n / FPS * sp + 0.5
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{sh['tin']:.3f}", "-t", f"{need:.3f}", "-i", info["path"],
               "-vf", shot_filter(sh) + f",tpad=stop_mode=clone:stop_duration=2", "-frames:v", str(n), "-an", *enc, out]
    run(cmd)
    open(out + ".key", "w").write(key)
    return out


def render_part(pi, items, crf):
    """join the shots of one part with short cross-dissolves; output length = sum of n"""
    out = f"{B}/shots/part_{pi:02d}.mkv"
    files = [f for f, _ in items]
    key = "|".join(open(f + ".key").read() for f in files) + f"XF{XF}"
    if os.path.exists(out) and os.path.exists(out + ".key") and open(out + ".key").read() == key:
        return out
    total_n = sum(sh["n"] for _, sh in items)
    enc = ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-x264-params", "keyint=30"]
    if len(items) == 1:
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", files[0], "-frames:v", str(total_n), "-c", "copy", out])
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        for f in files:
            cmd += ["-i", f]
        fc = []; last = "[0:v]"; acc = 0
        for k in range(len(items)):
            fc.append(f"[{k}:v]settb=AVTB,fps={FPS},format=yuv420p[s{k}]")
        last = "[s0]"
        for k in range(1, len(items)):
            acc += items[k - 1][1]["n"]
            fc.append(f"{last}[s{k}]xfade=transition=fade:duration={XF / FPS:.4f}:offset={acc / FPS:.4f}[x{k}]")
            last = f"[x{k}]"
        cmd += ["-filter_complex", ";".join(fc), "-map", last, "-frames:v", str(total_n), *enc, out]
        run(cmd)
    open(out + ".key", "w").write(key)
    return out


def render_shots(shots, crf):
    with ThreadPoolExecutor(2) as ex:
        files = list(ex.map(lambda a: render_shot(a[0], a[1], crf), enumerate(shots)))
    parts = {}
    for f, sh in zip(files, shots):
        parts.setdefault(sh["part"], []).append((f, sh))
    with ThreadPoolExecutor(2) as ex:
        pfiles = list(ex.map(lambda kv: render_part(kv[0], kv[1], crf), sorted(parts.items())))
    with open(f"{B}/shots.txt", "w") as f:
        for p in pfiles:
            f.write(f"file '{p}'\n")
    return pfiles


# ---------------------------------------------------------------- audio
def load_audio(path, ss=0.0, dur=None, stream="0:a:0", af=None):
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", f"{max(ss,0):.3f}"]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", path, "-map", stream, "-ac", "2", "-ar", str(SR)]
    if af:
        cmd += ["-af", af]
    cmd += ["-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)
    return x


def fade(x, fi=0.02, fo=0.02):
    x = x.copy(); a = int(fi * SR); b = int(fo * SR)
    if a and len(x) > a: x[:a] *= np.linspace(0, 1, a)[:, None]
    if b and len(x) > b: x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x


def place(buf, x, at):
    i = int(round(at * SR)); j = min(len(buf), i + len(x))
    if j > i: buf[i:j] += x[: j - i]


def db(g):
    return 10 ** (g / 20)


@functools.lru_cache(None)
def voice_norm(who):
    out = f"{B}/voice_{who}.wav"
    if not os.path.exists(out):
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{ROOT}/voix/{who}.m4a", "-af",
             "highpass=f=80,loudnorm=I=-16:TP=-2:LRA=7", "-ar", str(SR), "-ac", "1", out])
    return out


def snap(who, t, window=0.10):
    """move a cut point to the quietest 10 ms frame within ±window"""
    x = load_audio(voice_norm(who), max(t - window, 0), 2 * window)[:, 0]
    hop = int(0.01 * SR)
    if len(x) < hop * 3: return t
    e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)])
    k = int(np.argmin(e))
    return max(t - window, 0) + k * 0.01 + 0.005


def make_music(total, sections):
    """sections: list of (t_start, name) — names: intro, main, calm, outro. Original synth beat."""
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(7)
    BPM = 90; BEAT = 60 / BPM; BAR = 4 * BEAT
    n = int((total + 1) * SR)
    L = np.zeros(n); R = np.zeros(n)

    def add(sig, t, g=1.0, pan=0.0):
        i = int(t * SR); j = min(n, i + len(sig))
        if j <= i: return
        s = sig[: j - i] * g
        L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))

    def lp(x, f): return sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)
    def hp(x, f): return sosfilt(butter(2, f, "high", fs=SR, output="sos"), x)
    def hz(m): return 440 * 2 ** ((m - 69) / 12)

    def kick():
        k = int(0.45 * SR); tt = np.arange(k) / SR
        f = 45 + 110 * np.exp(-tt * 35)
        return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7))

    def snare():
        k = int(0.3 * SR); tt = np.arange(k) / SR
        return (0.6 * hp(rng.standard_normal(k), 1500) * np.exp(-tt * 18) + 0.5 * np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 30))

    def hat(o=False):
        k = int((0.25 if o else 0.05) * SR); tt = np.arange(k) / SR
        return hp(rng.standard_normal(k), 7000) * np.exp(-tt * (12 if o else 90))

    def crash():
        k = int(2.5 * SR); tt = np.arange(k) / SR
        return hp(rng.standard_normal(k), 4000) * np.exp(-tt * 1.6)

    K, S, Hh, HO, CR = kick(), snare(), hat(), hat(True), crash()
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]

    def bass(m, d):
        k = int(d * SR); tt = np.arange(k) / SR; f = hz(m - 12)
        return np.tanh(1.6 * (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt))) * np.minimum(1, tt / 0.01) * np.exp(-tt * 1.2)

    def pad(notes, d):
        k = int(d * SR); tt = np.arange(k) / SR; s = np.zeros(k)
        for m in notes:
            for det in (-0.12, 0.12):
                f = hz(m + det); s += 2 * ((f * tt) % 1) - 1
        s = lp(s / (len(notes) * 2), 1400)
        return s * np.minimum(1, tt / 0.3) * np.minimum(1, np.maximum(0, d - tt) / 0.3)

    def pluck(m, d=0.5):
        k = int(d * SR); tt = np.arange(k) / SR; f = hz(m)
        return np.sin(2 * np.pi * f * tt + 0.8 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 6)) * np.minimum(1, tt / 0.003) * np.exp(-tt / 0.22)

    motifs = [[76, None, 72, None, 74, 76, None, 69], [77, None, 76, None, 72, None, 69, None],
              [76, None, 72, 74, None, 72, 67, None], [74, None, 71, None, 74, 79, None, 76]]

    def section_at(tt):
        name = sections[0][1]
        for s0, nm in sections:
            if tt + 1e-6 >= s0: name = nm
        return name

    # sections change exactly at their time: build per beat-grid but anchored at each section start
    bounds = [s for s, _ in sections] + [total]
    for si, (s0, name) in enumerate(sections):
        s1 = bounds[si + 1]
        if name == "outro":
            add(CR, s0, 0.35); add(K, s0, 1.0)
            add(pad(prog[0][1], s1 - s0 + 0.5), s0, 0.22)
            add(bass(prog[0][0], 2.5), s0, 0.5)
            continue
        b = 0
        while s0 + b * BAR < s1 - 0.05:
            t0 = s0 + b * BAR
            bar_len = min(BAR, s1 - t0)
            root, chord = prog[b % 4]
            add(pad(chord, bar_len + 0.05), t0, 0.22 if name in ("intro", "calm") else 0.13)
            if name in ("main", "calm"):
                add(bass(root, bar_len * (0.75 if b % 2 else 1)), t0, 0.5)
            if name == "main":
                if b == 0: add(CR, t0, 0.22)
                for pos in [0, 3, 6] + ([7] if b % 4 == 3 else []):
                    if pos * BEAT / 2 < bar_len: add(K, t0 + pos * BEAT / 2, 0.9)
                for bb in (1, 3):
                    if bb * BEAT < bar_len: add(S, t0 + bb * BEAT, 0.55)
                for k in range(8):
                    if k * BEAT / 2 < bar_len: add(Hh, t0 + k * BEAT / 2, 0.18, 0.3)
                if b % 2 == 1:
                    for k in range(6):
                        if 3.25 * BEAT + k * BEAT / 8 < bar_len: add(Hh, t0 + 3.25 * BEAT + k * BEAT / 8, 0.12, 0.3)
                if b % 4 == 0: add(HO, t0 + 1.5 * BEAT, 0.12, -0.3)
            if name == "calm":
                for bb in (1, 3):
                    if bb * BEAT < bar_len: add(S, t0 + bb * BEAT, 0.2)
                for k in range(4):
                    if k * BEAT < bar_len: add(Hh, t0 + k * BEAT, 0.08, 0.3)
            if name in ("main", "intro") and not (name == "main" and b % 8 >= 6):
                for k, m in enumerate(motifs[b % 4]):
                    if m is not None and k * BEAT / 2 < bar_len:
                        add(pluck(m), t0 + k * BEAT / 2, 0.15 if name == "main" else 0.1, -0.2)
            b += 1
    d = int(BEAT * 0.75 * SR)
    L[d:] += 0.15 * R[:-d]; R[d:] += 0.15 * L[:-d]
    mix = np.tanh(np.stack([L, R], 1) * 0.9)
    mix /= np.max(np.abs(mix)) + 1e-9
    fi = int(0.8 * SR); mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    end = int(total * SR); fo = int(2.5 * SR)
    mix[end - fo:end] *= np.linspace(1, 0, fo)[:, None]; mix[end:] = 0
    return mix[: int(total * SR) + SR] * db(-23)  # music bed, kept low under the voices


def build_audio(shots, dialog, zones, total):
    n = int((total + 1) * SR)
    dia = np.zeros((n, 2)); amb = np.zeros((n, 2))
    # dialog
    for i, d in enumerate(dialog):
        x = load_audio(voice_norm(d["who"]), d["vin"], d["vout"] - d["vin"])
        prev = dialog[i - 1] if i else None; nxt = dialog[i + 1] if i + 1 < len(dialog) else None
        cin = prev and prev["who"] == d["who"] and abs(prev["vout"] - d["vin"]) < 0.01 and abs(prev["at"] + prev["vout"] - prev["vin"] - d["at"]) < 0.05
        cout = nxt and nxt["who"] == d["who"] and abs(nxt["vin"] - d["vout"]) < 0.01 and abs(d["at"] + d["vout"] - d["vin"] - nxt["at"]) < 0.05
        place(dia, fade(x, 0.003 if cin else 0.05, 0.003 if cout else 0.08), d["at"])
    # Abdou voice-over
    abd0 = min(z[0] for z in zones if z[0] > 60)
    vo_path = f"{B}/vo_abdou.wav"
    if not os.path.exists(vo_path):
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{ROOT}/vo/abdou.m4a", "-af",
             "highpass=f=70,loudnorm=I=-16:TP=-2:LRA=7", "-ar", str(SR), "-ac", "1", vo_path])
    for a, b2, off in TL.VO_ABDOU:
        x = load_audio(vo_path, a, b2 - a)
        place(dia, fade(x, 0.03, 0.06), abd0 + off)
    # Sidy voice-over
    sidy0 = min(z[0] for z in zones)
    vo_s = f"{B}/vo_sidy.wav"
    if not os.path.exists(vo_s):
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{ROOT}/vo/sidy.m4a", "-af",
             "highpass=f=70,loudnorm=I=-16:TP=-2:LRA=7", "-ar", str(SR), "-ac", "1", vo_s])
    for a, b2, off in TL.VO_SIDY:
        x = load_audio(vo_s, a, b2 - a)
        place(dia, fade(x, 0.03, 0.06), sidy0 + off)
    # ambience from rushes
    for sh in shots:
        if sh["kind"] == "black" or sh.get("amb") is None:
            continue
        dur = sh["n"] / FPS
        x = load_audio(probe(sh["src"])["path"], sh["tin"], dur)
        if len(x) == 0: continue
        place(amb, fade(x, 0.04, 0.06) * db(sh["amb"]), sh["start"])
    # loudness-normalize ambience chunks roughly: rush audio is ~ -18 dB mean already
    # music sections
    first_main = shots[1]["start"] + shots[1]["n"] / FPS  # main beat starts at WIN CERGY
    abd = min(z[0] for z in zones if z[0] > 60)
    outro = shots[-1]["start"]
    secs = [(0, "intro"), (first_main, "main"), (abd, "calm"), (outro, "outro")]
    mus = make_music(total, secs)
    mus = np.pad(mus, ((0, max(0, n - len(mus))), (0, 0)))[:n]
    # ducking from dialog envelope
    hop = int(0.01 * SR)
    m = np.abs(dia[:, 0])
    env = np.array([m[i:i + hop].max() if i < len(m) else 0 for i in range(0, n, hop)])
    act = (env > 0.02).astype(float)
    # attack 60 ms, release 400 ms smoothing
    g = np.zeros_like(act); s = 0
    for i, v in enumerate(act):
        s = s + (v - s) * (0.17 if v > s else 0.025); g[i] = s
    duck = 1 - g * (1 - db(-14))
    duck = np.repeat(duck, hop)[:n][:, None]
    # voice-over zones: music a bit lower (version A), music removed (version B)
    vo_mask = np.zeros(n)
    for z0, z1 in zones:
        vo_mask[int(z0 * SR):int(z1 * SR)] = 1
    k = int(0.25 * SR)
    vo_mask = np.convolve(vo_mask, np.ones(k) / k, "same")[:, None]
    mus_a = mus * duck * (1 - vo_mask * (1 - db(-5)))
    mus_b = mus * duck * (1 - vo_mask)
    return dia, amb, mus_a, mus_b, n


def write_wav(path, x):
    x = np.clip(x, -1, 1).astype(np.float32)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                          "-c:a", "pcm_s24le", path], stdin=subprocess.PIPE)
    p.stdin.write(x.tobytes()); p.stdin.close(); p.wait()


def loudnorm_file(src, dst, I=-14, af=None):
    if af:
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le", dst]); return af
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={I}:TP=-1.0:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(r[r.rfind("{"):r.rfind("}") + 1])
    af = (f"loudnorm=I={I}:TP=-1.0:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le", dst])
    return af


# ---------------------------------------------------------------- graphics
@functools.lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


def parse_marked(text):
    """'A {B C} D' -> [(word, gold)]"""
    out = []; gold = False
    for tok in text.replace("{", " { ").replace("}", " } ").split():
        if tok == "{": gold = True; continue
        if tok == "}": gold = False; continue
        out.append((tok, gold))
    return out


def text_block(words, fnt, maxw, color=WHITE, stroke=0, line_gap=1.12, align="center", spacing=0):
    """render list of (word, gold) wrapped into an RGBA image"""
    sp = fnt.getlength(" ")
    lines = [[]]; lw = 0
    for w, g in words:
        ww = fnt.getlength(w)
        if lines[-1] and lw + sp + ww > maxw:
            lines.append([]); lw = 0
        lw += (sp if lines[-1] else 0) + ww
        lines[-1].append((w, g, ww))
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * line_gap)
    widths = [sum(x[2] for x in l) + sp * (len(l) - 1) for l in lines]
    iw = int(max(widths) + 2 * stroke + 8); ih = int(lh * len(lines) + 2 * stroke + 8)
    im = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = stroke + 4
    for l, lwid in zip(lines, widths):
        x = stroke + 4 + ((iw - 2 * stroke - 8 - lwid) / 2 if align == "center" else 0)
        for w, g, ww in l:
            d.text((x, y), w, font=fnt, fill=GOLD if g else color, stroke_width=stroke, stroke_fill=(0, 0, 0))
            x += ww + sp
        y += lh
    return im


def shadow(im, r=10, a=150, off=(0, 4)):
    al = im.getchannel("A").filter(ImageFilter.GaussianBlur(r)).point(lambda v: v * a // 255)
    sh = Image.new("RGBA", (im.width + 4 * r, im.height + 4 * r), (0, 0, 0, 0))
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255)); blk.putalpha(al)
    sh.alpha_composite(blk, (2 * r + off[0], 2 * r + off[1]))
    sh.alpha_composite(im, (2 * r, 2 * r))
    return sh


@functools.lru_cache(None)
def spr_title(main, sub, size=96):
    words = [(w, w == "·") for w in main.split()]
    while font(F_BLACK, size).getlength(main) > 960 and size > 40:
        size -= 2
    t = text_block(words, font(F_BLACK, size), 1040)
    parts = [t]
    bar = Image.new("RGBA", (140, 8), GOLD + (255,))
    s = text_block([(w, True) for w in sub.split()], font(F_XBOLD, 44), 980) if sub else None
    wmax = max(t.width, s.width if s else 0)
    hh = t.height + 30 + (s.height + 22 if s else 0)
    im = Image.new("RGBA", (wmax, hh), (0, 0, 0, 0))
    im.alpha_composite(t, ((wmax - t.width) // 2, 0))
    im.alpha_composite(bar, ((wmax - 140) // 2, t.height + 6))
    if s:
        im.alpha_composite(s, ((wmax - s.width) // 2, t.height + 32))
    return shadow(im, 14, 170)


@functools.lru_cache(None)
def spr_card(name, info, extra=None):
    cw = 900
    nm = text_block([(name, False)], font(F_BLACK, 88), 2000, align="left")
    inf = text_block([(info, True)], font(F_XBOLD, 42), 2000, align="left")
    ex = text_block([(extra, False)], font(F_BOLD, 34), 2000, color=(235, 235, 235), align="left") if extra else None
    ch = 30 + nm.height - 8 + inf.height + (ex.height + 2 if ex else 0) + 24
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, cw, ch], fill=(8, 8, 8, 235))
    d.rectangle([0, 0, cw, 5], fill=GOLD + (255,))
    d.rectangle([0, ch - 3, cw, ch], fill=GOLD + (255,))
    d.rectangle([0, 0, 14, ch], fill=GOLD + (255,))
    y = 22
    im.alpha_composite(nm, (40, y)); y += nm.height - 8
    im.alpha_composite(inf, (42, y)); y += inf.height
    if ex:
        im.alpha_composite(ex, (42, y))
    return im


@functools.lru_cache(None)
def spr_sub(text):
    return text_block(parse_marked(text), font(F_BLACK, 64), 940, stroke=7, line_gap=1.08)


@functools.lru_cache(None)
def spr_question(text):
    lab = text_block([("LA QUESTION", True)], font(F_XBOLD, 40), 900)
    ln = Image.new("RGBA", (90, 5), GOLD + (255,))
    q = text_block(parse_marked(text), font(F_BLACK, 80), 920, line_gap=1.1)
    w = max(q.width, lab.width + 220)
    im = Image.new("RGBA", (w, lab.height + 30 + q.height), (0, 0, 0, 0))
    lx = (w - lab.width) // 2
    im.alpha_composite(lab, (lx, 0))
    im.alpha_composite(ln, (lx - 110, lab.height // 2)); im.alpha_composite(ln, (lx + lab.width + 20, lab.height // 2))
    im.alpha_composite(q, ((w - q.width) // 2, lab.height + 30))
    return shadow(im, 14, 160)


@functools.lru_cache(None)
def spr_band(main, sub):
    bh = 380
    im = Image.new("RGBA", (W, bh), (8, 8, 8, 240))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 6], fill=GOLD + (255,)); d.rectangle([0, bh - 6, W, bh], fill=GOLD + (255,))
    return im


@functools.lru_cache(None)
def spr_band_text(main, sub):
    return spr_title(main, sub, 86)


@functools.lru_cache(None)
def logo_img(w):
    lg = Image.open(LOGO).convert("RGBA")
    return lg.resize((w, int(lg.height * w / lg.width)), Image.LANCZOS)


@functools.lru_cache(None)
def spr_outro_text():
    a = text_block(parse_marked("RENDEZ-VOUS LE {20 DÉCEMBRE}"), font(F_BLACK, 60), 1040)
    b = text_block([("À", False), ("GROSLAY", True)], font(F_BLACK, 60), 1040)
    im = Image.new("RGBA", (max(a.width, b.width), a.height + b.height), (0, 0, 0, 0))
    im.alpha_composite(a, ((im.width - a.width) // 2, 0)); im.alpha_composite(b, ((im.width - b.width) // 2, a.height))
    return im


def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_in(x): x = min(max(x, 0), 1); return x ** 3


def with_alpha(im, a):
    if a >= 0.999: return im
    im = im.copy(); al = im.getchannel("A").point(lambda v: int(v * a)); im.putalpha(al); return im


def scaled(im, s):
    if abs(s - 1) < 0.003: return im
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)


def paste_c(canvas, im, cx, cy):
    x = int(cx - im.width / 2); y = int(cy - im.height / 2)
    # clip to canvas
    if x < 0 or y < 0 or x + im.width > W or y + im.height > H:
        bx0, by0 = max(0, -x), max(0, -y)
        im = im.crop((bx0, by0, min(im.width, W - x), min(im.height, H - y)))
        x, y = max(x, 0), max(y, 0)
    canvas.alpha_composite(im, (x, y))


def anim_pop(t, t0, t1, tin=0.45, tout=0.35):
    """returns (alpha, scale) for title-like elements"""
    if t < t0 or t > t1: return 0, 1
    if t < t0 + tin:
        k = ease_out((t - t0) / tin); return k, 0.88 + 0.12 * k
    if t > t1 - tout:
        k = ease_in((t - (t1 - tout)) / tout); return 1 - k, 1 + 0.06 * k
    return 1, 1


def subtitle_events(dialog):
    """split each dialog segment into short chunks timed on voice activity"""
    ev = []
    for d in dialog:
        x = load_audio(voice_norm(d["who"]), d["vin"], d["vout"] - d["vin"])[:, 0]
        hop = int(0.02 * SR)
        e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, max(len(x) - hop, 1), hop)])
        act = e > max(0.015, 0.25 * np.percentile(e, 90))
        cum = np.cumsum(act) / max(act.sum(), 1)
        words = d["text"].upper().replace("’", "'").split()
        chunks = []; cur = []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or len(" ".join(cur)) > 16 or w.endswith((",", ".", "?")):
                chunks.append(cur); cur = []
        if cur: chunks.append(cur)
        total_chars = sum(len(" ".join(c)) for c in chunks)
        acc = 0; dur = d["vout"] - d["vin"]
        for c in chunks:
            f0 = acc / total_chars; acc += len(" ".join(c)); f1 = acc / total_chars
            i0 = int(np.searchsorted(cum, f0 + 1e-6)); i1 = int(np.searchsorted(cum, f1 - 1e-6))
            t0 = d["at"] + i0 * 0.02; t1 = d["at"] + (i1 + 1) * 0.02
            mk = " ".join("{" + w + "}" if w.strip(",.?!").upper() in TL.GOLD_WORDS else w for w in c)
            ev.append([t0, t1, mk.replace(",", "").replace(".", "")])
        # make chunks contiguous within the segment
    ev.sort()
    for i in range(len(ev) - 1):
        if ev[i + 1][0] - ev[i][1] < 0.35:
            ev[i][1] = ev[i + 1][0]
    for e in ev:
        e[1] = max(e[1], e[0] + 0.45)
    return ev


def frames(gfx, subs, dips, total):
    n = nframes(total)
    small = with_alpha(logo_img(150), 0.72)
    big_logo_windows = [(g["t0"], g["t1"]) for g in gfx if g["type"] == "logo_big"]
    for fi in range(n):
        t = fi / FPS
        cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for g in gfx:
            if not (g["t0"] - 0.01 <= t <= g["t1"] + 0.01): continue
            ty = g["type"]
            if ty == "title":
                a, s = anim_pop(t, g["t0"], g["t1"])
                if a > 0: paste_c(cv, with_alpha(scaled(spr_title(g["main"], g["sub"]), s), a), W / 2, 900)
            elif ty == "title_top":
                a, s = anim_pop(t, g["t0"], g["t1"])
                if a > 0: paste_c(cv, with_alpha(scaled(spr_title(g["main"], g["sub"], 70), s), a), W / 2, g.get("y", 560))
            elif ty == "question":
                a, s = anim_pop(t, g["t0"], g["t1"], 0.35, 0.25)
                if a > 0: paste_c(cv, with_alpha(scaled(spr_question(g["text"]), s), a), W / 2, 880)
            elif ty == "card":
                c = spr_card(g["name"], g["info"], g.get("extra"))
                if g.get("instant") and t < g["t0"] + 0.3:
                    x = 60
                else:
                    k = ease_out((t - g["t0"]) / 0.3) if t < g["t0"] + 0.3 else 1
                    if t > g["t1"] - 0.3: k = 1 - ease_in((t - (g["t1"] - 0.3)) / 0.3)
                    x = int(-c.width + (60 + c.width) * k)
                y = 1430
                if x + c.width > 0:
                    cv.alpha_composite(c.crop((max(0, -x), 0, c.width, c.height)), (max(0, x), y))
            elif ty == "band":
                band = spr_band(g["main"], g["sub"])
                cv.alpha_composite(band, (0, 1290))
                k = ease_out((t - g["t0"] - 0.1) / 0.35)
                tx = spr_band_text(g["main"], g["sub"])
                if k > 0:
                    paste_c(cv, with_alpha(tx, k), W / 2 - (1 - k) * 300, 1290 + 190)
            elif ty == "sentence":
                a = min(1, (t - g["t0"]) / 0.15, (g["t1"] - t) / 0.15)
                if a > 0: paste_c(cv, with_alpha(spr_sub(g["text"]), a), W / 2, 1250)
            elif ty == "logo_big":
                d = g["t1"] - g["t0"]
                a, s = anim_pop(t, g["t0"], g["t1"], 0.7, 0.5)
                s = s * (1 + 0.04 * (t - g["t0"]) / d)
                lg = logo_img(780 if not g.get("outro") else 700)
                cy = 900 if not g.get("outro") else 780
                if a > 0: paste_c(cv, with_alpha(scaled(lg, s), a), W / 2, cy)
                if g.get("outro") and t > g["t0"] + 0.6:
                    a2, s2 = anim_pop(t, g["t0"] + 0.6, g["t1"], 0.45, 0.5)
                    paste_c(cv, with_alpha(scaled(spr_outro_text(), s2), a2), W / 2, 1390)
        for t0, t1, txt in subs:
            if t0 <= t < t1:
                a = min(1, (t - t0) / 0.06)
                sc = 0.92 + 0.08 * ease_out((t - t0) / 0.12)
                paste_c(cv, with_alpha(scaled(spr_sub(txt), sc), a), W / 2, 1250)
        # dip to black at part boundaries
        for d in dips:
            dd = abs(t - d)
            if dd < DIP / 2 + 1e-6:
                al = int(255 * (1 - dd / (DIP / 2)))
                cv.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, al)))
        # final fade to black
        if t > total - 0.8:
            al = int(255 * min(1, (t - (total - 0.8)) / 0.8))
            cv.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, al)))
        if not any(a - 0.2 <= t <= b + 0.2 for a, b in big_logo_windows) and t < total - 0.8:
            cv.alpha_composite(small, (W - 150 - 44, 210))
        yield cv.tobytes()


# ---------------------------------------------------------------- final render
def render(final, gfx, subs, dips, total, audio_path, out, nomusic_audio=None):
    if final:
        venc = ["-c:v", "libx264", "-preset", "slow", "-crf", "14", "-profile:v", "high", "-level", "4.2",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "320k"]
        vf = "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    else:
        venc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "27", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-c:a", "aac", "-b:a", "128k"]
        vf = "[0:v][1:v]overlay=0:0:format=auto,scale=720:1280,format=yuv420p[v]"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{B}/shots.txt",
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", audio_path, "-filter_complex", vf, "-map", "[v]", "-map", "2:a",
           "-r", str(FPS), "-frames:v", str(nframes(total)), *venc, "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i, fr in enumerate(frames(gfx, subs, dips, total)):
        p.stdin.write(fr)
        if i % 300 == 0: print(f"  frame {i}/{nframes(total)}", flush=True)
    p.stdin.close(); p.wait()
    if p.returncode: raise SystemExit("render failed")


def main(mode):
    shots, gfx, dialog, dips, zones, total = build_timeline()
    total = sum(s["n"] for s in shots) / FPS
    print(f"timeline {total:.2f}s, {len(shots)} shots")
    json.dump(dict(shots=[{k: v for k, v in s.items() if k != 'gfx'} for s in shots], dips=dips, zones=zones, total=total),
              open(f"{B}/timeline.json", "w"), indent=1, default=str)
    final = mode == "final"
    print("shots..."); render_shots(shots, 12 if not final else 8)
    print("audio...")
    dia, amb, mus_a, mus_b, n = build_audio(shots, dialog, zones, total)
    write_wav(f"{B}/mix_a_raw.wav", dia + amb + mus_a)
    write_wav(f"{B}/mix_b_raw.wav", dia + amb + mus_b)
    af = loudnorm_file(f"{B}/mix_a_raw.wav", f"{B}/mix_a.wav")
    # version B gets exactly the same gain as A so voices sit at the same level
    loudnorm_file(f"{B}/mix_b_raw.wav", f"{B}/mix_b.wav", af=af)
    subs = subtitle_events(dialog)
    json.dump(subs, open(f"{B}/subs.json", "w"), ensure_ascii=False, indent=0)
    out_dir = "/home/user/SEKO95130/livrables"
    if final:
        print("render final A..."); render(True, gfx, subs, dips, total, f"{B}/mix_a.wav", f"{out_dir}/HOUSE_Cergy_interview_FINAL.mp4")
        print("render final B..."); render(True, gfx, subs, dips, total, f"{B}/mix_b.wav", f"{out_dir}/HOUSE_Cergy_interview_FINAL_sans_musique_Sidy_Abdou.mp4")
    else:
        print("render preview..."); render(False, gfx, subs, dips, total, f"{B}/mix_a.wav", f"{out_dir}/HOUSE_Cergy_interview_V7_preview.mp4")
    print("done")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "preview")
