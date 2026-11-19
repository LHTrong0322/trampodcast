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
import music as MU  # noqa: E402
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

# chữ thương hiệu (insight.py ghi đè cho chuỗi Trạm Insight)
BRAND = {"name": "TRẠM PODCAST CRYPTO", "title_tag": "TỔNG HỢP TUẦN",
         "outro_line": "Đăng ký kênh để nhận tổng hợp crypto mỗi tuần",
         "cta_v": "Xem full tổng hợp tuần · @Trong0322", "thumb_tag": "TỔNG HỢP TUẦN {week}",
         "tg_header": "Video tổng hợp tuần {week}", "tag_prefix": "weekly"}

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


def silences(pcm: bytes, noise="-38dB", min_d=0.25) -> list[tuple[float, float]]:
    """Tìm các khoảng lặng (để biết chỗ chuyển giữa các tin trong 1 lần đọc)."""
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        pcm_to_wav(pcm, Path(f.name))
        r = subprocess.run(["ffmpeg", "-i", f.name, "-af", f"silencedetect=noise={noise}:d={min_d}",
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
    raw = gem.text(cfg["models"]["text"], system, prompt + "\nKhông dùng dấu gạch ngang dài (— –) ở bất kỳ đâu.", json_mode=True)
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M)
    data = json.loads(raw)
    if isinstance(data, list):  # một số model bọc kết quả trong [ ... ]
        dicts = [x for x in data if isinstance(x, dict)]
        data = dicts[0] if len(dicts) == 1 else ({"items": data} if not dicts else dicts[0])
    return P.nodash(data)


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
    "key_stat": "con số nổi bật nhất, viết KIỂU TIẾNG ANH rất ngắn (vd '$1.2B', '$400M', '+18%', '10M HYPE'), để trống nếu không có",
    "key_label": "giải thích con số, tối đa 6 từ",
    "visual_query": "2-4 từ TIẾNG ANH mô tả ảnh minh hoạ chính để tìm ảnh stock (vd 'US Capitol building', 'stock exchange trading floor', 'hacker laptop dark', 'Federal Reserve building'); không dùng tên coin",
    "visual_queries": ["4 từ khoá TIẾNG ANH khác nhau cho 4 góc hình bám sát nội dung tin, mỗi cái 2-4 từ, đa dạng (bối cảnh, con người, đồ vật, biểu tượng), vd cho tin hack sàn: 'hacker hoodie laptop', 'server room red light', 'padlock broken', 'worried trader screen'"],
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
            "visual_queries": [q for q in (it.get("visual_queries") or []) if isinstance(q, str)][:5],
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
# định dạng tiền/số kiểu tiếng Anh cho CHỮ HIỆN TRÊN VIDEO ($6B, $1.2B, $400M, $63,000)
# ---------------------------------------------------------------------------
_UNITS = [("nghìn tỷ", "T"), ("ngàn tỷ", "T"), ("tỷ", "B"), ("triệu", "M"), ("nghìn", "K"), ("ngàn", "K")]
_UNIT_RE = re.compile(r"(?:(\$)\s?)?(\d+(?:[.,]\d+)*)\s*(nghìn tỷ|ngàn tỷ|tỷ|triệu|nghìn|ngàn)"
                      r"(\s*(?:đô la Mỹ|đô la|đô|USD|usd|USDT|\$))?", re.I)
_DOLLAR_RE = re.compile(r"(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(?:đô la Mỹ|đô la|đô|USD)\b", re.I)


def _num(raw: str) -> str:
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", raw):          # 63.000 (kiểu VN) → 63,000
        return f"{int(raw.replace('.', '')):,}"
    if re.fullmatch(r"\d{1,3}(,\d{3})+", raw):           # 63,000 giữ nguyên
        return raw
    return raw.replace(",", ".")                          # 1,2 → 1.2


def en_money(text: str) -> str:
    if not text:
        return text
    text = P.nodash(text)

    def unit(m):
        dollar = bool(m.group(1)) or bool(m.group(4))
        u = dict(_UNITS)[m.group(3).lower()]
        return f"{'$' if dollar else ''}{_num(m.group(2))}{u}"
    text = _UNIT_RE.sub(unit, text)
    text = _DOLLAR_RE.sub(lambda m: f"${_num(m.group(1))}", text)
    text = re.sub(r"(\d)\s*phần trăm", r"\1%", text)
    return re.sub(r"\$\$", "$", text)


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


_api_cache: dict = {}


def _cached(key, fn):
    if key not in _api_cache:
        try:
            _api_cache[key] = fn()
        except Exception as ex:
            log(f"      ! {key[0]} lỗi: {ex}")
            _api_cache[key] = []
    return _api_cache[key]


def _first_new(cands, min_side=700):
    """cands: [(url, credit)] → ảnh đầu tiên chưa dùng trong video."""
    for url, cred in cands:
        if not url or url in _used:
            continue
        _used.add(url)
        im = _download(url)
        if im and min(im.size) >= min_side:
            return im, cred
    return None


def search_pexels(query: str, orientation: str):
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return None
    cands = _cached(("Pexels", query, orientation), lambda: [
        (ph["src"].get("large2x") or ph["src"]["original"], f"{ph.get('photographer', '')} / Pexels")
        for ph in _get("https://api.pexels.com/v1/search", headers={"Authorization": key},
                       params={"query": query, "orientation": orientation, "per_page": 12}).json().get("photos", [])])
    return _first_new(cands)


def search_pixabay(query: str, orientation: str):
    key = os.getenv("PIXABAY_API_KEY")
    if not key:
        return None
    cands = _cached(("Pixabay", query, orientation), lambda: [
        (h.get("largeImageURL") or h.get("webformatURL"), f"{h.get('user', '')} / Pixabay")
        for h in _get("https://pixabay.com/api/", params={
            "key": key, "q": query[:100], "image_type": "photo", "safesearch": "true", "per_page": 15,
            "orientation": "horizontal" if orientation == "landscape" else "vertical"}).json().get("hits", [])])
    return _first_new(cands)


def search_wikimedia(query: str, orientation: str = "landscape"):
    def fetch():
        r = _get("https://commons.wikimedia.org/w/api.php", params={
            "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
            "gsrsearch": f"filetype:bitmap {query}", "gsrlimit": 12, "prop": "imageinfo",
            "iiprop": "url|size|extmetadata", "iiurlwidth": 1920})
        out = []
        for pg in sorted(r.json().get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99)):
            ii = (pg.get("imageinfo") or [{}])[0]
            wide = ii.get("width", 0) >= ii.get("height", 1) * 0.9
            if ii.get("width", 0) < 1000 or (wide != (orientation == "landscape")):
                continue
            meta = ii.get("extmetadata", {})
            lic = meta.get("LicenseShortName", {}).get("value", "")
            if not re.search(r"CC|Public domain|PD", lic, re.I):
                continue
            artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))[:40]
            out.append((ii.get("thumburl") or ii.get("url"), f"{artist} / Wikimedia Commons ({lic})"))
        return out
    return _first_new(_cached(("Wikimedia", query, orientation), fetch))


