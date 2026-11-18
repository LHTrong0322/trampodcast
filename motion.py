"""
Bộ dựng video CHUYỂN ĐỘNG cho Trạm Podcast Crypto (vẽ từng khung hình bằng Pillow, mã hoá bằng ffmpeg).

Hiệu ứng: chữ trượt lên/hiện dần theo nhịp, nhãn "bật" ra, ô số liệu trượt vào + số đếm chạy,
biểu đồ giá vẽ dần, phụ đề karaoke (chữ đang đọc tô vàng), cột sóng nhạc nhảy theo giọng đọc,
nền + hạt sáng trôi nhẹ, chuyển cảnh quét vàng giữa các tin.
"""
from __future__ import annotations

import math
import random
import re
import subprocess
import wave
from array import array
from pathlib import Path

from PIL import Image, ImageDraw

FPS = 25
SR = 24000


# ---------------------------------------------------------------------------
# easing
# ---------------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_out_back(x, s=1.7):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


# ---------------------------------------------------------------------------
# layer = 1 ảnh RGBA nhỏ + kiểu xuất hiện
# ---------------------------------------------------------------------------
class Layer:
    def __init__(self, img: Image.Image, x: int, y: int, anim: str = "fade_up", delay: float = 0.0,
                 dur: float = 0.55, dist: int = 46):
        self.img, self.x, self.y = img, x, y
        self.anim, self.delay, self.dur, self.dist = anim, delay, dur, dist
        self._cache: dict = {}

    def _variant(self, alpha_q: int, scale_q: int) -> Image.Image:
        key = (alpha_q, scale_q)
        if key not in self._cache:
            im = self.img
            if scale_q != 100:
                w, h = im.size
                im = im.resize((max(1, int(w * scale_q / 100)), max(1, int(h * scale_q / 100))),
                               Image.BILINEAR)
            if alpha_q < 16:
                im = im.copy()
                a = im.getchannel("A").point(lambda v, f=alpha_q / 16: int(v * f))
                im.putalpha(a)
            self._cache[key] = im
        return self._cache[key]

    def draw(self, canvas: Image.Image, t: float):
        p = (t - self.delay) / self.dur
        if p <= 0:
            return
        e = ease_out_cubic(p)
        alpha_q = 16 if p >= 1 else max(1, int(round(clamp(p * 1.6) * 16)))
        x, y, scale_q = self.x, self.y, 100
        if self.anim == "fade_up":
            y += int((1 - e) * self.dist)
        elif self.anim == "slide_left":
            x += int((1 - e) * self.dist * 4)
        elif self.anim == "slide_up":
            y += int((1 - e) * self.dist * 3)
        elif self.anim == "pop":
            s = ease_out_back(p) if p < 1 else 1.0
            scale_q = max(10, int(round((0.6 + 0.4 * s) * 20)) * 5)
        im = self._variant(alpha_q, scale_q)
        if scale_q != 100:
            w0, h0 = self.img.size
            x += (w0 - im.size[0]) // 2
            y += (h0 - im.size[1]) // 2
        canvas.paste(im, (x, y), im)


# ---------------------------------------------------------------------------
# nền chuyển động
# ---------------------------------------------------------------------------
class Backdrop:
    def __init__(self, W, H, base=(20, 16, 12), glow=(120, 84, 20), seed=7):
        self.W, self.H = W, H
        BW, BH = int(W * 1.25), int(H * 1.25)
        img = Image.new("RGB", (BW, BH), base)
        for cx, cy, r, col, k in [(BW * 0.85, BH * 0.1, max(BW, BH) * 0.55, glow, 30),
                                  (BW * 0.1, BH * 0.95, max(BW, BH) * 0.45, (60, 40, 110), 18)]:
            mask = Image.new("L", (BW, BH), 0)
            md = ImageDraw.Draw(mask)
            for i in range(36, 0, -1):
                rr = r * i / 36
                md.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=int(k * (1 - i / 36)) + 1)
            img.paste(Image.new("RGB", (BW, BH), col), (0, 0), mask)
        self.big = img
        rnd = random.Random(seed)
        self.parts = [(rnd.random() * W, rnd.random() * H, rnd.uniform(6, 22), rnd.uniform(1.5, 4.5),
                       rnd.uniform(0, 6.28)) for _ in range(38)]

    def frame(self, t: float) -> Image.Image:
        dx = (self.big.width - self.W) * (0.5 + 0.5 * math.sin(t * 0.05))
        dy = (self.big.height - self.H) * (0.5 + 0.5 * math.cos(t * 0.04))
        img = self.big.crop((int(dx), int(dy), int(dx) + self.W, int(dy) + self.H))
        d = ImageDraw.Draw(img)
        for x, y, sp, r, ph in self.parts:
            yy = (y - t * sp) % self.H
            xx = x + math.sin(t * 0.6 + ph) * 14
            tw = 0.5 + 0.5 * math.sin(t * 1.3 + ph)
            c = int(70 + 70 * tw)
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(c, int(c * 0.8), int(c * 0.4)))
        return img


