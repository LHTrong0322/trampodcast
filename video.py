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
import math
import os
import random
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
import motion as M  # noqa: E402
from motion import Layer  # noqa: E402

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
    "visual_query": "2-4 từ TIẾNG ANH mô tả ảnh minh hoạ phù hợp để tìm ảnh stock (vd 'US Capitol building', 'stock exchange trading floor', 'hacker laptop dark', 'Federal Reserve building'); không dùng tên coin",
    "visual_fallback": "1 từ khoá tiếng Anh chung hơn cho ảnh (vd 'finance', 'technology', 'government')",
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
            "visual_query": it.get("visual_query", ""), "visual_fallback": it.get("visual_fallback", ""),
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
# 2. HÌNH ẢNH: tự tìm ảnh hợp từng tin (ảnh được phép dùng) + logo coin
# ---------------------------------------------------------------------------
IMG_CACHE = Path(tempfile.gettempdir()) / "tpc_img"
_used: set = set()  # không dùng lại 1 ảnh 2 lần trong cùng video


def _get(url, **kw):
    kw.setdefault("timeout", 25)
    kw.setdefault("headers", {"User-Agent": "TramPodcastCrypto/1.0 (video bot)"})
    r = requests.get(url, **kw)
    r.raise_for_status()
    return r


def _download(url: str) -> Image.Image | None:
    IMG_CACHE.mkdir(exist_ok=True)
    p = IMG_CACHE / (P.item_id(url) + ".img")
    try:
        if not p.exists():
            p.write_bytes(_get(url).content)
        im = Image.open(p)
        im.load()
        return im.convert("RGB")
    except Exception as ex:
        log(f"      ! tải ảnh lỗi: {ex}")
        return None


def search_pexels(query: str, orientation: str) -> tuple[Image.Image, str] | None:
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return None
    try:
        r = _get("https://api.pexels.com/v1/search", headers={"Authorization": key},
                 params={"query": query, "orientation": orientation, "per_page": 8, "size": "large"})
        for ph in r.json().get("photos", []):
            src = ph["src"].get("large2x") or ph["src"]["original"]
            if src in _used:
                continue
            im = _download(src)
            if im and min(im.size) >= 700:
                _used.add(src)
                return im, f"Ảnh: {ph.get('photographer', '')} / Pexels"
    except Exception as ex:
        log(f"      ! Pexels lỗi: {ex}")
    return None


def search_pixabay(query: str, orientation: str) -> tuple[Image.Image, str] | None:
    key = os.getenv("PIXABAY_API_KEY")
    if not key:
        return None
    try:
        r = _get("https://pixabay.com/api/", params={
            "key": key, "q": query[:100], "image_type": "photo", "safesearch": "true", "per_page": 10,
            "orientation": "horizontal" if orientation == "landscape" else "vertical"})
        for h in r.json().get("hits", []):
            url = h.get("largeImageURL") or h.get("webformatURL")
            if url in _used:
                continue
            im = _download(url)
            if im and min(im.size) >= 700:
                _used.add(url)
                return im, f"Ảnh: {h.get('user', '')} / Pixabay"
    except Exception as ex:
        log(f"      ! Pixabay lỗi: {ex}")
    return None


def search_openverse(query: str, orientation: str) -> tuple[Image.Image, str] | None:
    """Kho ảnh Creative Commons (Flickr, Wikimedia, bảo tàng...). Không cần key nhưng giới hạn lượt."""
    try:
        r = _get("https://api.openverse.org/v1/images/", params={
            "q": query, "license_type": "commercial,modification", "size": "large", "page_size": 10,
            "aspect_ratio": "wide" if orientation == "landscape" else "tall", "mature": "false"})
        for h in r.json().get("results", []):
            url = h.get("url")
            if not url or url in _used:
                continue
            im = _download(url)
            if im and min(im.size) >= 700:
                _used.add(url)
                lic = f"CC {str(h.get('license', '')).upper()} {h.get('license_version', '')}".strip()
                return im, f"Ảnh: {(h.get('creator') or '')[:30]} / {h.get('source', 'Openverse')} ({lic})"
    except Exception as ex:
        log(f"      ! Openverse lỗi: {ex}")
    return None