def search_openverse(query: str, orientation: str):
    cands = _cached(("Openverse", query, orientation), lambda: [
        (h.get("url"), f"{(h.get('creator') or '')[:30]} / {h.get('source', 'Openverse')} "
                       f"(CC {str(h.get('license', '')).upper()} {h.get('license_version', '')})")
        for h in _get("https://api.openverse.org/v1/images/", params={
            "q": query, "license_type": "commercial,modification", "size": "large", "page_size": 12,
            "aspect_ratio": "wide" if orientation == "landscape" else "tall", "mature": "false"}).json().get("results", [])])
    return _first_new(cands)


CATEGORY_QUERIES = {"Pháp lý": ["government building", "judge gavel court", "law books"],
                    "Vĩ mô & Chính trị": ["stock market screen", "federal reserve", "world economy"],
                    "Dòng tiền & ETF": ["wall street", "money finance", "investment growth"],
                    "Dự án": ["technology network", "blockchain digital", "startup team office"],
                    "Bảo mật": ["cyber security hacker", "padlock digital", "server room"],
                    "Thị trường": ["trading chart screen", "stock exchange", "trader monitors"]}
TICKER_QUERIES = {"BTC": "bitcoin coin", "ETH": "ethereum", "SOL": "solana", "XRP": "ripple xrp",
                  "BNB": "binance", "DOGE": "dogecoin"}


def find_images(item: dict, orientation: str, n: int) -> list:
    """Tìm n ảnh KHÁC NHAU bám nội dung tin: lần lượt theo các từ khoá AI gợi ý, rồi từ khoá chung."""
    queries = [q for q in (item.get("visual_queries") or []) if q]
    queries += [q for q in [item.get("visual_query"), item.get("visual_fallback")] if q]
    queries += [TICKER_QUERIES[str(t).lstrip("$").upper()] for t in (item.get("tickers") or [])
                if str(t).lstrip("$").upper() in TICKER_QUERIES]
    queries += CATEGORY_QUERIES.get(item.get("category"), ["cryptocurrency"])
    queries = list(dict.fromkeys(queries))
    out, rounds = [], 0
    while len(out) < n and rounds < 3:
        got = False
        for q in queries:
            if len(out) >= n:
                break
            res = (search_pexels(q, orientation) or search_pixabay(q, orientation)
                   or search_wikimedia(q, orientation) or search_openverse(q, orientation))
            if res:
                out.append(res)
                got = True
        rounds += 1
        if not got:
            break
    return out


_coin_logo: dict = {}
_coin_info: dict = {}


def coin_info(ticker: str) -> dict | None:
    t = str(ticker).lstrip("$").upper()
    if t not in _coin_info:
        _coin_info[t] = None
        try:
            r = _get("https://api.coingecko.com/api/v3/search", params={"query": t})
            for c in r.json().get("coins", [])[:8]:
                if c.get("symbol", "").upper() == t and c.get("market_cap_rank"):
                    _coin_info[t] = c
                    break
        except Exception:
            pass
    return _coin_info[t]


def coin_series(ticker: str) -> list | None:
    """Giá 7 ngày của coin (để vẽ biểu đồ nhỏ trong cảnh tin)."""
    info = coin_info(ticker)
    if not info:
        return None
    try:
        time.sleep(1.2)  # nhẹ tay với giới hạn của CoinGecko
        r = _get(f"https://api.coingecko.com/api/v3/coins/{info['id']}/market_chart",
                 params={"vs_currency": "usd", "days": 7})
        pts = [p[1] for p in r.json().get("prices", [])]
        return pts[::3] if len(pts) > 10 else None
    except Exception:
        return None


