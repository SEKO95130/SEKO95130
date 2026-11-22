"""Original instrumental (trap / hip-hop, 90 BPM, A minor) for the House of Basketball edit.
Fully synthesized: no samples, no copyright issues."""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
BPM = 90
BEAT = 60 / BPM
BAR = 4 * BEAT
N_BARS = 64  # ~170 s
rng = np.random.default_rng(7)

total = int(N_BARS * BAR * SR) + SR * 3
L = np.zeros(total)
R = np.zeros(total)


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    j = min(total, i + len(sig))
    sig = sig[: j - i] * gain
    L[i:j] += sig * (1 - max(0, pan))
    R[i:j] += sig * (1 + min(0, pan))


def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
    return e


def lp(x, f):
    return sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)


def hp(x, f):
    return sosfilt(butter(2, f, "high", fs=SR, output="sos"), x)


def note_hz(n):  # midi
    return 440 * 2 ** ((n - 69) / 12)


# --- drums ---
def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 35)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(2.2 * np.sin(ph) * np.exp(-t * 7))


def snare():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    noise = hp(rng.standard_normal(n), 1500) * np.exp(-t * 18)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    clap = sum(hp(rng.standard_normal(n), 900) * np.exp(-np.maximum(0, t - k * 0.011) * 60) * (t >= k * 0.011) for k in range(3))
    return 0.6 * noise + 0.5 * tone + 0.35 * clap


def hat(open_=False):
    n = int((0.25 if open_ else 0.05) * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t * (12 if open_ else 90))


K, S, H, HO = kick(), snare(), hat(), hat(True)

# --- harmony: Am - F - C - G ---
prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]


def bass808(midi, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note_hz(midi - 12)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return np.tanh(1.6 * s) * np.minimum(1, t / 0.01) * np.exp(-t * 1.2)


def pad(notes, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for m in notes:
        for det in (-0.12, 0.12):
            f = note_hz(m + det)
            s += ((2 * ((f * t) % 1) - 1))  # saw
    s = lp(s / (len(notes) * 2), 1400)
    e = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.4)
    return s * e


def pluck(midi, dur=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note_hz(midi)
    s = np.sin(2 * np.pi * f * t + 0.8 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 6))
    return s * env(n, 0.003, 0.22)


# melody motif per chord (scale degrees in A minor, as midi), 8th-note grid
motifs = [
    [76, None, 72, None, 74, 76, None, 69],
    [77, None, 76, None, 72, None, 69, None],
    [76, None, 72, 74, None, 72, 67, None],
    [74, None, 71, None, 74, 79, None, 76],
]

for bar in range(N_BARS):
    t0 = bar * BAR
    root, chord = prog[bar % 4]
    section = (
        "intro" if bar < 4 else
        "main" if bar < 40 else
        "calm" if bar < 56 else
        "main" if bar < 62 else
        "outro"
    )
    # pad always (quieter in main)
    add(pad(chord, BAR), t0, 0.22 if section in ("intro", "calm", "outro") else 0.14, 0)
    if section in ("main", "calm"):
        add(bass808(root, BAR * (0.75 if bar % 2 else 1)), t0, 0.55)
    if section == "main":
        # kick pattern (8th grid positions)
        for pos in [0, 3, 6] + ([7] if bar % 4 == 3 else []):
            add(K, t0 + pos * BEAT / 2, 0.9)
        for b in (1, 3):
            add(S, t0 + b * BEAT, 0.55)
        # hats: 8ths with 16th/32nd rolls at bar end
        for k in range(8):
            add(H, t0 + k * BEAT / 2, 0.18, pan=0.3)
        if bar % 2 == 1:
            for k in range(6):
                add(H, t0 + 3.25 * BEAT + k * BEAT / 8, 0.12, pan=0.3)
        if bar % 4 == 0:
            add(HO, t0 + 1.5 * BEAT, 0.12, pan=-0.3)
    if section == "calm":
        for b in (1, 3):
            add(S, t0 + b * BEAT, 0.25)
        for k in range(4):
            add(H, t0 + k * BEAT, 0.1, pan=0.3)
    if section in ("main", "intro") and not (section == "main" and bar % 8 >= 6):
        for k, m in enumerate(motifs[bar % 4]):
            if m is not None:
                add(pluck(m), t0 + k * BEAT / 2, 0.16 if section == "main" else 0.1, pan=-0.2)

# simple stereo widening reverb-ish echo on melody bus (global light delay)
d = int(BEAT * 0.75 * SR)
L[d:] += 0.18 * R[:-d]
R[d:] += 0.18 * L[:-d]

mix = np.stack([L, R], 1)
mix = np.tanh(mix * 0.9)
mix /= np.max(np.abs(mix)) + 1e-9
# fades
fi = int(1.0 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(3.0 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
wavfile.write("/home/user/work/brand/music_house.wav", SR, (mix * 0.89 * 32767).astype(np.int16))
print("bars", N_BARS, "seconds", total / SR)