def search_wikimedia(query: str) -> tuple[Image.Image, str] | None:
    try:
        r = _get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
            "gsrsearch": f"filetype:bitmap {query}", "gsrlimit": 10, "prop": "imageinfo",
            "iiprop": "url|size|extmetadata", "iiurlwidth": 1920})
        pages = sorted(r.json().get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
        for pg in pages:
            ii = (pg.get("imageinfo") or [{}])[0]
            if ii.get("width", 0) < 1000 or ii.get("width", 0) < ii.get("height", 1) * 0.9:
                continue
            meta = ii.get("extmetadata", {})
            lic = meta.get("LicenseShortName", {}).get("value", "")
            if not re.search(r"CC|Public domain|PD", lic, re.I):
                continue
            url = ii.get("thumburl") or ii["url"]
            if url in _used:
                continue
            im = _download(url)
            if im:
                _used.add(url)
                artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))[:40]
                return im, f"Ảnh: {artist} / Wikimedia Commons ({lic})"
    except Exception as ex:
        log(f"      ! Wikimedia lỗi: {ex}")
    return None


def find_image(item: dict, orientation: str) -> tuple[Image.Image, str] | None:
    queries = [q for q in [item.get("visual_query"), item.get("visual_fallback")] if q]
    queries.append({"Pháp lý": "government building law", "Vĩ mô & Chính trị": "stock market finance",
                    "Dòng tiền & ETF": "wall street finance", "Dự án": "technology blockchain",
                    "Bảo mật": "cyber security hacker", "Thị trường": "trading chart screen"}
                   .get(item.get("category"), "cryptocurrency"))
    for q in queries:
        res = (search_pexels(q, orientation) or search_pixabay(q, orientation)
               or search_wikimedia(q) or search_openverse(q, orientation))
        if res:
            return res
    return None


_coin_logo: dict = {}


def coin_logo(ticker: str, size: int) -> Image.Image | None:
    t = str(ticker).lstrip("$").upper()
    if t not in _coin_logo:
        _coin_logo[t] = None
        try:
            r = _get("https://api.coingecko.com/api/v3/search", params={"query": t})
            for c in r.json().get("coins", [])[:8]:
                if c.get("symbol", "").upper() == t and c.get("large"):
                    _coin_logo[t] = _download(c["large"].replace("/large/", "/large/"))
                    break
        except Exception:
            pass
    im = _coin_logo[t]
    if im is None:
        return None
    im = im.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    im.putalpha(mask)
    return im


def cover_fit(im: Image.Image, W: int, H: int) -> Image.Image:
    s = max(W / im.width, H / im.height)
    return im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)


class KenBurns:
    """Ảnh nền trôi chậm + phủ tối để chữ dễ đọc."""

    def __init__(self, im: Image.Image, W: int, H: int, region: tuple, vertical: bool, seed: int):
        x0, y0, x1, y1 = region
        rw, rh = x1 - x0, y1 - y0
        big = cover_fit(im, int(rw * 1.18), int(rh * 1.18)).convert("RGB")
        shade = Image.new("L", big.size, 0)
        sd = ImageDraw.Draw(shade)
        if vertical:   # mờ dần xuống dưới
            for y in range(big.height):
                sd.line([(0, y), (big.width, y)], fill=int(40 + 200 * (y / big.height) ** 1.6))
        else:          # tối bên trái (chỗ đặt chữ)
            for x in range(big.width):
                sd.line([(x, 0), (x, big.height)], fill=int(235 - 150 * (x / big.width) ** 0.9))
        big.paste(Image.new("RGB", big.size, (14, 11, 8)), (0, 0), shade)
        self.big, self.region, self.rw, self.rh = big, region, rw, rh
        rnd = random.Random(seed)
        self.dir = (rnd.choice([-1, 1]), rnd.choice([-1, 1]))

    def draw(self, canvas: Image.Image, t: float, dur: float):
        p = M.ease_in_out(t / max(dur, 0.1))
        mx, my = self.big.width - self.rw, self.big.height - self.rh
        x = int(mx * (p if self.dir[0] > 0 else 1 - p))
        y = int(my * (p if self.dir[1] > 0 else 1 - p))
        canvas.paste(self.big.crop((x, y, x + self.rw, y + self.rh)), self.region[:2])


# ---------------------------------------------------------------------------
# 3. VẼ CHỮ / THÀNH PHẦN
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