def coin_logo(ticker: str, size: int) -> Image.Image | None:
    t = str(ticker).lstrip("$").upper()
    if t not in _coin_logo:
        info = coin_info(t)
        _coin_logo[t] = _download(info["large"]) if info and info.get("large") else None
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
    """1 ảnh: phóng to/thu nhỏ chậm + trôi ngang (kiểu phim tài liệu), phủ tối để chữ dễ đọc."""

    def __init__(self, im: Image.Image, region: tuple, vertical: bool, seed: int, shade: float = 1.0):
        x0, y0, x1, y1 = region
        rw, rh = x1 - x0, y1 - y0
        big = cover_fit(im, int(rw * 1.2), int(rh * 1.2)).convert("RGB")
        mask = Image.new("L", big.size, 0)
        md = ImageDraw.Draw(mask)
        if vertical:
            for y in range(big.height):
                md.line([(0, y), (big.width, y)], fill=int(min(255, (70 + 185 * (y / big.height) ** 1.1) * shade)))
        else:
            for x in range(big.width):
                md.line([(x, 0), (x, big.height)], fill=int(min(255, (225 - 135 * (x / big.width) ** 0.9) * shade)))
        big.paste(Image.new("RGB", big.size, (14, 11, 8)), (0, 0), mask)
        self.big, self.region, self.rw, self.rh = big, region, rw, rh
        rnd = random.Random(seed)
        self.zoom_in = rnd.random() < 0.5
        self.c0 = (rnd.uniform(0.38, 0.62), rnd.uniform(0.4, 0.6))
        self.c1 = (rnd.uniform(0.38, 0.62), rnd.uniform(0.4, 0.6))

    def frame(self, p: float) -> Image.Image:
        p = M.clamp(p)
        f = 1.0 - 0.16 * (p if self.zoom_in else 1 - p)          # tỉ lệ vùng cắt
        bw, bh = self.big.size
        cw, ch = bw * f, bh * f
        cx = (self.c0[0] + (self.c1[0] - self.c0[0]) * p) * bw
        cy = (self.c0[1] + (self.c1[1] - self.c0[1]) * p) * bh
        x0 = min(max(0, cx - cw / 2), bw - cw)
        y0 = min(max(0, cy - ch / 2), bh - ch)
        return self.big.resize((self.rw, self.rh), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


class Slideshow:
    """Nhiều ảnh nối nhau liên tục, mỗi ảnh vài giây, chuyển bằng hoà mờ (crossfade)."""

    def __init__(self, images: list, region: tuple, vertical: bool, dur: float, every: float, seed: int,
                 shade: float = 1.0):
        self.region, self.dur = region, dur
        n = max(1, min(len(images), int(math.ceil(dur / every))))
        self.kbs = [KenBurns(im, region, vertical, seed + i, shade) for i, (im, _) in enumerate(images[:n])]
        self.slot = dur / max(1, len(self.kbs))
        self.fade = min(0.7, self.slot * 0.25)

    def draw(self, canvas: Image.Image, t: float):
        if not self.kbs:
            return
        i = min(int(t / self.slot), len(self.kbs) - 1)
        # mỗi ảnh chuyển động trong (slot + fade) giây để lúc hoà mờ vẫn đang trôi
        span = self.slot + self.fade
        cur = self.kbs[i].frame((t - i * self.slot) / span)
        nxt_start = (i + 1) * self.slot - self.fade
        if i + 1 < len(self.kbs) and t >= nxt_start:
            a = M.ease_in_out((t - nxt_start) / self.fade)
            nxt = self.kbs[i + 1].frame((t - nxt_start) / span)
            cur = Image.blend(cur, nxt, a)
        canvas.paste(cur, self.region[:2])


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
        for dx, dy in ((4, 5), (3, 3), (5, 6)):
            d.text((dx, dy), text, font=fnt, fill=(0, 0, 0, 170))
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
    d.text((60 + s + 22, 14 + (8 if vertical else 2)), BRAND["name"], font=f1, fill=CREAM)
    d.text((60 + s + 22, 14 + (60 if vertical else 46)), sub, font=f2, fill=MUTED)
    return im


def watermark_layer(vertical: bool) -> tuple:
    """Watermark @Trong0322 nhỏ, mờ, cố định góc trên bên phải mọi khung hình."""
    f = font("Bold", 26 if not vertical else 30)
    w = int(_measure.textlength("@Trong0322", font=f)) + 12
    im = Image.new("RGBA", (w, f.size + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((3, 4), "@Trong0322", font=f, fill=(0, 0, 0, 120))
    d.text((1, 2), "@Trong0322", font=f, fill=(255, 248, 232, 175))
    W = 1080 if vertical else 1920
    return im, (W - w - (44 if not vertical else 40), 118 if not vertical else 140)


def draw_progress(d, W, H, frac, vertical=False):
    y = H - (10 if not vertical else 14)
    d.rectangle([0, y, W, H], fill=(48, 39, 30))
    d.rectangle([0, y, int(W * M.clamp(frac)), H], fill=CHEESE)


def credit(d, W, H, text, vertical=False):
    return  # nguồn ảnh ghi trong mô tả YouTube, không hiện trên video
    if text:
        f = font("Regular", 20 if not vertical else 22)
        d.text((W - 40 - d.textlength(text[:80], font=f), H - (48 if not vertical else 70)), text[:80],
               font=f, fill=(200, 190, 175))


def chunk_bounds(item: dict, chunks: list, speech: float) -> list:
    """Mốc thời gian từng câu phụ đề: ước lượng theo độ dài chữ rồi 'hít' vào chỗ ngừng thật của giọng."""
    lens = [max(1, len(" ".join(c))) for c in chunks]
    tot = sum(lens)
    sil = silences(item["pcm"], "-35dB", 0.12) if item.get("pcm") else []
    mids = [(a + b) / 2 for a, b in sil if b < speech]
    cuts, acc = [], 0
    for L in lens[:-1]:
        acc += L
        guess = speech * acc / tot
        near = [m for m in mids if abs(m - guess) < max(0.9, speech * 0.06) and (not cuts or m > cuts[-1] + 0.6)]
        cuts.append(min(near, key=lambda m: abs(m - guess)) if near else guess)
    edges = [0.0] + cuts + [speech]
    return [(edges[i], edges[i + 1]) for i in range(len(chunks))]


def balance_lines(lines: list[str]) -> list[str]:
    if len(lines) >= 2 and len(lines[-1].split()) == 1 and len(lines[-2].split()) > 2:
        a = lines[-2].split()
        lines[-1] = a.pop() + " " + lines[-1]
        lines[-2] = " ".join(a)
    return lines


# ---------------------------------------------------------------------------
# 4. CẢNH (scene) — mỗi cảnh trả về hàm vẽ theo thời gian
# ---------------------------------------------------------------------------
def scene_title(title, week, host, dur, images=None):
    W, H = 1920, 1080
    show = Slideshow(images or [], (0, 0, W, H), False, dur, 2.6, 99, shade=1.15) if images else None
    L = [Layer(logo(240), 120, 170, "pop", 0.1, 0.7),
         Layer(text_img(BRAND["title_tag"], font("ExtraBold", 46), CHEESE), 120, 470, "fade_up", 0.35),
         Layer(text_img(week, font("SemiBold", 40), MUTED), 120, 530, "fade_up", 0.45)]
    tf = fit_font(title, "ExtraBold", 92, 60, 1680, 3)
    for i, ln in enumerate(wrap(_measure, title, tf, 1680, 3)):
        L.append(Layer(text_img(ln, tf, CREAM), 116, 620 + i * int(tf.size * 1.15), "fade_up", 0.6 + 0.12 * i))
    if host:
        L.append(Layer(text_img(f"MC {host}", font("SemiBold", 32), MUTED), 1560, 990, "fade_up", 1.1))

    def draw(c, t, ctx):
        if show:
            show.draw(c, t)
        for ly in L:
            ly.draw(c, t)
        d = ImageDraw.Draw(c)
        M.eq_bars(d, 1740, 40, ctx["lvl"], ctx["t_glob"], CHEESE, h=60, w=14, gapx=9)
        draw_progress(d, W, H, ctx["t_glob"] / ctx["total"])
    return draw


def scene_hook(hook, stat, label, dur, images):
    """3 giây mở màn: con số sốc nhất tuần chạy số + câu hook, ảnh nền đổi nhanh."""
    W, H = 1920, 1080
    show = Slideshow(images or [], (0, 0, W, H), False, dur, 1.4, 7, shade=1.25) if images else None
    stat = (stat or "").strip()
    sf = fit_font(stat, "ExtraBold", 230, 100, 1600, 1) if stat else None
    L = []
    if label:
        ti = text_img(label.upper(), font("Bold", 40), CREAM)
        L.append(Layer(ti, (W - ti.size[0]) // 2, 585, "fade_up", 0.35))
    hf = fit_font(hook, "ExtraBold", 64, 44, 1600, 2)
    y = 680 if stat else 420
    for i, ln in enumerate(wrap(_measure, hook, hf, 1600, 2)):
        ti = text_img(ln, hf, CHEESE if not stat else (255, 255, 255))
        L.append(Layer(ti, (W - ti.size[0]) // 2, y, "pop", 0.15 + 0.12 * i, 0.5))
        y += int(hf.size * 1.2)

    def draw(c, t, ctx):
        if show:
            show.draw(c, t)
        d = ImageDraw.Draw(c)
        if stat:
            s_ = M.countup_text(stat, t / 0.9)
            sw = d.textlength(s_, font=sf)
            sc = 1 + 0.04 * math.sin(min(1, t / 0.9) * math.pi)
            d.text(((W - sw * sc) / 2 + 4, 270 + 6), s_, font=sf, fill=(0, 0, 0))
            d.text(((W - sw) / 2, 270), s_, font=sf, fill=CHEESE)
        for ly in L:
            ly.draw(c, t)
        M.eq_bars(d, (W - 100) // 2, 210, ctx["lvl"], ctx["t_glob"], CHEESE, h=60, w=14, gapx=9)
    return draw


def make_thumbnail(text: str, stat: str, week: str, bg) -> Image.Image:
    """Ảnh bìa YouTube 1280×720: chữ to 3-5 từ + con số + logo + @Trong0322."""
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), BG)
    if bg is not None:
        img.paste(KenBurns(bg, (0, 0, W, H), False, 1, shade=1.05).frame(0.5), (0, 0))
    d = ImageDraw.Draw(img)
    text = (text or "").upper().strip()
    tf = fit_font(text, "ExtraBold", 118, 64, 820, 3)
    lines = wrap(_measure, text, tf, 820, 3)
    y = 150 if not stat else 110
    for k, ln in enumerate(lines):
        col = CHEESE if k % 2 == 0 else (255, 255, 255)
        for dx, dy in ((6, 7), (4, 4)):
            d.text((60 + dx, y + dy), ln, font=tf, fill=(0, 0, 0))
        d.text((60, y), ln, font=tf, fill=col)
        y += int(tf.size * 1.05)
    if stat:
        sf = fit_font(stat, "ExtraBold", 120, 70, 520, 1)
        sw = int(d.textlength(stat, font=sf))
        bx0, by0 = 60, min(y + 24, H - sf.size - 90)
        d.rounded_rectangle([bx0, by0, bx0 + sw + 60, by0 + sf.size + 40], radius=26, fill=CHEESE)
        d.text((bx0 + 30, by0 + 12), stat, font=sf, fill=(20, 16, 12))
    img.paste(logo(110), (W - 150, 36), logo(110))
    tag = BRAND["thumb_tag"].format(week=week)
    tf2 = font("ExtraBold", 30)
    tw = d.textlength(tag, font=tf2)
    d.rounded_rectangle([60, 40, 60 + tw + 40, 92], radius=26, fill=(20, 16, 12))
    d.text((80, 46), tag, font=tf2, fill=CHEESE)
    wf = font("Bold", 30)
    d.text((W - 40 - d.textlength("@Trong0322", font=wf), H - 60), "@Trong0322", font=wf, fill=CREAM)
    return img


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
            pct = f"{'+' if ch >= 0 else ''}{ch * e:.1f}%"
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


def story_layers_h(item, idx, total, week_label):
    W, H = 1920, 1080
    L = [Layer(brand_layer(W, week_label), 0, 40, "fade_up", 0, 0.4, 20),
         Layer(text_img(f"{idx:02d}/{total:02d}", font("ExtraBold", 40), CHEESE), 1760, 60, "fade_up", 0.1)]
    fc = font("Bold", 28)
    x = 120
    chips = [chip_img(item["category"], CAT_COLORS.get(item["category"], (176, 115, 14)), fc)]
    if item.get("is_update"):
        chips.append(chip_img("CẬP NHẬT", (11, 110, 79), fc))
    chips.append(text_img(item.get("date_text") or date_label(datetime.fromisoformat(item["date"])),
                          font("SemiBold", 30), MUTED))
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
        lf = font("SemiBold", 30)
        for i, ln in enumerate(balance_lines(wrap(_measure, item.get("key_label", ""), lf, 470, 2))):
            ti = text_img(ln, lf, MUTED, shadow=False)
            L.append(Layer(ti, 1270 + (540 - ti.size[0]) // 2, 520 + i * 42, "fade_up", 1.1))
    return L, stat, stat_box


def scene_story_h(item, idx, total, week_label, dur, images, every):
    W, H = 1920, 1080
    L, stat, stat_box = story_layers_h(item, idx, total, week_label)
    show = Slideshow(images, (0, 0, W, H), False, dur, every, hash(item["headline"]) & 0xffff)
    chunks = M.split_words_chunks(item.get("sub_text") or item["narration"], 78) or [[]]
    speech = max(0.5, item["speech_dur"])
    bounds = chunk_bounds(item, chunks, speech)
    sf_big = fit_font(stat, "ExtraBold", 140, 64, 480, 1) if stat else None
    cc = item.get("coin_chart")
    cbox = (1270, 662, 540, 176) if stat else (1270, 300, 540, 300)
    if cc:
        L.append(Layer(panel_img(cbox[2], cbox[3], outline=(80, 64, 40, 255)), cbox[0], cbox[1], "slide_left", 0.9, 0.6))

    def draw(c, t, ctx):
        show.draw(c, t)
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
        if cc and t > 1.2:
            sym, ser = cc
            e = M.ease_out_cubic((t - 1.2) / 1.6)
            x0, y0, w, h = cbox
            ch_pct = (ser[-1] / ser[0] - 1) * 100
            col = (34, 197, 94) if ch_pct >= 0 else (239, 68, 68)
            d.text((x0 + 26, y0 + 18), f"{sym} · 7 ngày", font=font("Bold", 28), fill=CREAM)
            pct = f"{'+' if ch_pct >= 0 else ''}{ch_pct * e:.1f}%"
            pf = font("ExtraBold", 32)
            d.text((x0 + w - 26 - d.textlength(pct, font=pf), y0 + 16), pct, font=pf, fill=col)
            gx0, gy0, gx1, gy1 = x0 + 26, y0 + 66, x0 + w - 26, y0 + h - 22
            lo, hi = min(ser), max(ser)
            rng = (hi - lo) or 1
            k = max(2, int(len(ser) * e))
            pts = [(gx0 + (gx1 - gx0) * j / (len(ser) - 1), gy1 - (gy1 - gy0) * (v - lo) / rng)
                   for j, v in enumerate(ser[:k])]
            d.line(pts, fill=col, width=4, joint="curve")
            px, py = pts[-1]
            d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col)
        for (a, b), ch in zip(bounds, chunks):
            if a <= t < b + (dur - speech if (a, b) == bounds[-1] else 0):
                M.karaoke(c, d, W, H, ch, (t - a) / max(0.1, b - a), font("SemiBold", 46), 1400, H - 64)
                break
        M.eq_bars(d, 1610, 62, ctx["lvl"], ctx["t_glob"], CHEESE, h=40, w=9, gapx=6)
        draw_progress(d, W, H, ctx["t_glob"] / ctx["total"])
    return draw


def scene_story_v(item, dur, week_label, images, every):
    W, H = 1080, 1920
    L = [Layer(brand_layer(W, week_label, True), 0, 40, "fade_up", 0, 0.4, 20)]
    show = Slideshow(images, (0, 230, W, 1050), True, dur, every, hash(item["headline"]) & 0xffff)
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
    cta = text_img(BRAND["cta_v"], font("Bold", 32), MUTED, shadow=False)
    L.append(Layer(cta, (W - cta.size[0]) // 2, H - 110, "fade_up", 1.0))
    chunks = M.split_words_chunks(item.get("sub_text") or item["narration"], 54) or [[]]
    speech = max(0.5, item["speech_dur"])
    bounds = chunk_bounds(item, chunks, speech)

    def draw(c, t, ctx):
        show.draw(c, t)
        for ly in L:
            ly.draw(c, t)
        d = ImageDraw.Draw(c)
        if stat and t > 1.0:
            s = M.countup_text(stat, (t - 1.0) / 1.0)
            sw = d.textlength(s, font=sf)
            d.text(((W - sw) / 2, sy + 30 + (150 - sf.size) / 2), s, font=sf, fill=CHEESE)
        for (a, b), ch in zip(bounds, chunks):
            if a <= t < b + (dur - speech if (a, b) == bounds[-1] else 0):
                M.karaoke(c, d, W, H, ch, (t - a) / max(0.1, b - a), font("ExtraBold", 54), W - 150, H - 170,
                          max_lines=3)
                break
        M.eq_bars(d, W - 150, 70, ctx["lvl"], ctx["t_glob"], CHEESE, h=56, w=12, gapx=8)
        draw_progress(d, W, H, ctx["t_glob"] / ctx["total"], vertical=True)
    return draw


def scene_outro(vertical=False):
    W, H = (1080, 1920) if vertical else (1920, 1080)
    s = 300 if vertical else 240
    L = [Layer(logo(s), (W - s) // 2, int(H * 0.2), "pop", 0.05, 0.7)]
    y = int(H * 0.2) + s + 50
    for k, (text, f, c) in enumerate([
            (BRAND["name"], font("ExtraBold", 64 if vertical else 58), CHEESE),
            (BRAND["outro_line"], font("SemiBold", 40 if vertical else 36), CREAM),
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
6. "hook": 1 câu MỞ MÀN cực sốc, đọc trong ~3 giây (≤ 16 từ), nêu con số/sự kiện gây chú ý nhất
   tuần, KHÔNG chào hỏi (vd "Sáu tỷ đô bị thanh lý chỉ trong bảy ngày, chuyện gì đang xảy ra?").
   "hook_stat": con số đó viết kiểu tiếng Anh để hiện chữ to (vd "$6B", "$400M", "-15%"); CHỈ điền khi là số liệu
   thật, có ý nghĩa rõ ràng trong tin; không có thì để trống "". "hook_label": giải thích ≤ 6 từ.
7. Ảnh bìa YouTube: "thumb_text" 3-5 từ IN HOA gây tò mò; "thumb_stat" con số ngắn (có thể trống).
8. Với MỖI tin trong "shorts": "short_hooks" là 1 câu mở đầu giật tít đọc trong ~2-3 giây
   (≤ 12 từ), khiến người lướt phải dừng lại xem.
Lời "intro" bắt đầu ngay bằng lời chào (vì đã có hook phía trước).

Trả về DUY NHẤT JSON:
{{"title": "...", "description": "...", "hook": "...", "hook_stat": "...", "hook_label": "...",
  "thumb_text": "...", "thumb_stat": "...", "intro": "...", "outro": "...",
  "order": [id, ...], "shorts": [id, ...], "short_hooks": {{"id": "câu hook", ...}}}}"""


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
            if cfg["podcast"].get("tts_provider") == "vieneu":   # đọc lại bằng giọng VieNeu
                it["pcm"] = P.clean_chunk(P.speak_chunk(None, cfg, [it["narration"]], 0))
            else:
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
    hook = P.sanitize_script(plan.get("hook", ""))
    sh_raw = plan.get("short_hooks") or {}
    sh_lines = {i: P.sanitize_script(str(sh_raw.get(str(i)) or sh_raw.get(i) or "")) for i in shorts}
    parts = ([hook] if hook else []) + [intro, outro] + [sh_lines[i] for i in shorts if sh_lines[i]]
    log(f"   ♪ Đọc hook + lời mở + kết + hook video dọc ({sum(map(len, parts))} ký tự, 1 lượt)")
    io_pcm = tts_once(gem, cfg, "\n\n".join(parts))
    spans = split_points(io_pcm, parts)
    pcs = [slice_pcm(io_pcm, a, b) for a, b in spans]
    hook_pcm = pcs.pop(0) if hook else b""
    intro_pcm, outro_pcm = pcs.pop(0), pcs.pop(0)
    sh_pcm = {}
    for i in shorts:
        if sh_lines[i] and pcs:
            sh_pcm[i] = pcs.pop(0)

    tmp = Path(tempfile.mkdtemp())
    result_dir = out / "video" / "weekly"
    result_dir.mkdir(parents=True, exist_ok=True)
    tag = now.strftime("%Y%m%d")
    title = en_money(plan.get("title") or f"Tổng hợp crypto tuần {week}")
    wl = f"Tổng hợp tuần {week}"
    T = 0.6  # nghỉ giữa các tin

    # chữ hiện trên video: tiền/số kiểu tiếng Anh ($6B, $1.2B...). Giọng đọc giữ tiếng Việt.
    for it in pool:
        for k in ("headline", "key_stat", "key_label", "hook"):
            it[k] = en_money(it.get(k, ""))
        it["sub_text"] = en_money(it["narration"])
    every = float(vcfg.get("image_seconds", 4.0))  # đổi ảnh mỗi ~4 giây
    log("   🖼  Tìm ảnh minh hoạ cho từng tin")
    credits = []
    for i in set(order) | set(shorts):
        it = pool[i]
        it["speech_dur"] = len(it["pcm"]) / SR / 2
        n = max(2, min(9, int(math.ceil((it["speech_dur"] + 0.6) / every))))
        it["imgs_h"] = find_images(it, "landscape", n) if i in order else []
        it["imgs_v"] = find_images(it, "portrait", n) if i in shorts else []
        credits += [c for _, c in it["imgs_h"] + it["imgs_v"]]
        log(f"      [{i}] {len(it['imgs_h'])} ảnh ngang · {len(it['imgs_v'])} ảnh dọc · {it.get('visual_query', '')!r}")
    for i in order:
        pool[i]["coin_chart"] = None
        for tk in (pool[i].get("tickers") or [])[:3]:
            series = coin_series(tk)
            if series:
                pool[i]["coin_chart"] = (str(tk).lstrip("$").upper(), series)
                break
    intro_imgs = find_images({"visual_queries": ["cryptocurrency bitcoin", "stock market trading screen",
                                                 "city skyline night finance"], "category": "Thị trường"},
                             "landscape", 4)
    credits += [c for _, c in intro_imgs]

    # ---- video ngang 16:9 ----
    scenes = []
    if hook_pcm:
        hd = len(hook_pcm) / SR / 2 + 0.35
        scenes.append({"dur": hd, "pcm": hook_pcm + gap(0.35), "wipe": False,
                       "draw": scene_hook(en_money(hook), en_money(plan.get("hook_stat", "")),
                                          en_money(plan.get("hook_label", "")), hd,
                                          intro_imgs)})
    prices = fetch_prices()
    idur = len(intro_pcm) / SR / 2 + T
    if prices:
        scenes.append({"dur": idur * 0.5, "pcm": intro_pcm[: int(len(intro_pcm) * 0.5) // 2 * 2],
                       "draw": scene_title(title, week, pc.get("host_name", ""), idur * 0.5, intro_imgs),
                       "wipe": bool(hook_pcm)})
        rest = intro_pcm[int(len(intro_pcm) * 0.5) // 2 * 2:] + gap(T)
        scenes.append({"dur": len(rest) / SR / 2, "pcm": rest, "draw": scene_chart(prices, wl, len(rest) / SR / 2)})
    else:
        scenes.append({"dur": idur, "pcm": intro_pcm + gap(T),
                       "draw": scene_title(title, week, pc.get("host_name", ""), idur, intro_imgs),
                       "wipe": bool(hook_pcm)})
    marks = [(0, "Mở đầu")]
    tcur = sum(s_["dur"] for s_ in scenes)
    for k, i in enumerate(order, 1):
        it = pool[i]
        a_ = it["pcm"] + gap(T)
        dur = len(a_) / SR / 2
        marks.append((tcur, it["headline"][:70]))
        scenes.append({"dur": dur, "pcm": a_, "draw": scene_story_h(it, k, len(order), wl, dur, it["imgs_h"], every)})
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
    seed = int(now.strftime("%G%V"))
    total_s = sum(s_["dur"] for s_ in scenes)
    music = MU.make_music(total_s + 1, seed) if vcfg.get("music", True) else None
    h_mp4 = M.render(scenes, 1920, 1080, result_dir / f"tong-hop-tuan-{tag}-16x9.mp4", tmp, log=log,
                     watermark=watermark_layer(False), music_pcm=music,
                     music_vol=float(vcfg.get("music_volume", 0.22)))
    log(f"   ✓ Video ngang: {h_mp4.stat().st_size / 1e6:.1f} MB (dựng mất {time.time() - t0:.0f}s)")

    # ---- video dọc 9:16: câu hook + lời tin đọc nhanh hơn ~8%, tối đa ~30 giây ----
    v_files = []
    speed = float(vcfg.get("shorts_speed", 1.08))
    max_s = float(vcfg.get("shorts_max_seconds", 30))
    for n, i in enumerate(shorts, 1):
        it = dict(pool[i])
        hk = sh_pcm.get(i, b"")
        body = P._ffmpeg_pcm(["-f", "s16le", "-ar", str(SR), "-ac", "1"], it["pcm"], f"atempo={speed}")
        sents = [x for x in re.split(r"(?<=[.!?…])\s+", it["narration"]) if x.strip()]
        budget = max_s - 2.6 - len(hk) / SR / 2 - 0.2
        if len(body) / SR / 2 > budget and len(sents) > 1:
            b_ = chunk_bounds({"pcm": body}, [s_.split() for s_ in sents], len(body) / SR / 2)
            keep = max(1, len([1 for a, b in b_ if b <= budget]))
            body = body[: int(b_[keep - 1][1] * SR) * 2]
            sents = sents[:keep]
        text = " ".join(sents)
        it["sub_text"] = en_money((sh_lines[i] + " " + text) if hk else text)
        if hk:
            it["narration"] = sh_lines[i] + " " + text
            it["pcm"] = hk + gap(0.15) + body
        else:
            it["narration"], it["pcm"] = text, body
        it["speech_dur"] = len(it["pcm"]) / SR / 2
        a_ = it["pcm"] + gap(0.4)
        dur = len(a_) / SR / 2
        vs = [{"dur": dur, "pcm": a_, "draw": scene_story_v(it, dur, wl, it["imgs_v"], every * 0.8), "wipe": False},
              {"dur": 2.2, "pcm": gap(2.2), "draw": scene_outro(vertical=True)}]
        for sc in vs:
            k = int(round(sc["dur"] * M.FPS))
            sc["pcm"] = (sc["pcm"] + gap(1))[: int(k / M.FPS * SR) * 2]
            sc["dur"] = k / M.FPS
        tot = sum(s_["dur"] for s_ in vs)
        v = M.render(vs, 1080, 1920, result_dir / f"short-{tag}-{n}.mp4", tmp, log=lambda *a: None,
                     watermark=watermark_layer(True),
                     music_pcm=MU.make_music(tot + 1, seed + n) if vcfg.get("music", True) else None,
                     music_vol=float(vcfg.get("music_volume", 0.22)) * 1.15)
        v_files.append((v, it))
        log(f"   ✓ Short {n}: {tot:.0f}s, {v.stat().st_size / 1e6:.1f} MB")

    # ---- ảnh bìa YouTube ----
    thumb = result_dir / f"thumbnail-{tag}.png"
    bg = (pool[order[0]]["imgs_h"][0][0] if order and pool[order[0]].get("imgs_h") else
          (intro_imgs[0][0] if intro_imgs else None))
    make_thumbnail(en_money(plan.get("thumb_text") or title), en_money(plan.get("thumb_stat", "")), week, bg).save(thumb)
    log(f"   ✓ Ảnh bìa YouTube: {thumb.name}")

    desc = (plan.get("description", "") + "\n\n" + youtube_chapters(marks) +
            "\n\nAgent build by @Trong0322 · Nội dung do AI tổng hợp, không phải lời khuyên đầu tư."
            + ("\n\nNguồn ảnh (giấy phép miễn phí): " + "; ".join(dict.fromkeys(credits)) if credits else ""))
    return {"tag": tag, "title": title, "description": desc, "week": week,
            "h": h_mp4, "shorts": v_files, "thumb": thumb}


# ---------------------------------------------------------------------------
# 4. GỬI ĐI: GitHub Release + Telegram
# ---------------------------------------------------------------------------
def publish_release(res: dict) -> str:
    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo or not os.getenv("GH_TOKEN"):
        return ""
    tag = f"{BRAND['tag_prefix']}-{res['tag']}"
    notes = f"# {res['title']}\n\n{res['description']}"
    files = [str(res["h"])] + [str(v) for v, _ in res["shorts"]] + ([str(res["thumb"])] if res.get("thumb") else [])
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
        "text": (f"🎬 <b>{esc(BRAND['tg_header'].format(week=res['week']))}</b> — bản xem trước\n"
                 f"1 video ngang 16:9 (YouTube) + {len(res['shorts'])} video dọc 9:16 (Reels/Shorts)\n"
                 + (f"📦 Tải file gốc: {esc(release_url)}" if release_url else ""))})
    if res.get("thumb"):
        with open(res["thumb"], "rb") as f:
            requests.post(f"{api}/sendPhoto", timeout=120, data={
                "chat_id": chat, "caption": "🖼 Ảnh bìa (thumbnail) YouTube"},
                files={"photo": (res["thumb"].name, f, "image/png")})
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
    ap.add_argument("--voice-provider", default="", help="gemini | vieneu (ghi đè cho lần chạy này)")
    ap.add_argument("--voice-name", default="", help="tên giọng (vd 'Mai Anh' cho VieNeu)")
    args = ap.parse_args()
    out = Path(args.out)
    cfg = load_cfg()
    if args.voice_provider:
        cfg["podcast"]["tts_provider"] = args.voice_provider
        if args.voice_provider == "vieneu":
            cfg.setdefault("vieneu", {})
            if args.voice_name:
                cfg["vieneu"]["voice"] = args.voice_name
            BRAND["tag_prefix"] = "weekly-vieneu"
            BRAND["tg_header"] = "Video tổng hợp tuần {week} · giọng VieNeu " + cfg["vieneu"].get("voice", "Mai Anh")
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
