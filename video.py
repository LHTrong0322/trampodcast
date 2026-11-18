#!/usr/bin/env python3
"""
Trạm Podcast Crypto — dựng VIDEO tổng hợp tuần bằng lượt Gemini còn dư.

  python video.py daily  --out public       # sau podcast mỗi ngày: làm sẵn "đoạn video của ngày"
                                             # (1 lượt đọc giọng + 1 lượt AI viết)
  python video.py weekly --out public       # Chủ nhật: ghép video ngang 16:9 + cắt video dọc 9:16
         [--backfill N]                      # làm bù đoạn video cho N tập gần nhất còn thiếu

Kết quả tuần: GitHub Release (lưu file) + gửi Telegram để xem trước.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import podcast as P  # noqa: E402

log = P.log
SR = P.SAMPLE_RATE
ROOT = P.ROOT
FONT_DIR = ROOT / "fonts"
WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

# màu: nền tối + vàng phô mai (đồng bộ web)
BG = (20, 16, 12)
PANEL = (36, 29, 22)
CHEESE = (255, 200, 61)
CREAM = (255, 248, 232)
MUTED = (184, 165, 140)
CAT_COLORS = {
    "Pháp lý": (123, 92, 255), "Vĩ mô & Chính trị": (47, 128, 237), "Dòng tiền & ETF": (18, 160, 107),
    "Dự án": (232, 137, 43), "Bảo mật": (229, 72, 77), "Thị trường": (176, 115, 14),
}

TERMS = """THUẬT NGỮ: giữ nguyên thuật ngữ tiếng Anh dân crypto hay dùng (crypto, stablecoin, token,
altcoin, DeFi, ETF, spot, futures, long, short, leverage, liquidation, staking, airdrop, unlock,
TGE, listing, mainnet, L1, L2, DEX, CEX, TVL, market cap, whale, on-chain, RWA, buyback...);
không dịch sang tiếng Việt. Tên tổ chức/luật giữ nguyên (SEC, CFTC, Fed, FOMC, CPI...)."""


# ---------------------------------------------------------------------------
# tiện ích chung
# ---------------------------------------------------------------------------
_fonts: dict = {}


def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    key = (weight, size)
    if key not in _fonts:
        path = FONT_DIR / f"BeVietnamPro-{weight}.ttf"
        _fonts[key] = ImageFont.truetype(str(path), size)
    return _fonts[key]


def ep_date(ep_id: str) -> datetime:
    return datetime.strptime(ep_id[:8], "%Y%m%d").replace(tzinfo=P.VN_TZ)


def date_label(d: datetime) -> str:
    return f"{WEEKDAYS[d.weekday()]} {d.day}/{d.month}"


def pcm_to_wav(pcm: bytes, path: Path):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)


def pcm_to_mp3(pcm: bytes, path: Path):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1",
                    "-i", "pipe:0", "-codec:a", "libmp3lame", "-b:a", "96k", str(path)],
                   input=pcm, check=True)


def file_to_pcm(path: Path) -> bytes:
    return P._ffmpeg_pcm([], path.read_bytes())


def silences(pcm: bytes) -> list[tuple[float, float]]:
    """Tìm các khoảng lặng (để biết chỗ chuyển giữa các tin trong 1 lần đọc)."""
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        pcm_to_wav(pcm, Path(f.name))
        r = subprocess.run(["ffmpeg", "-i", f.name, "-af", "silencedetect=noise=-38dB:d=0.25",
                            "-f", "null", "-"], capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return list(zip(starts, ends))


def split_points(pcm: bytes, texts: list[str]) -> list[tuple[float, float]]:
    """Chia audio của nhiều đoạn văn (đọc liền 1 lần) thành mốc thời gian từng đoạn.
    Ước lượng theo độ dài chữ, rồi 'hít' vào khoảng lặng gần nhất cho khớp."""
    total = len(pcm) / (SR * 2)
    sil = silences(pcm)
    lens = [max(1, len(t)) for t in texts]
    cuts, acc = [], 0
    for L in lens[:-1]:
        acc += L
        guess = total * acc / sum(lens)
        near = [((s + e) / 2, abs((s + e) / 2 - guess)) for s, e in sil
                if abs((s + e) / 2 - guess) < total * 0.12 and (not cuts or (s + e) / 2 > cuts[-1] + 1)]
        cuts.append(min(near, key=lambda x: x[1])[0] if near else guess)
    bounds = [0.0] + cuts + [total]
    return [(bounds[i], bounds[i + 1]) for i in range(len(texts))]


def slice_pcm(pcm: bytes, t0: float, t1: float) -> bytes:
    a, b = int(t0 * SR) * 2, int(t1 * SR) * 2
    return P.clean_chunk(pcm[a:b])


def gap(sec: float) -> bytes:
    return b"\x00\x00" * int(SR * sec)


def load_cfg() -> dict:
    import yaml
    return yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))


def tts_once(gem, cfg, text: str) -> bytes:
    return P.clean_chunk(P.speak_chunk(gem, cfg, [text], 0))


def llm_json(gem, cfg, system: str, prompt: str) -> dict:
    raw = gem.text(cfg["models"]["text"], system, prompt, json_mode=True)
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M)
    return json.loads(raw)


# ---------------------------------------------------------------------------
# 1. ĐOẠN VIDEO CỦA NGÀY
# ---------------------------------------------------------------------------
DAILY_SYSTEM = """Bạn viết lời dẫn cho video tin crypto tiếng Việt (MC {host}, nữ, giọng {region},
tươi tắn, rõ ràng). Lời văn NÓI, sẽ được đọc bằng máy: không markdown, không emoji, không link,
không ký hiệu lạ; số đọc tự nhiên ("1,2 tỷ đô", "tăng 8 phần trăm"); ticker đọc thành tên coin.
""" + TERMS

DAILY_PROMPT = """Các tin nổi bật ngày {date}:
{stories}

