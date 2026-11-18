"""
Nhạc nền lo-fi tự sáng tác (không bản quyền) cho video Trạm Podcast Crypto.
Mỗi tuần 1 giai điệu khác nhau (theo seed), tempo chậm, âm lượng nhẹ để không lấn giọng đọc.
"""
from __future__ import annotations

import numpy as np

SR = 24000

# các vòng hợp âm "chill" (nốt MIDI)
PROGRESSIONS = [
    [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 66]],   # Am7 Fmaj7 Cmaj7 G
    [[50, 53, 57, 60], [55, 59, 62, 65], [48, 52, 55, 59], [57, 60, 64, 67]],   # Dm7 G7 Cmaj7 Am7
    [[52, 55, 59, 62], [57, 60, 64, 67], [50, 53, 57, 60], [55, 59, 62, 65]],   # Em7 Am7 Dm7 G7
    [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]],   # Fmaj7 Em7 Dm7 Cmaj7
]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    # lọc 1 cực, vector hoá theo khối để nhanh
    for i in range(0, len(x), 4096):
        blk = x[i:i + 4096]
        out = np.empty_like(blk)
        for j, v in enumerate(blk):
            acc = (1 - a) * v + a * acc
            out[j] = acc
        y[i:i + 4096] = out
    return y


def make_music(seconds: float, seed: int = 0) -> bytes:
    rnd = np.random.default_rng(seed)
    prog = PROGRESSIONS[seed % len(PROGRESSIONS)]
    bpm = float(rnd.choice([74, 78, 82, 86]))
    beat = 60.0 / bpm
    bar = 4 * beat
    n = int(seconds * SR) + SR
    t_all = np.arange(n) / SR
    out = np.zeros(n)

    # pad hợp âm: sóng sin + lệch nhẹ, mở/tắt mềm theo từng ô nhịp
    nbars = int(np.ceil(seconds / bar)) + 1
    for b in range(nbars):
        chord = prog[b % 4]
        s0 = int(b * bar * SR)
        s1 = min(n, int((b + 1) * bar * SR + 0.4 * SR))
        if s0 >= n:
            break
        tt = np.arange(s1 - s0) / SR
        env = np.minimum(1, tt / 0.8) * np.minimum(1, np.maximum(0, (bar + 0.4 - tt) / 0.9))
        sig = np.zeros_like(tt)
        for m in chord:
            f = hz(m)
            sig += np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.004 * tt + 1.3)
        out[s0:s1] += 0.05 * env * sig
        # bass
        root = hz(chord[0] - 12)
        for k in (0, 2):
            q0 = s0 + int(k * beat * SR)
            q1 = min(n, q0 + int(beat * 1.6 * SR))
            if q0 >= n:
                continue
            tq = np.arange(q1 - q0) / SR
            out[q0:q1] += 0.16 * np.exp(-tq * 2.2) * np.sin(2 * np.pi * root * tq)
        # arpeggio nhẹ (móc 8 nốt/ô nhịp)
        for k in range(8):
            if rnd.random() < 0.35:
                continue
            m = chord[int(rnd.integers(0, 4))] + 12
            q0 = s0 + int(k * beat / 2 * SR)
            q1 = min(n, q0 + int(0.5 * SR))
            if q0 >= n:
                continue
            tq = np.arange(q1 - q0) / SR
            out[q0:q1] += 0.035 * np.exp(-tq * 7) * np.sin(2 * np.pi * hz(m) * tq)

    # trống nhẹ: kick nhịp 1 & 3, hi-hat nốt móc
    total_beats = int(seconds / beat) + 2
    for k in range(total_beats):
        s0 = int(k * beat * SR)
        if s0 >= n:
            break
        if k % 2 == 0:
            L = min(n - s0, int(0.22 * SR))
            tq = np.arange(L) / SR
            f = 45 + 75 * np.exp(-tq * 30)
            out[s0:s0 + L] += 0.22 * np.exp(-tq * 14) * np.sin(2 * np.pi * np.cumsum(f) / SR)
        h0 = s0 + int(beat / 2 * SR)
        L = min(max(0, n - h0), int(0.05 * SR))
        if L > 0:
            noise = rnd.standard_normal(L)
            noise = noise - np.convolve(noise, np.ones(4) / 4, mode="same")
            out[h0:h0 + L] += 0.02 * np.exp(-np.arange(L) / SR * 60) * noise

    # vào/ra mềm
    fade = int(2.5 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = out[: int(seconds * SR)]
    peak = np.max(np.abs(out)) or 1
    out = out / peak * 0.5
    return (out * 32767).astype("<i2").tobytes()