# ---------------------------------------------------------------------------
# âm lượng theo khung hình (cho cột sóng nhạc)
# ---------------------------------------------------------------------------
def levels(pcm: bytes, fps=FPS) -> list[float]:
    a = array("h")
    a.frombytes(pcm[: len(pcm) // 2 * 2])
    step = SR // fps
    out = []
    for i in range(0, len(a), step):
        w = a[i:i + step]
        if not w:
            break
        out.append(math.sqrt(sum(v * v for v in w[::4]) / max(1, len(w[::4]))) / 9000)
    peak = sorted(out)[int(len(out) * 0.95)] if out else 1
    return [clamp(v / (peak or 1)) for v in out]


def eq_bars(d: ImageDraw.ImageDraw, x, y, lvl: float, t: float, color, n=5, w=10, gapx=7, h=46):
    for i in range(n):
        k = 0.45 + 0.55 * abs(math.sin(t * (5 + i * 1.7) + i))
        hh = max(6, int(h * clamp(lvl * k * 1.15)))
        xx = x + i * (w + gapx)
        d.rounded_rectangle([xx, y + h - hh, xx + w, y + h], radius=w // 2, fill=color)


# ---------------------------------------------------------------------------
# phụ đề karaoke
# ---------------------------------------------------------------------------
def karaoke(canvas: Image.Image, d: ImageDraw.ImageDraw, W, H, words: list[str], prog: float, fnt, max_w,
            bottom, hi=(255, 200, 61), on=(255, 255, 255), off=(214, 208, 198), max_lines=2):
    """Phụ đề: chữ đã/đang đọc trắng, chữ đang đọc tô vàng, chữ sắp đọc trắng ngà; nền đen trong suốt."""
    if not words:
        return
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if cur and d.textlength(test, font=fnt) > max_w:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    if len(lines) == 2 and len(lines[1]) == 1 and len(lines[0]) > 2:   # tránh 1 chữ lẻ dòng dưới
        lines[1].insert(0, lines[0].pop())
    lines = lines[:max_lines]
    lens = [len(w) + 1 for ln in lines for w in ln]
    total = sum(lens) or 1
    pos = prog * total
    lh = int(fnt.size * 1.34)
    box_h = lh * len(lines) + 36
    y0 = int(bottom - box_h)
    widths = [d.textlength(" ".join(ln), font=fnt) for ln in lines]
    bw = int(max(widths) + 72)
    x0 = (W - bw) // 2
    box = Image.new("RGBA", (bw, box_h), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, bw - 1, box_h - 1], radius=22, fill=(8, 6, 4, 178))
    canvas.paste(box, (x0, y0), box)
    acc, y = 0, y0 + 16
    sp = d.textlength(" ", font=fnt)
    for ln, lw in zip(lines, widths):
        x = (W - lw) / 2
        for w in ln:
            L = len(w) + 1
            col = on if acc + L <= pos else hi if acc <= pos else off
            d.text((x + 2, y + 3), w, font=fnt, fill=(0, 0, 0))
            d.text((x, y), w, font=fnt, fill=col)
            x += d.textlength(w, font=fnt) + sp
            acc += L
        y += lh


def split_words_chunks(text: str, max_chars: int) -> list[list[str]]:
    sents = re.split(r"(?<=[.!?…])\s+", text.strip())
    chunks = []
    for s in sents:
        words, cur = s.split(), []
        for w in words:
            if cur and len(" ".join(cur + [w])) > max_chars:
                chunks.append(cur)
                cur = [w]
            else:
                cur.append(w)
        if cur:
            chunks.append(cur)
    return chunks


# ---------------------------------------------------------------------------
# số đếm chạy
# ---------------------------------------------------------------------------
NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")


def countup_text(stat: str, p: float) -> str:
    m = NUM_RE.search(stat or "")
    if not m or p >= 1:
        return stat
    raw = m.group(0)
    if raw.count(",") == 1 and len(raw.split(",")[1]) <= 2:      # 1,2 (thập phân kiểu VN)
        dec, val = len(raw.split(",")[1]), float(raw.replace(".", "").replace(",", "."))
        sep_dec = ","
    elif raw.count(".") == 1 and len(raw.split(".")[1]) <= 2:    # 1.5
        dec, val = len(raw.split(".")[1]), float(raw)
        sep_dec = "."
    else:                                                          # 10,000 / 10.000
        dec, val, sep_dec = 0, float(re.sub(r"[.,]", "", raw)), ","
    v = val * ease_out_cubic(p)
    if dec:
        s = f"{v:.{dec}f}".replace(".", sep_dec)
    else:
        s = f"{int(round(v)):,}"
        if "." in raw and "," not in raw:
            s = s.replace(",", ".")
        elif "," not in raw:
            s = s.replace(",", "")
    return stat[: m.start()] + s + stat[m.end():]


# ---------------------------------------------------------------------------
# bộ mã hoá
# ---------------------------------------------------------------------------
class Encoder:
    def __init__(self, path: Path, W: int, H: int, audio_wav: Path, crf: int = 22):
        self.p = subprocess.Popen([
            "ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0", "-i", str(audio_wav),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p",
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-shortest", "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)
        self.path = path

    def write(self, img: Image.Image):
        self.p.stdin.write(img.tobytes())

    def close(self):
        self.p.stdin.close()
        if self.p.wait() != 0:
            raise RuntimeError("ffmpeg lỗi khi mã hoá video")
        return self.path


def write_wav(pcm: bytes, path: Path):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)


def wipe(new: Image.Image, prev: Image.Image, p: float, color=(255, 200, 61)) -> Image.Image:
    """Chuyển cảnh: dải vàng chéo quét từ trái sang phải, lộ cảnh mới phía sau."""
    W, H = new.size
    e = ease_in_out(p)
    band = 160
    bx = int(-band - H * 0.3 + (W + band * 2 + H * 0.3) * e)
    out = new.copy()
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon([(bx + band, 0), (W, 0), (W, H), (bx + band - H * 0.3, H)], fill=255)
    out.paste(prev, (0, 0), mask)
    ImageDraw.Draw(out).polygon([(bx, 0), (bx + band, 0), (bx + band - H * 0.3, H), (bx - H * 0.3, H)],
                                fill=color)
    return out


def render(scenes: list[dict], W: int, H: int, out_path: Path, tmp: Path, crf: int = 22,
           log=print, watermark: tuple | None = None) -> Path:
    """scenes: [{"dur": giây, "pcm": bytes, "draw": fn(canvas, t_local, ctx)}]."""
    pcm = b"".join(s["pcm"] for s in scenes)
    wav = tmp / (out_path.stem + ".wav")
    write_wav(pcm, wav)
    lv = levels(pcm)
    total = sum(s["dur"] for s in scenes)
    bg = Backdrop(W, H)
    enc = Encoder(out_path, W, H, wav, crf)
    t_glob, fidx, prev = 0.0, 0, None
    for si, sc in enumerate(scenes):
        n = int(round(sc["dur"] * FPS))
        last = None
        for k in range(n):
            t = k / FPS
            canvas = bg.frame(t_glob + t)
            ctx = {"t_glob": t_glob + t, "total": total,
                   "lvl": lv[fidx] if fidx < len(lv) else 0.0}
            sc["draw"](canvas, t, ctx)
            if prev is not None and t < 0.42 and sc.get("wipe", True):
                canvas = wipe(canvas, prev, t / 0.42)
            if watermark:
                canvas.paste(watermark[0], watermark[1], watermark[0])
            enc.write(canvas)
            last = canvas
            fidx += 1
        prev = last
        t_glob += n / FPS
        if si % 4 == 0:
            log(f"      … dựng {si + 1}/{len(scenes)} cảnh ({out_path.name})")
    return enc.close()