Với MỖI tin, viết lại cho video. Trả về DUY NHẤT JSON:
{{"items": [
  {{"headline": "tiêu đề ngắn, tối đa 70 ký tự",
    "hook": "câu giật tít cho video dọc, tối đa 8 từ, gây tò mò nhưng đúng sự thật",
    "key_stat": "con số nổi bật nhất của tin, rất ngắn (vd '$1,2 tỷ', '+18%', '10 triệu HYPE'), để trống nếu không có",
    "key_label": "giải thích con số, tối đa 6 từ",
    "narration": "lời đọc 2-4 câu, khoảng 300-450 ký tự: chuyện gì xảy ra + vì sao investor cần quan tâm"}}
]}}
Giữ đúng thứ tự tin như trên."""


def make_daily(out: Path, cfg: dict, gem, ep: dict) -> bool:
    pc = cfg["podcast"]
    vcfg = cfg.get("video") or {}
    seg_dir = out / "video" / "segments" / ep["id"]
    if (seg_dir / "seg.json").exists():
        log(f"   Đoạn video {ep['id']} đã có — bỏ qua")
        return False
    top = sorted(ep.get("stories", []), key=lambda s: -int(s.get("importance") or 0))
    top = top[: int(vcfg.get("stories_per_day", 3))]
    if not top:
        return False
    d = ep_date(ep["id"])
    brief = json.dumps([{k: s.get(k) for k in ("headline", "detail", "why_it_matters", "tickers",
                                               "is_update")} for s in top], ensure_ascii=False, indent=1)
    data = llm_json(gem, cfg, DAILY_SYSTEM.format(host=pc.get("host_name", "Mai Hương"),
                                                  region=pc.get("region", "Hà Nội")),
                    DAILY_PROMPT.format(date=date_label(d), stories=brief))
    items = data.get("items", [])[: len(top)]
    if not items:
        raise RuntimeError("AI không trả về nội dung video")
    narrs = [P.sanitize_script(it.get("narration", "")) for it in items]
    log(f"   ♪ Đọc đoạn video {ep['id']} ({sum(map(len, narrs))} ký tự, 1 lượt)")
    pcm = tts_once(gem, cfg, "\n\n".join(narrs))
    spans = split_points(pcm, narrs)
    seg_dir.mkdir(parents=True, exist_ok=True)
    pcm_to_mp3(pcm, seg_dir / "seg.mp3")
    meta = {"episode": ep["id"], "date": d.isoformat(), "items": []}
    for it, st, nar, (t0, t1) in zip(items, top, narrs, spans):
        meta["items"].append({
            "headline": it.get("headline") or st.get("headline", ""),
            "hook": it.get("hook", ""), "key_stat": it.get("key_stat", ""),
            "key_label": it.get("key_label", ""), "narration": nar,
            "category": st.get("category", "Thị trường"), "importance": int(st.get("importance") or 3),
            "tickers": st.get("tickers", []), "is_update": bool(st.get("is_update")),
            "sources": st.get("sources", []), "t0": round(t0, 2), "t1": round(t1, 2),
        })
    (seg_dir / "seg.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"   ✓ Đoạn video {ep['id']}: {len(meta['items'])} tin, {len(pcm) / SR / 2:.0f}s")
    return True


def prune_segments(out: Path, keep_days: int = 16):
    base = out / "video" / "segments"
    if not base.exists():
        return
    cutoff = datetime.now(P.VN_TZ) - timedelta(days=keep_days)
    for d in base.iterdir():
        try:
            if ep_date(d.name) < cutoff:
                for f in d.iterdir():
                    f.unlink()
                d.rmdir()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 2. VẼ KHUNG HÌNH
# ---------------------------------------------------------------------------
def wrap(draw, text: str, fnt, max_w: int, max_lines: int = 99) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while draw.textlength(lines[-1] + "…", font=fnt) > max_w and " " in lines[-1]:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "…"
    return lines


def fit_font(draw, text, weight, size, min_size, max_w, max_lines):
    while size > min_size:
        f = font(weight, size)
        if len(wrap(draw, text, f, max_w)) <= max_lines:
            return f, size
        size -= 4
    return font(weight, min_size), min_size


def draw_lines(draw, lines, fnt, x, y, fill, spacing=1.18, anchor_center_w=None):
    lh = int(fnt.size * spacing)
    for ln in lines:
        if anchor_center_w:
            w = draw.textlength(ln, font=fnt)
            draw.text((x + (anchor_center_w - w) / 2, y), ln, font=fnt, fill=fill)
        else:
            draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


_bg_cache: dict = {}


def background(W: int, H: int) -> Image.Image:
    if (W, H) not in _bg_cache:
        img = Image.new("RGB", (W, H), BG)
        glow = Image.new("L", (W, H), 0)
        gd = ImageDraw.Draw(glow)
        r = int(max(W, H) * 0.55)
        for i in range(40, 0, -1):
            rr = int(r * i / 40)
            gd.ellipse([W - rr * 0.7 - rr, -rr * 0.6 - rr * 0.2, W - rr * 0.7 + rr, rr * 1.2],
                       fill=int(26 * (1 - i / 40) + 2))
        img.paste(Image.new("RGB", (W, H), (120, 84, 20)), (0, 0), glow)
        _bg_cache[(W, H)] = img
    return _bg_cache[(W, H)].copy()


_logo_cache: dict = {}


def logo(size: int) -> Image.Image:
    if size not in _logo_cache:
        src = Image.open(ROOT / "cover.png").convert("RGBA").resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
        src.putalpha(mask)
        _logo_cache[size] = src
    return _logo_cache[size]


def chip(draw, x, y, text, color, fnt, pad=(18, 8)):
    w = draw.textlength(text, font=fnt)
    h = fnt.size + pad[1] * 2
    draw.rounded_rectangle([x, y, x + w + pad[0] * 2, y + h], radius=h // 2, fill=color)
    draw.text((x + pad[0], y + pad[1] - 2), text, font=fnt, fill=(255, 255, 255))
    return x + w + pad[0] * 2


def brand_bar(img, draw, W, sub: str, vertical=False):
    s = 92 if vertical else 76
    img.paste(logo(s), (60, 50), logo(s))
    f1, f2 = font("ExtraBold", 40 if vertical else 34), font("Regular", 28 if vertical else 24)
    draw.text((60 + s + 22, 54 + (8 if vertical else 2)), "TRẠM PODCAST CRYPTO", font=f1, fill=CREAM)
    draw.text((60 + s + 22, 54 + (60 if vertical else 46)), sub, font=f2, fill=MUTED)


def progress(draw, W, H, frac, vertical=False):
    y = H - (14 if not vertical else 18)
    draw.rectangle([0, y, W, H], fill=(48, 39, 30))
    draw.rectangle([0, y, int(W * max(0, min(1, frac))), H], fill=CHEESE)


def subtitle_box(draw, W, H, text, vertical=False):
    if not text:
        return
    fnt = font("SemiBold", 50 if vertical else 44)
    max_w = W - (160 if vertical else 360)
    lines = wrap(draw, text, fnt, max_w, 3 if vertical else 2)
    lh = int(fnt.size * 1.3)
    box_h = lh * len(lines) + 44
    y0 = H - (330 if vertical else 70) - box_h
    draw.rounded_rectangle([(W - max_w) / 2 - 36, y0, (W + max_w) / 2 + 36, y0 + box_h],
                           radius=26, fill=(0, 0, 0))
    y = y0 + 20
    for ln in lines:
        w = draw.textlength(ln, font=fnt)
        draw.text(((W - w) / 2, y), ln, font=fnt, fill=(255, 255, 255))
        y += lh


def story_frame_h(item, sub, week_label, idx, total, frac):
    W, H = 1920, 1080
    img = background(W, H)
    d = ImageDraw.Draw(img)
    brand_bar(img, d, W, week_label)
    fc = font("Bold", 28)
    d.text((W - 60 - d.textlength(f"{idx:02d}/{total:02d}", font=font("ExtraBold", 40)), 62),
           f"{idx:02d}/{total:02d}", font=font("ExtraBold", 40), fill=CHEESE)
    x = chip(d, 120, 230, item["category"], CAT_COLORS.get(item["category"], (176, 115, 14)), fc)
    if item.get("is_update"):
        x = chip(d, x + 14, 230, "CẬP NHẬT", (11, 110, 79), fc)
    d.text((x + 22, 238), date_label(datetime.fromisoformat(item["date"])), font=font("Regular", 30), fill=MUTED)
    stat = (item.get("key_stat") or "").strip()
    head_w = 1080 if stat else 1680
    hf, _ = fit_font(d, item["headline"], "ExtraBold", 78, 52, head_w, 3)
    y = draw_lines(d, wrap(d, item["headline"], hf, head_w, 3), hf, 120, 310, CREAM)
    tick = [f"${str(t).lstrip('$')}" for t in (item.get("tickers") or [])[:4]]
    if tick:
        xx = 120
        for t in tick:
            xx = chip(d, xx, y + 24, t, (58, 47, 35), font("Bold", 28)) + 12
    if stat:
        sf, _ = fit_font(d, stat, "ExtraBold", 150, 70, 560, 1)
        sx = 1280
        d.rounded_rectangle([sx, 290, 1800, 640], radius=36, fill=PANEL, outline=(80, 64, 40), width=2)
        sw = d.textlength(stat, font=sf)
        d.text((sx + (520 - sw) / 2, 330 + (150 - sf.size) / 2), stat, font=sf, fill=CHEESE)
        lf = font("SemiBold", 34)
        draw_lines(d, wrap(d, item.get("key_label", ""), lf, 440, 2), lf, sx + 40, 520, MUTED,
                   anchor_center_w=440)
    subtitle_box(d, W, H, sub)
    progress(d, W, H, frac)
    return img


def story_frame_v(item, sub, frac, week_label):
    W, H = 1080, 1920
    img = background(W, H)
    d = ImageDraw.Draw(img)
    brand_bar(img, d, W, week_label, vertical=True)
    fc = font("Bold", 32)
    x = chip(d, 70, 250, item["category"], CAT_COLORS.get(item["category"], (176, 115, 14)), fc)
    if item.get("is_update"):
        chip(d, x + 14, 250, "CẬP NHẬT", (11, 110, 79), fc)
    hook = (item.get("hook") or item["headline"]).strip()
    hk, _ = fit_font(d, hook.upper(), "ExtraBold", 96, 60, W - 140, 3)
    y = draw_lines(d, wrap(d, hook.upper(), hk, W - 140, 3), hk, 70, 340, CHEESE, 1.12)
    hf = font("SemiBold", 46)
    y = draw_lines(d, wrap(d, item["headline"], hf, W - 140, 3), hf, 70, y + 26, CREAM, 1.25)
    stat = (item.get("key_stat") or "").strip()
    if stat:
        sf, _ = fit_font(d, stat, "ExtraBold", 170, 80, W - 200, 1)
        y0 = max(y + 50, 900)
        d.rounded_rectangle([70, y0, W - 70, y0 + 330], radius=40, fill=PANEL, outline=(80, 64, 40), width=2)
        sw = d.textlength(stat, font=sf)
        d.text(((W - sw) / 2, y0 + 40 + (170 - sf.size) / 2), stat, font=sf, fill=CHEESE)
        lf = font("SemiBold", 38)
        draw_lines(d, wrap(d, item.get("key_label", ""), lf, W - 260, 1), lf, 130, y0 + 245, MUTED,
                   anchor_center_w=W - 260)
    subtitle_box(d, W, H, sub, vertical=True)
    cf = font("Bold", 34)
    cta = "Xem full tổng hợp tuần · Agent build by @Trong0322"
    d.text(((W - d.textlength(cta, font=cf)) / 2, H - 120), cta, font=cf, fill=MUTED)
    progress(d, W, H, frac, vertical=True)
    return img


def title_frame_h(title, week_label, host):
    W, H = 1920, 1080
    img = background(W, H)
    d = ImageDraw.Draw(img)
    img.paste(logo(260), (120, 200), logo(260))
    d.text((120, 520), "TỔNG HỢP TUẦN", font=font("ExtraBold", 44), fill=CHEESE)
    d.text((120, 580), week_label.replace("Tổng hợp tuần ", ""), font=font("SemiBold", 40), fill=MUTED)
    tf, _ = fit_font(d, title, "ExtraBold", 92, 60, 1680, 3)
    draw_lines(d, wrap(d, title, tf, 1680, 3), tf, 120, 660, CREAM, 1.12)
    d.text((W - 60 - d.textlength(f"MC {host}", font=font("SemiBold", 32)), 990), f"MC {host}",
           font=font("SemiBold", 32), fill=MUTED)
    progress(d, W, H, 0)
    return img


def chart_frame_h(prices, week_label, frac):
    W, H = 1920, 1080
    img = background(W, H)
    d = ImageDraw.Draw(img)
    brand_bar(img, d, W, week_label)
    d.text((120, 200), "Thị trường trong tuần", font=font("ExtraBold", 64), fill=CREAM)
    boxes = [(120, 320, 930, 960), (990, 320, 1800, 960)]
    for (sym, series), (x0, y0, x1, y1) in zip(prices.items(), boxes):
        d.rounded_rectangle([x0, y0, x1, y1], radius=36, fill=PANEL)
        first, last = series[0], series[-1]
        ch = (last / first - 1) * 100
        col = (34, 197, 94) if ch >= 0 else (239, 68, 68)
        d.text((x0 + 40, y0 + 34), sym, font=font("ExtraBold", 54), fill=CREAM)
        price = f"${last:,.0f}" if last > 100 else f"${last:,.2f}"
        d.text((x0 + 40, y0 + 104), price, font=font("Bold", 44), fill=CREAM)
        pct = f"{'+' if ch >= 0 else ''}{ch:.1f}%".replace(".", ",")
        d.text((x1 - 40 - d.textlength(pct, font=font("ExtraBold", 54)), y0 + 34), pct,
               font=font("ExtraBold", 54), fill=col)
        cx0, cy0, cx1, cy1 = x0 + 40, y0 + 200, x1 - 40, y1 - 50
        lo, hi = min(series), max(series)
        rng = (hi - lo) or 1
        pts = [(cx0 + (cx1 - cx0) * i / (len(series) - 1), cy1 - (cy1 - cy0) * (v - lo) / rng)
               for i, v in enumerate(series)]
        d.polygon(pts + [(cx1, cy1), (cx0, cy1)], fill=(col[0] // 5 + 20, col[1] // 5 + 16, col[2] // 5 + 12))
        d.line(pts, fill=col, width=6, joint="curve")
    d.text((120, 990), "Nguồn giá: CoinGecko · 7 ngày", font=font("Regular", 26), fill=MUTED)
    progress(d, W, H, frac)
    return img


def outro_frame(vertical=False):
    W, H = (1080, 1920) if vertical else (1920, 1080)
    img = background(W, H)
    d = ImageDraw.Draw(img)
    s = 300 if vertical else 240
    img.paste(logo(s), ((W - s) // 2, int(H * 0.22)), logo(s))
    y = int(H * 0.22) + s + 50
    for text, f, c in [("TRẠM PODCAST CRYPTO", font("ExtraBold", 64 if vertical else 58), CHEESE),
                       ("Đăng ký kênh để nhận tổng hợp crypto mỗi tuần", font("SemiBold", 40 if vertical else 36), CREAM),
                       ("Agent build by @Trong0322", font("Bold", 36 if vertical else 32), MUTED),
                       ("Nội dung do AI tổng hợp · không phải lời khuyên đầu tư", font("Regular", 30 if vertical else 26), MUTED)]:
        for ln in wrap(d, text, f, W - 160):
            d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=c)
            y += int(f.size * 1.35)
        y += 18
    return img


def sub_chunks(text: str, max_len: int) -> list[str]:
    out = []
    for sent in re.split(r"(?<=[.!?…])\s+", text.strip()):
        while len(sent) > max_len:
            cut = sent.rfind(",", 0, max_len)
            cut = cut + 1 if cut > max_len * 0.4 else (sent.rfind(" ", 0, max_len) or max_len)
            out.append(sent[:cut].strip())
            sent = sent[cut:].strip()
        if sent:
            out.append(sent)
    return out


# ---------------------------------------------------------------------------
# 3. GHÉP VIDEO
# ---------------------------------------------------------------------------
class Timeline:
    """Danh sách (ảnh, thời lượng) + audio ghép song song."""

    def __init__(self, tmp: Path, name: str):
        self.tmp, self.name = tmp, name
        self.frames: list[tuple[Path, float]] = []
        self.audio = b""
        self.n = 0

    def add_frame(self, img: Image.Image, dur: float):
        p = self.tmp / f"{self.name}_{self.n:04d}.png"
        self.n += 1
        img.save(p)
        self.frames.append((p, max(0.04, dur)))

    def duration(self) -> float:
        return len(self.audio) / SR / 2

    def render(self, out_mp4: Path, crf: int = 27):
        lst = self.tmp / f"{self.name}.txt"
        with open(lst, "w") as f:
            for p, dur in self.frames:
                f.write(f"file '{p}'\nduration {dur:.3f}\n")
            f.write(f"file '{self.frames[-1][0]}'\n")
        wav = self.tmp / f"{self.name}.wav"
        pcm_to_wav(self.audio, wav)
        subprocess.run([
            "ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
            "-i", str(wav), "-vf", "fps=24,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", str(crf),
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-shortest", "-movflags", "+faststart", str(out_mp4)], check=True)
        return out_mp4


def add_story(tl: Timeline, pcm: bytes, item, make_frame, total_dur: float, max_len: int):
    """Thêm 1 tin: phụ đề đổi theo từng câu, thời lượng chia theo độ dài chữ."""
    dur = len(pcm) / SR / 2
    chunks = sub_chunks(item["narration"], max_len) or [""]
    lens = [max(1, len(c)) for c in chunks]
    start = tl.duration()
    acc = 0.0
    for c, L in zip(chunks, lens):
        part = dur * L / sum(lens)
        tl.add_frame(make_frame(c, (start + acc) / total_dur), part)
        acc += part
    tl.audio += pcm


def fetch_prices() -> dict:
    out = {}
    for sym, cid, cb in [("BTC", "bitcoin", "BTC-USD"), ("ETH", "ethereum", "ETH-USD")]:
        try:
            r = requests.get(f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart",
                             params={"vs_currency": "usd", "days": 7}, timeout=20,
                             headers={"User-Agent": P.UA})
            r.raise_for_status()
            out[sym] = [p[1] for p in r.json()["prices"]][::6]
        except Exception:
            try:
                r = requests.get(f"https://api.exchange.coinbase.com/products/{cb}/candles",
                                 params={"granularity": 21600}, timeout=20, headers={"User-Agent": P.UA})
                r.raise_for_status()
                out[sym] = [c[4] for c in sorted(r.json())][-28:]
            except Exception as ex:
                log(f"   ! không lấy được giá {sym}: {ex}")
    return out if len(out) == 2 and all(len(v) > 3 for v in out.values()) else {}


WEEKLY_SYSTEM = """Bạn là biên tập viên video "tổng hợp crypto tuần" tiếng Việt cho nhà đầu tư.
MC {host} (nữ, giọng {region}). Lời văn NÓI, đọc bằng máy: không markdown, không emoji, không
link; số đọc tự nhiên. """ + TERMS

WEEKLY_PROMPT = """Các tin đã làm video trong tuần {week} (mỗi tin có số [id]):
{items}