_measure = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def fit_font(text, weight, size, min_size, max_w, max_lines):
    while size > min_size:
        f = font(weight, size)
        if len(wrap(_measure, text, f, max_w)) <= max_lines:
            return f
        size -= 4
    return font(weight, min_size)


def text_img(text: str, fnt, fill, shadow=True) -> Image.Image:
    w = int(_measure.textlength(text, font=fnt)) + 12
    h = int(fnt.size * 1.35) + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        d.text((4, 5), text, font=fnt, fill=(0, 0, 0, 150))
    d.text((2, 2), text, font=fnt, fill=fill)
    return im


def chip_img(text: str, color, fnt, pad=(20, 9), icon: Image.Image | None = None) -> Image.Image:
    tw = int(_measure.textlength(text, font=fnt))
    ic = icon.size[0] + 10 if icon else 0
    w, h = tw + pad[0] * 2 + ic, fnt.size + pad[1] * 2 + 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=color)
    if icon:
        im.paste(icon, (pad[0] - 6, (h - icon.size[1]) // 2), icon)
    d.text((pad[0] + ic, pad[1] - 2), text, font=fnt, fill=(255, 255, 255))
    return im


def panel_img(w, h, fill=(30, 24, 18, 225), outline=(255, 200, 61, 90), r=36) -> Image.Image:
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=fill, outline=outline, width=2)
    return im


_logo_cache: dict = {}


def logo(size: int) -> Image.Image:
    if size not in _logo_cache:
        src = Image.open(ROOT / "cover.png").convert("RGBA").resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
        src.putalpha(mask)
        _logo_cache[size] = src
    return _logo_cache[size]


def brand_layer(W, sub: str, vertical=False) -> Image.Image:
    s = 92 if vertical else 76
    im = Image.new("RGBA", (W, s + 40), (0, 0, 0, 0))
    im.paste(logo(s), (60, 10), logo(s))
    d = ImageDraw.Draw(im)
    f1, f2 = font("ExtraBold", 40 if vertical else 34), font("Regular", 28 if vertical else 24)
    d.text((60 + s + 22, 14 + (8 if vertical else 2)), "TRẠM PODCAST CRYPTO", font=f1, fill=CREAM)
    d.text((60 + s + 22, 14 + (60 if vertical else 46)), sub, font=f2, fill=MUTED)
    return im


def draw_progress(d, W, H, frac, vertical=False):
    y = H - (10 if not vertical else 14)
    d.rectangle([0, y, W, H], fill=(48, 39, 30))
    d.rectangle([0, y, int(W * M.clamp(frac)), H], fill=CHEESE)


def credit(d, W, H, text, vertical=False):
    if text:
        f = font("Regular", 20 if not vertical else 22)
        d.text((W - 40 - d.textlength(text[:80], font=f), H - (48 if not vertical else 70)), text[:80],
               font=f, fill=(200, 190, 175))


# ---------------------------------------------------------------------------
# 4. CẢNH (scene) — mỗi cảnh trả về hàm vẽ theo thời gian
# ---------------------------------------------------------------------------
def scene_title(title, week, host, dur):
    W, H = 1920, 1080
    L = [Layer(logo(240), 120, 170, "pop", 0.1, 0.7),
         Layer(text_img("TỔNG HỢP TUẦN", font("ExtraBold", 46), CHEESE), 120, 470, "fade_up", 0.35),
         Layer(text_img(week, font("SemiBold", 40), MUTED), 120, 530, "fade_up", 0.45)]
    tf = fit_font(title, "ExtraBold", 92, 60, 1680, 3)
    for i, ln in enumerate(wrap(_measure, title, tf, 1680, 3)):
        L.append(Layer(text_img(ln, tf, CREAM), 116, 620 + i * int(tf.size * 1.15), "fade_up", 0.6 + 0.12 * i))
    L.append(Layer(text_img(f"MC {host}", font("SemiBold", 32), MUTED), 1560, 990, "fade_up", 1.1))

    def draw(c, t, ctx):
        for ly in L:
            ly.draw(c, t)
        d = ImageDraw.Draw(c)
        M.eq_bars(d, 1760, 120, ctx["lvl"], ctx["t_glob"], CHEESE, h=60, w=14, gapx=9)
        draw_progress(d, W, H, ctx["t_glob"] / ctx["total"])
    return draw


def scene_chart(prices, week_label, dur):
    W, H = 1920, 1080
    brand = Layer(brand_layer(W, week_label), 0, 40, "fade_up", 0, 0.4, 20)
    head = Layer(text_img("Thị trường trong tuần", font("ExtraBold", 64), CREAM), 116, 190, "fade_up", 0.15)
    boxes = [(120, 320, 930, 960), (990, 320, 1800, 960)]
    panels = [Layer(panel_img(x1 - x0, y1 - y0, outline=(80, 64, 40, 255)), x0, y0, "slide_up", 0.25 + 0.15 * i, 0.6)
              for i, (x0, y0, x1, y1) in enumerate(boxes)]

    def draw(c, t, ctx):
        brand.draw(c, t)
        head.draw(c, t)
        for p in panels:
            p.draw(c, t)
        d = ImageDraw.Draw(c)
        for i, ((sym, series), (x0, y0, x1, y1)) in enumerate(zip(prices.items(), boxes)):
            pt = (t - 0.6 - 0.15 * i) / 1.8
            if pt <= 0:
                continue
            first, last = series[0], series[-1]
            ch = (last / first - 1) * 100
            col = (34, 197, 94) if ch >= 0 else (239, 68, 68)
            e = M.ease_out_cubic(pt)
            d.text((x0 + 40, y0 + 34), sym, font=font("ExtraBold", 54), fill=CREAM)
            cur_price = first + (last - first) * e
            price = f"${cur_price:,.0f}" if last > 100 else f"${cur_price:,.2f}"
            d.text((x0 + 40, y0 + 104), price, font=font("Bold", 44), fill=CREAM)
            pct = f"{'+' if ch >= 0 else ''}{ch * e:.1f}%".replace(".", ",")
            pf = font("ExtraBold", 54)
            d.text((x1 - 40 - d.textlength(pct, font=pf), y0 + 34), pct, font=pf, fill=col)
            cx0, cy0, cx1, cy1 = x0 + 40, y0 + 200, x1 - 40, y1 - 50
            lo, hi = min(series), max(series)
            rng = (hi - lo) or 1
            n = max(2, int(len(series) * e))
            pts = [(cx0 + (cx1 - cx0) * k / (len(series) - 1), cy1 - (cy1 - cy0) * (v - lo) / rng)
                   for k, v in enumerate(series[:n])]
            d.polygon(pts + [(pts[-1][0], cy1), (cx0, cy1)], fill=(col[0] // 5 + 20, col[1] // 5 + 16, col[2] // 5 + 12))
            d.line(pts, fill=col, width=6, joint="curve")
            px, py = pts[-1]
            r = 10 + 4 * math.sin(ctx["t_glob"] * 6)
            d.ellipse([px - r, py - r, px + r, py + r], fill=col)
        d.text((120, 990), "Nguồn giá: CoinGecko · 7 ngày", font=font("Regular", 26), fill=MUTED)
        draw_progress(d, W, H, ctx["t_glob"] / ctx["total"])
    return draw


def story_layers_h(item, idx, total, week_label, image):
    W, H = 1920, 1080
    L = [Layer(brand_layer(W, week_label), 0, 40, "fade_up", 0, 0.4, 20),
         Layer(text_img(f"{idx:02d}/{total:02d}", font("ExtraBold", 40), CHEESE), 1760, 60, "fade_up", 0.1)]
    fc = font("Bold", 28)
    x = 120
    chips = [chip_img(item["category"], CAT_COLORS.get(item["category"], (176, 115, 14)), fc)]
    if item.get("is_update"):
        chips.append(chip_img("CẬP NHẬT", (11, 110, 79), fc))
    chips.append(text_img(date_label(datetime.fromisoformat(item["date"])), font("SemiBold", 30), MUTED))
    for k, ci in enumerate(chips):
        L.append(Layer(ci, x, 236 if k < len(chips) - 1 else 240, "pop", 0.2 + 0.08 * k, 0.5))
        x += ci.size[0] + 14
    stat = (item.get("key_stat") or "").strip()
    head_w = 1060 if stat else 1640
    hf = fit_font(item["headline"], "ExtraBold", 78, 50, head_w, 3)
    y = 312
    for i, ln in enumerate(wrap(_measure, item["headline"], hf, head_w, 3)):
        L.append(Layer(text_img(ln, hf, CREAM), 116, y, "fade_up", 0.35 + 0.1 * i))
        y += int(hf.size * 1.16)
    xx = 120
    for k, tk in enumerate((item.get("tickers") or [])[:4]):
        ic = coin_logo(tk, 34)
        ci = chip_img(f"${str(tk).lstrip('$')}", (40, 32, 24), font("Bold", 28), icon=ic)
        L.append(Layer(ci, xx, y + 26, "pop", 0.7 + 0.07 * k, 0.45))
        xx += ci.size[0] + 12
    stat_box = None
    if stat:
        stat_box = (1270, 300, 540, 340)
        L.append(Layer(panel_img(540, 340), 1270, 300, "slide_left", 0.45, 0.7))
        lf = font("SemiBold", 32)
        for i, ln in enumerate(wrap(_measure, item.get("key_label", ""), lf, 460, 2)):
            ti = text_img(ln, lf, MUTED, shadow=False)
            L.append(Layer(ti, 1270 + (540 - ti.size[0]) // 2, 520 + i * 42, "fade_up", 1.1))
    kb = KenBurns(image[0], W, H, (0, 0, W, H), False, hash(item["headline"]) & 0xffff) if image else None
    return L, stat, stat_box, kb, (image[1] if image else "")


def scene_story_h(item, idx, total, week_label, dur, image):
    W, H = 1920, 1080
    L, stat, stat_box, kb, cred = story_layers_h(item, idx, total, week_label, image)
    chunks = M.split_words_chunks(item["narration"], 78) or [[]]
    lens = [max(1, len(" ".join(c))) for c in chunks]
    speech = max(0.5, item["speech_dur"])
    bounds, acc = [], 0
    for Lc in lens:
        bounds.append((acc / sum(lens) * speech, (acc + Lc) / sum(lens) * speech))
        acc += Lc
    sf_big = fit_font(stat, "ExtraBold", 140, 64, 480, 1) if stat else None

    def draw(c, t, ctx):
        if kb:
            kb.draw(c, t, dur)
        for ly in L:
            ly.draw(c, t)
        d = ImageDraw.Draw(c)
        if stat:
            p = (t - 0.7) / 1.0
            if p > 0:
                s = M.countup_text(stat, p)
                x0, y0, w, h = stat_box
                sw = d.textlength(s, font=sf_big)
                d.text((x0 + (w - sw) / 2, y0 + 50 + (140 - sf_big.size) / 2), s, font=sf_big, fill=CHEESE)
        for (a, b), ch in zip(bounds, chunks):
            if a <= t < b + (dur - speech if (a, b) == bounds[-1] else 0):
                M.karaoke(d, W, H, ch, (t - a) / max(0.1, b - a), font("SemiBold", 44), 1500, H - 70)
                break
        M.eq_bars(d, 1610, 62, ctx["lvl"], ctx["t_glob"], CHEESE, h=40, w=9, gapx=6)
        credit(d, W, H, cred)
        draw_progress(d, W, H, ctx["t_glob"] / ctx["total"])
    return draw


def scene_story_v(item, dur, week_label, image):
    W, H = 1080, 1920
    L = [Layer(brand_layer(W, week_label, True), 0, 40, "fade_up", 0, 0.4, 20)]
    kb = KenBurns(image[0], W, H, (0, 230, W, 1050), True, hash(item["headline"]) & 0xffff) if image else None
    fc = font("Bold", 32)
    x = 70
    for k, ci in enumerate([chip_img(item["category"], CAT_COLORS.get(item["category"], (176, 115, 14)), fc)] +
                           ([chip_img("CẬP NHẬT", (11, 110, 79), fc)] if item.get("is_update") else [])):
        L.append(Layer(ci, x, 270, "pop", 0.15 + 0.08 * k, 0.5))
        x += ci.size[0] + 14
    hook = (item.get("hook") or item["headline"]).strip().upper()
    hk = fit_font(hook, "ExtraBold", 96, 58, W - 140, 3)
    y = 760
    for i, ln in enumerate(wrap(_measure, hook, hk, W - 140, 3)):
        L.append(Layer(text_img(ln, hk, CHEESE), 66, y, "fade_up", 0.3 + 0.1 * i))
        y += int(hk.size * 1.1)
    hf = font("SemiBold", 44)
    for i, ln in enumerate(wrap(_measure, item["headline"], hf, W - 140, 3)):
        L.append(Layer(text_img(ln, hf, CREAM), 66, y + 20, "fade_up", 0.6 + 0.08 * i))
        y += int(hf.size * 1.25)
    stat = (item.get("key_stat") or "").strip()
    sy = max(y + 50, 1180)
    sf = fit_font(stat, "ExtraBold", 150, 70, W - 260, 1) if stat else None
    if stat:
        L.append(Layer(panel_img(W - 140, 270), 70, sy, "slide_up", 0.8, 0.6))
        lf = font("SemiBold", 34)
        ti = text_img(wrap(_measure, item.get("key_label", ""), lf, W - 260, 1)[0] if item.get("key_label") else "",
                      lf, MUTED, shadow=False)
        L.append(Layer(ti, (W - ti.size[0]) // 2, sy + 200, "fade_up", 1.2))
    cta = text_img("Xem full tổng hợp tuần · @Trong0322", font("Bold", 32), MUTED, shadow=False)
    L.append(Layer(cta, (W - cta.size[0]) // 2, H - 110, "fade_up", 1.0))
    chunks = M.split_words_chunks(item["narration"], 54) or [[]]
    lens = [max(1, len(" ".join(c))) for c in chunks]
    speech = max(0.5, item["speech_dur"])
    bounds, acc = [], 0
    for Lc in lens:
        bounds.append((acc / sum(lens) * speech, (acc + Lc) / sum(lens) * speech))
        acc += Lc
    cred = image[1] if image else ""

    def draw(c, t, ctx):
        if kb:
            kb.draw(c, t, dur)
        for ly in L:
            ly.draw(c, t)
        d = ImageDraw.Draw(c)
        if stat and t > 1.0:
            s = M.countup_text(stat, (t - 1.0) / 1.0)
            sw = d.textlength(s, font=sf)
            d.text(((W - sw) / 2, sy + 30 + (150 - sf.size) / 2), s, font=sf, fill=CHEESE)
        for (a, b), ch in zip(bounds, chunks):
            if a <= t < b + (dur - speech if (a, b) == bounds[-1] else 0):
                M.karaoke(d, W, H, ch, (t - a) / max(0.1, b - a), font("ExtraBold", 54), W - 150, H - 170,
                          max_lines=3)
                break
        M.eq_bars(d, W - 150, 70, ctx["lvl"], ctx["t_glob"], CHEESE, h=56, w=12, gapx=8)
        credit(d, W, H, cred, vertical=True)
        draw_progress(d, W, H, ctx["t_glob"] / ctx["total"], vertical=True)
    return draw


def scene_outro(vertical=False):
    W, H = (1080, 1920) if vertical else (1920, 1080)
    s = 300 if vertical else 240
    L = [Layer(logo(s), (W - s) // 2, int(H * 0.2), "pop", 0.05, 0.7)]
    y = int(H * 0.2) + s + 50
    for k, (text, f, c) in enumerate([
            ("TRẠM PODCAST CRYPTO", font("ExtraBold", 64 if vertical else 58), CHEESE),
            ("Đăng ký kênh để nhận tổng hợp crypto mỗi tuần", font("SemiBold", 40 if vertical else 36), CREAM),
            ("Agent build by @Trong0322", font("Bold", 36 if vertical else 32), MUTED),
            ("Nội dung do AI tổng hợp · không phải lời khuyên đầu tư", font("Regular", 30 if vertical else 26), MUTED)]):
        for ln in wrap(_measure, text, f, W - 160):
            ti = text_img(ln, f, c)
            L.append(Layer(ti, (W - ti.size[0]) // 2, y, "fade_up", 0.35 + 0.15 * k))
            y += int(f.size * 1.35)
        y += 18

    def draw(c, t, ctx):
        for ly in L:
            ly.draw(c, t)
        d = ImageDraw.Draw(c)
        M.eq_bars(d, W // 2 - 44, int(H * 0.2) - 80, ctx["lvl"], ctx["t_glob"], CHEESE, h=50, w=12, gapx=8)
    return draw


# ---------------------------------------------------------------------------
# 5. TUẦN
# ---------------------------------------------------------------------------
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
    T = 0.6  # nghỉ giữa các tin

    log("   🖼  Tìm ảnh minh hoạ cho từng tin")
    for i in set(order) | set(shorts):
        it = pool[i]
        it["speech_dur"] = len(it["pcm"]) / SR / 2
        it["img_h"] = find_image(it, "landscape") if i in order else None
        it["img_v"] = find_image(it, "portrait") if i in shorts else None
        log(f"      [{i}] {it.get('visual_query', '')!r} → {'có ảnh' if (it['img_h'] or it['img_v']) else 'không có'}")

    # ---- video ngang 16:9 ----
    scenes = []
    prices = fetch_prices()
    idur = len(intro_pcm) / SR / 2 + T
    if prices:
        scenes.append({"dur": idur * 0.5, "pcm": intro_pcm[: int(len(intro_pcm) * 0.5) // 2 * 2],
                       "draw": scene_title(title, week, pc.get("host_name", ""), idur * 0.5), "wipe": False})
        rest = intro_pcm[int(len(intro_pcm) * 0.5) // 2 * 2:] + gap(T)
        scenes.append({"dur": len(rest) / SR / 2, "pcm": rest, "draw": scene_chart(prices, wl, len(rest) / SR / 2)})
    else:
        scenes.append({"dur": idur, "pcm": intro_pcm + gap(T),
                       "draw": scene_title(title, week, pc.get("host_name", ""), idur), "wipe": False})
    marks = [(0, "Mở đầu")]
    tcur = sum(s_["dur"] for s_ in scenes)
    for k, i in enumerate(order, 1):
        it = pool[i]
        a_ = it["pcm"] + gap(T)
        dur = len(a_) / SR / 2
        marks.append((tcur, it["headline"][:70]))
        scenes.append({"dur": dur, "pcm": a_, "draw": scene_story_h(it, k, len(order), wl, dur, it["img_h"])})
        tcur += dur
    marks.append((tcur, "Tổng kết"))
    o_ = outro_pcm + gap(2.5)
    scenes.append({"dur": len(o_) / SR / 2, "pcm": o_, "draw": scene_outro()})
    # làm tròn thời lượng theo khung hình để hình & tiếng khớp nhau
    for sc in scenes:
        n = int(round(sc["dur"] * M.FPS))
        need = int(n / M.FPS * SR) * 2
        sc["pcm"] = (sc["pcm"] + gap(1))[:need]
        sc["dur"] = n / M.FPS
    log(f"   🎬 Dựng video ngang ({sum(s_['dur'] for s_ in scenes) / 60:.1f} phút)…")
    t0 = time.time()
    h_mp4 = M.render(scenes, 1920, 1080, result_dir / f"tong-hop-tuan-{tag}-16x9.mp4", tmp, log=log)
    log(f"   ✓ Video ngang: {h_mp4.stat().st_size / 1e6:.1f} MB (dựng mất {time.time() - t0:.0f}s)")

    # ---- video dọc 9:16 ----
    v_files = []
    for n, i in enumerate(shorts, 1):
        it = pool[i]
        a_ = it["pcm"] + gap(0.6)
        dur = len(a_) / SR / 2
        vs = [{"dur": dur, "pcm": a_, "draw": scene_story_v(it, dur, wl, it["img_v"]), "wipe": False},
              {"dur": 2.4, "pcm": gap(2.4), "draw": scene_outro(vertical=True)}]
        for sc in vs:
            k = int(round(sc["dur"] * M.FPS))
            sc["pcm"] = (sc["pcm"] + gap(1))[: int(k / M.FPS * SR) * 2]
            sc["dur"] = k / M.FPS
        v = M.render(vs, 1080, 1920, result_dir / f"short-{tag}-{n}.mp4", tmp, log=lambda *a: None)
        v_files.append((v, it))
        log(f"   ✓ Short {n}: {sum(s_['dur'] for s_ in vs):.0f}s, {v.stat().st_size / 1e6:.1f} MB")

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
        if path.stat().st_size > 48_000_000:  # Telegram bot giới hạn 50MB → nén bản xem trước
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                        "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout or 600)
            kbps = int(44_000_000 * 8 / dur / 1000) - 96
            small = path.with_name(path.stem + "-preview.mp4")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-vf", "scale=-2:720",
                            "-c:v", "libx264", "-preset", "veryfast", "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k",
                            "-bufsize", f"{kbps * 2}k", "-c:a", "aac", "-b:a", "96k", str(small)], check=True)
            caption += "\n(bản xem trước 720p — bản gốc 1080p ở link Release)"
            path = small
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