Nhiệm vụ:
1. Chọn tối đa {max_items} tin quan trọng nhất tuần để đưa vào video, sắp xếp hợp lý (tin nóng
   nhất trước, gom tin liên quan gần nhau). Bỏ tin trùng sự kiện (giữ bản mới nhất).
2. Chọn {n_shorts} tin "viral" nhất để cắt video dọc (Reels/Shorts).
3. Viết lời mở đầu (~350 ký tự): chào cả nhà, giới thiệu tổng hợp tuần {week}, điểm 2-3 tin nóng.
4. Viết lời kết (~260 ký tự): chốt tâm lý thị trường tuần, nhắc "không phải lời khuyên đầu tư",
   mời đăng ký kênh.
5. Tiêu đề video YouTube hấp dẫn (≤ 90 ký tự, đúng chính tả) và mô tả ngắn (2-3 câu).

Trả về DUY NHẤT JSON:
{{"title": "...", "description": "...", "intro": "...", "outro": "...",
  "order": [id, ...], "shorts": [id, ...]}}"""


def youtube_chapters(marks: list[tuple[float, str]]) -> str:
    lines = []
    for t, label in marks:
        m, s = divmod(int(t), 60)
        lines.append(f"{m:02d}:{s:02d} {label}")
    return "\n".join(lines)


def make_weekly(out: Path, cfg: dict, gem, days: int = 7) -> dict:
    pc, vcfg = cfg["podcast"], (cfg.get("video") or {})
    base = out / "video" / "segments"
    now = datetime.now(P.VN_TZ)
    segs = []
    for d in sorted(base.iterdir()) if base.exists() else []:
        if (d / "seg.json").exists() and ep_date(d.name) >= now - timedelta(days=days):
            meta = json.loads((d / "seg.json").read_text(encoding="utf-8"))
            meta["pcm"] = file_to_pcm(d / "seg.mp3")
            segs.append(meta)
    pool = []
    for s in segs:
        for it in s["items"]:
            it = dict(it, date=s["date"])
            it["pcm"] = slice_pcm(s["pcm"], it["t0"], it["t1"])
            pool.append(it)
    if not pool:
        raise RuntimeError("Chưa có đoạn video nào trong tuần (cần chạy daily hoặc --backfill)")
    d0 = min(datetime.fromisoformat(s["date"]) for s in segs)
    week = f"{d0.day}/{d0.month} – {now.day}/{now.month}"
    listing = "\n".join(f"[{i}] ({date_label(datetime.fromisoformat(it['date']))}, {it['category']}, "
                        f"quan trọng {it['importance']}/5) {it['headline']}: {it['narration'][:260]}"
                        for i, it in enumerate(pool))
    n_shorts = int(vcfg.get("shorts", 4))
    plan = llm_json(gem, cfg, WEEKLY_SYSTEM.format(host=pc.get("host_name", "Mai Hương"),
                                                   region=pc.get("region", "Hà Nội")),
                    WEEKLY_PROMPT.format(week=week, items=listing, n_shorts=n_shorts,
                                         max_items=int(vcfg.get("max_weekly_stories", 12))))
    order = [i for i in plan.get("order", []) if isinstance(i, int) and 0 <= i < len(pool)]
    order = list(dict.fromkeys(order)) or list(range(len(pool)))
    shorts = [i for i in plan.get("shorts", []) if isinstance(i, int) and 0 <= i < len(pool)][:n_shorts]
    intro, outro = P.sanitize_script(plan.get("intro", "")), P.sanitize_script(plan.get("outro", ""))
    log(f"   ♪ Đọc lời mở + kết ({len(intro) + len(outro)} ký tự, 1 lượt)")
    io_pcm = tts_once(gem, cfg, intro + "\n\n" + outro)
    (a0, a1), (b0, b1) = split_points(io_pcm, [intro, outro])
    intro_pcm, outro_pcm = slice_pcm(io_pcm, a0, a1), slice_pcm(io_pcm, b0, b1)

    tmp = Path(tempfile.mkdtemp())
    result_dir = out / "video" / "weekly"
    result_dir.mkdir(parents=True, exist_ok=True)
    tag = now.strftime("%Y%m%d")
    title = plan.get("title") or f"Tổng hợp crypto tuần {week}"
    wl = f"Tổng hợp tuần {week}"

    # ---- video ngang 16:9 ----
    T = 0.5
    total = (len(intro_pcm) + len(outro_pcm) + sum(len(pool[i]["pcm"]) for i in order)) / SR / 2 \
        + T * (len(order) + 2) + 2.5
    tl = Timeline(tmp, "h")
    marks = [(0, "Mở đầu")]
    prices = fetch_prices()
    idur = len(intro_pcm) / SR / 2
    if prices:
        tl.add_frame(title_frame_h(title, wl, pc.get("host_name", "")), idur * 0.5)
        tl.add_frame(chart_frame_h(prices, wl, idur * 0.5 / total), idur * 0.5 + T)
    else:
        tl.add_frame(title_frame_h(title, wl, pc.get("host_name", "")), idur + T)
    tl.audio += intro_pcm + gap(T)
    for k, i in enumerate(order, 1):
        it = pool[i]
        marks.append((tl.duration(), it["headline"][:70]))
        add_story(tl, it["pcm"], it, lambda sub, fr, it=it, k=k: story_frame_h(it, sub, wl, k, len(order), fr),
                  total, 95)
        tl.frames[-1] = (tl.frames[-1][0], tl.frames[-1][1] + T)
        tl.audio += gap(T)
    marks.append((tl.duration(), "Tổng kết"))
    tl.add_frame(outro_frame(), len(outro_pcm) / SR / 2 + 2.5)
    tl.audio += outro_pcm + gap(2.5)
    h_mp4 = tl.render(result_dir / f"tong-hop-tuan-{tag}-16x9.mp4")
    log(f"   ✓ Video ngang: {tl.duration() / 60:.1f} phút, {h_mp4.stat().st_size / 1e6:.1f} MB")

    # ---- video dọc 9:16 ----
    v_files = []
    for n, i in enumerate(shorts, 1):
        it = pool[i]
        tv = Timeline(tmp, f"v{n}")
        dur = len(it["pcm"]) / SR / 2 + 2.2
        add_story(tv, it["pcm"], it, lambda sub, fr, it=it: story_frame_v(it, sub, fr, wl), dur, 70)
        tv.add_frame(outro_frame(vertical=True), 2.2)
        tv.audio += gap(2.2)
        v = tv.render(result_dir / f"short-{tag}-{n}.mp4")
        v_files.append((v, it))
        log(f"   ✓ Short {n}: {tv.duration():.0f}s, {v.stat().st_size / 1e6:.1f} MB")

    desc = (plan.get("description", "") + "\n\n" + youtube_chapters(marks) +
            "\n\nAgent build by @Trong0322 · Nội dung do AI tổng hợp, không phải lời khuyên đầu tư.")
    return {"tag": tag, "title": title, "description": desc, "week": week,
            "h": h_mp4, "shorts": v_files}


# ---------------------------------------------------------------------------
# 4. GỬI ĐI: GitHub Release + Telegram
# ---------------------------------------------------------------------------
def publish_release(res: dict) -> str:
    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo or not os.getenv("GH_TOKEN"):
        return ""
    tag = f"weekly-{res['tag']}"
    notes = f"# {res['title']}\n\n{res['description']}"
    files = [str(res["h"])] + [str(v) for v, _ in res["shorts"]]
    subprocess.run(["gh", "release", "delete", tag, "-y", "--cleanup-tag", "-R", repo], capture_output=True)
    subprocess.run(["gh", "release", "create", tag, *files, "-R", repo, "--title", res["title"][:120],
                    "--notes", notes], check=True)
    return f"https://github.com/{repo}/releases/tag/{tag}"


def send_telegram_videos(res: dict, release_url: str):
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        log("   ! Chưa cài TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID — không gửi Telegram")
        return
    api = f"https://api.telegram.org/bot{token}"
    esc = P.html.escape

    def send_video(path: Path, caption: str, w: int, h: int):
        if path.stat().st_size > 49_000_000:
            requests.post(f"{api}/sendMessage", timeout=60, data={
                "chat_id": chat, "parse_mode": "HTML",
                "text": caption + f"\n\n(File lớn hơn 50MB, tải tại: {esc(release_url)})"})
            return
        with open(path, "rb") as f:
            r = requests.post(f"{api}/sendVideo", timeout=600, data={
                "chat_id": chat, "caption": caption[:1000], "parse_mode": "HTML",
                "supports_streaming": "true", "width": w, "height": h},
                files={"video": (path.name, f, "video/mp4")})
        if not r.ok:
            log(f"   ! Telegram sendVideo lỗi: {r.text[:200]}")

    requests.post(f"{api}/sendMessage", timeout=60, data={
        "chat_id": chat, "parse_mode": "HTML", "disable_web_page_preview": "true",
        "text": (f"🎬 <b>Video tổng hợp tuần {esc(res['week'])}</b> — bản xem trước\n"
                 f"1 video ngang 16:9 (YouTube) + {len(res['shorts'])} video dọc 9:16 (Reels/Shorts)\n"
                 + (f"📦 Tải file gốc: {esc(release_url)}" if release_url else ""))})
    send_video(res["h"], f"<b>{esc(res['title'])}</b>\n16:9 · YouTube", 1920, 1080)
    for n, (v, it) in enumerate(res["shorts"], 1):
        send_video(v, f"Short {n}: <b>{esc(it.get('hook') or it['headline'])}</b>\n9:16 · Reels/Shorts/TikTok",
                   1080, 1920)
    for chunk in [res["description"][i:i + 3800] for i in range(0, len(res["description"]), 3800)]:
        requests.post(f"{api}/sendMessage", timeout=60, data={
            "chat_id": chat, "text": f"📝 Gợi ý tiêu đề + mô tả YouTube:\n\n{res['title']}\n\n{chunk}"})
    log("   ✓ Đã gửi video vào Telegram")


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["daily", "weekly"])
    ap.add_argument("--out", default="public")
    ap.add_argument("--backfill", type=int, default=0, help="làm bù đoạn video cho N tập gần nhất")
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()
    out = Path(args.out)
    cfg = load_cfg()
    if not (cfg.get("video") or {}).get("enabled", True):
        log("Video đang tắt trong sources.yaml")
        return
    gem = P.Gemini(os.getenv("GEMINI_API_KEY", ""))
    eps_path = out / "episodes.json"
    episodes = json.loads(eps_path.read_text()) if eps_path.exists() else []
    if args.mode == "daily":
        if episodes:
            make_daily(out, cfg, gem, episodes[0])
        prune_segments(out)
        return
    # weekly
    if args.backfill:
        done = 0
        for ep in episodes[: args.backfill]:
            try:
                if make_daily(out, cfg, gem, ep):
                    done += 1
                    time.sleep(int(cfg["podcast"].get("tts_pause_seconds", 25)))
            except Exception as ex:
                log(f"   ! Làm bù {ep['id']} lỗi: {ex}")
                if "hết lượt" in str(ex):
                    break
        log(f"   Làm bù {done} đoạn video")
    res = make_weekly(out, cfg, gem, args.days)
    url = ""
    try:
        url = publish_release(res)
        if url:
            log(f"   ✓ GitHub Release: {url}")
    except Exception as ex:
        log(f"   ! Tạo Release lỗi: {ex}")
    send_telegram_videos(res, url)
    log("✓ Xong video tuần!")


if __name__ == "__main__":
    main()
