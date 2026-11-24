#!/usr/bin/env python3
"""
Trạm Podcast Crypto, tự động gom tin crypto, lọc tin có giá trị cho investor,
dịch sang tiếng Việt, viết kịch bản podcast và đọc thành audio (Gemini TTS).

Chạy:  python scripts/podcast.py --out public
Biến môi trường:
  GEMINI_API_KEY        (bắt buộc)  key lấy ở aistudio.google.com
  TELEGRAM_BOT_TOKEN    (tuỳ chọn)  gửi tập mới vào Telegram
  TELEGRAM_CHAT_ID      (tuỳ chọn)
  SITE_URL              (tuỳ chọn)  vd https://tram-podcast-crypto.pages.dev  (để tạo feed podcast)
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import wave
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

_HERE = Path(__file__).resolve().parent
# Hỗ trợ cả 2 kiểu: mọi file nằm chung 1 chỗ, hoặc podcast.py nằm trong thư mục scripts/
ROOT = _HERE if (_HERE / "sources.yaml").exists() else _HERE.parent
VN_TZ = timezone(timedelta(hours=7))
UA = "Mozilla/5.0 (compatible; TramPodcastCrypto/1.0; +podcast-bot)"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
SAMPLE_RATE = 24000  # Gemini TTS trả PCM 16-bit mono 24kHz


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------------------
# 1. GOM TIN
# ---------------------------------------------------------------------------
def clean_text(s: str, limit: int = 900) -> str:
    s = BeautifulSoup(s or "", "html.parser").get_text(" ")
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]


def item_id(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:16]


def parse_telegram_html(channel: str, page: str) -> list[dict]:
    soup = BeautifulSoup(page, "html.parser")
    out = []
    for msg in soup.select("div.tgme_widget_message[data-post]"):
        post = msg.get("data-post", "")
        body = msg.select_one(".tgme_widget_message_text")
        t = msg.select_one("time[datetime]")
        if not body or not t:
            continue
        # giữ xuống dòng giữa các đoạn
        for br in body.find_all("br"):
            br.replace_with("\n")
        text = re.sub(r"[ \t]+", " ", body.get_text()).strip()
        if len(text) < 25:
            continue
        try:
            ts = datetime.fromisoformat(t["datetime"].replace("Z", "+00:00"))
        except ValueError:
            continue
        links = [a["href"] for a in body.select("a[href]") if a["href"].startswith("http")]
        out.append({
            "id": item_id("tg", post),
            "source": f"Telegram @{channel}",
            "title": text.split("\n")[0][:160],
            "text": text[:1200],
            "url": f"https://t.me/{post}",
            "ext_links": links[:3],
            "time": ts,
        })
    return out


def fetch_telegram(channel: str) -> list[dict]:
    r = requests.get(f"https://t.me/s/{channel}", headers={"User-Agent": UA}, timeout=25)
    r.raise_for_status()
    items = parse_telegram_html(channel, r.text)
    if not items:
        log(f"   ! @{channel}: không đọc được bài nào (kênh private hoặc tắt preview?)")
    return items


def parse_rss(name: str, raw: bytes) -> list[dict]:
    feed = feedparser.parse(raw)
    out = []
    for e in feed.entries[:40]:
        tm = e.get("published_parsed") or e.get("updated_parsed")
        if not tm:
            continue
        ts = datetime(*tm[:6], tzinfo=timezone.utc)
        link = e.get("link", "")
        title = clean_text(e.get("title", ""), 200)
        summary = clean_text(e.get("summary", "") or e.get("description", ""), 700)
        out.append({
            "id": item_id("rss", link or title),
            "source": name,
            "title": title,
            "text": f"{title}. {summary}",
            "url": link,
            "ext_links": [],
            "time": ts,
        })
    return out


def fetch_rss(name: str, url: str) -> list[dict]:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
    r.raise_for_status()
    return parse_rss(name, r.content)


def userbot_fetch_all(channels: list, since: datetime) -> dict:
    """Đọc kênh Telegram bằng tài khoản của bạn (Telethon). Đọc được cả kênh private
    và kênh tắt web preview, miễn là tài khoản đã tham gia kênh.
    Trả về {kênh: [items]} hoặc {} nếu chưa cấu hình."""
    api_id, api_hash, sess = (os.getenv("TG_API_ID"), os.getenv("TG_API_HASH"),
                              os.getenv("TG_SESSION"))
    if not (api_id and api_hash and sess):
        return {}
    try:
        from telethon.sync import TelegramClient
        from telethon.sessions import StringSession
    except ImportError:
        log("   ! Chưa cài telethon, dùng chế độ đọc web preview")
        return {}
    result = {}
    try:
        with TelegramClient(StringSession(sess), int(api_id), api_hash) as client:
            for ch in channels:
                key = str(ch)
                try:
                    entity = client.get_entity(int(ch) if str(ch).lstrip("-").isdigit() else ch)
                    uname = getattr(entity, "username", None)
                    title = getattr(entity, "title", key)
                    items = []
                    for m in client.iter_messages(entity, limit=80):
                        if m.date < since:
                            break
                        text = (m.message or "").strip()
                        if len(text) < 25:
                            continue
                        post = f"{uname}/{m.id}" if uname else f"c/{entity.id}/{m.id}"
                        items.append({
                            "id": item_id("tg", post),
                            "source": f"Telegram @{uname}" if uname else f"Telegram {title}",
                            "title": text.split("\n")[0][:160],
                            "text": text[:1200],
                            "url": f"https://t.me/{post}",
                            "ext_links": [],
                            "time": m.date,
                        })
                    result[key] = items
                except Exception as ex:
                    log(f"   ! userbot không đọc được {key}: {ex}")
    except Exception as ex:
        log(f"   ! Đăng nhập userbot lỗi ({ex}), dùng chế độ đọc web preview")
    return result


def collect(cfg: dict, since: datetime, seen: set[str]) -> list[dict]:
    tg_channels = cfg.get("telegram") or []
    via_userbot = userbot_fetch_all(tg_channels, since)
    if via_userbot:
        log(f"   (Đọc Telegram bằng tài khoản userbot: {len(via_userbot)}/{len(tg_channels)} kênh)")
    jobs = [("tg", str(c), None) for c in tg_channels]
    jobs += [("rss", s["name"], s["url"]) for s in (cfg.get("rss") or [])]
    jobs += [("rss", s["name"], s["url"]) for s in (cfg.get("x_rss") or [])]
    all_items = []
    for kind, name, url in jobs:
        try:
            if kind == "tg" and name in via_userbot:
                items = via_userbot[name]
            elif kind == "tg":
                items = fetch_telegram(name)  # dự phòng: đọc t.me/s/
            else:
                items = fetch_rss(name, url)
        except Exception as ex:  # một nguồn lỗi không làm hỏng cả tập
            log(f"   ✗ {name}: {ex}")
            continue
        fresh = [i for i in items if i["time"] >= since and i["id"] not in seen]
        for i in fresh:
            seen.add(i["id"])  # chống trùng giữa các nguồn trong cùng lần chạy
        log(f"   ✓ {name}: {len(items)} bài, {len(fresh)} bài mới")
        all_items += fresh
    all_items.sort(key=lambda i: i["time"], reverse=True)
    return all_items[:300]  # giới hạn để prompt không quá dài


# ---------------------------------------------------------------------------
# 2. GEMINI
# ---------------------------------------------------------------------------
def _ffmpeg_pcm(args_in: list, data: bytes, filters: str = "") -> bytes:
    cmd = ["ffmpeg", "-loglevel", "error", *args_in, "-i", "pipe:0"]
    if filters:
        cmd += ["-af", filters]
    cmd += ["-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "pipe:1"]
    return subprocess.run(cmd, input=data, capture_output=True, check=True).stdout


def decode_audio(raw: bytes, mime: str) -> bytes:
    """Đưa mọi định dạng audio Gemini trả về (PCM thô, WAV có header, MP3...) về PCM 24kHz.
    Nếu không bóc header WAV, 44 byte header bị đọc như âm thanh → tiếng rè/tách."""
    m = (mime or "").lower()
    is_raw_pcm = (("l16" in m or "pcm" in m) and raw[:4] != b"RIFF")
    if is_raw_pcm:
        mt = re.search(r"rate=(\d+)", m)
        rate = int(mt.group(1)) if mt else SAMPLE_RATE
        if rate == SAMPLE_RATE:
            return raw[: len(raw) // 2 * 2]
        return _ffmpeg_pcm(["-f", "s16le", "-ar", str(rate), "-ac", "1"], raw)
    return _ffmpeg_pcm([], raw)  # để ffmpeg tự nhận định dạng (wav/mp3/ogg...)


def clean_chunk(pcm: bytes) -> bytes:
    """Cắt khoảng lặng/tạp âm nhỏ ở đầu-cuối mỗi đoạn và vuốt nhỏ dần để nối không bị 'tách'."""
    if not pcm:
        return pcm
    f = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,"
         "areverse,"
         "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.08,"
         "afade=t=in:d=0.12,"          # = vuốt nhỏ dần ở CUỐI đoạn (vì đang đảo ngược)
         "areverse,"
         "afade=t=in:d=0.02")
    try:
        out = _ffmpeg_pcm(["-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1"], pcm, f)
        return out if len(out) > len(pcm) * 0.5 else pcm
    except Exception:
        return pcm


_CHIME = None


def transition_sound() -> bytes:
    """Tiếng chuông 'ting-tinh' nhẹ, ấm (tự tổng hợp, không bản quyền) để chuyển tin."""
    global _CHIME
    if _CHIME is None:
        expr = ("0.22*sin(2*PI*1046.5*t)*exp(-5*t)"
                "+0.07*sin(2*PI*2093*t)*exp(-9*t)"
                "+0.18*sin(2*PI*1568*(t-0.14))*exp(-4.5*(t-0.14))*gte(t,0.14)"
                "+0.05*sin(2*PI*3136*(t-0.14))*exp(-9*(t-0.14))*gte(t,0.14)")
        cmd = ["ffmpeg", "-loglevel", "error", "-f", "lavfi",
               "-i", f"aevalsrc='{expr}':s={SAMPLE_RATE}:d=1.1",
               "-af", "afade=t=in:d=0.005,afade=t=out:st=0.8:d=0.3,volume=0.55,"
                      "aecho=0.8:0.5:60:0.25",
               "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "pipe:1"]
        _CHIME = subprocess.run(cmd, capture_output=True, check=True).stdout
    return _CHIME


class Gemini:
    def __init__(self, key: str):
        # Kho key: key truyền vào trước, rồi lần lượt các key dự phòng. Key nào hết lượt hoặc lỗi credit
        # thì tự chuyển sang key kế tiếp. Thêm key mới: tạo secret GEMINI_API_KEY3, 4, 5... (tối đa 9)
        # hoặc GEMINI_API_KEYS (nhiều key cách nhau dấu phẩy).
        pool = [key, os.getenv("INSIGHT_GEMINI_API_KEY", ""), os.getenv("GEMINI_API_KEY", ""),
                os.getenv("GEMINI_API_KEY2", "")]
        pool += [os.getenv(f"GEMINI_API_KEY{i}", "") for i in range(3, 10)]
        pool += os.getenv("GEMINI_API_KEYS", "").split(",")
        self.keys = list(dict.fromkeys(k.strip() for k in pool if k and k.strip())) or [key]
        self.ki = 0
        self.key = self.keys[0]
        self.dead: set[str] = set()  # model đã lỗi trong lần chạy này → bỏ qua luôn

    def _post(self, model: str, body: dict, timeout=240) -> dict:
        url = f"{GEMINI_BASE}/{model}:generateContent"
        for attempt in range(8):
            r = requests.post(url, json=body, timeout=timeout,
                              headers={"x-goog-api-key": self.key})
            if r.status_code == 429 or r.status_code >= 500:
                txt = r.text
                if r.status_code == 429 and "PerDay" in txt:
                    if self._next_key("hết lượt trong ngày"):
                        continue
                    raise RuntimeError(f"{model}: hết lượt miễn phí trong ngày. {txt[:400]}")
                m = re.search(r'"retryDelay":\s*"(\d+)', txt)
                wait = int(m.group(1)) + 5 if m else min(30 * (attempt + 1), 120)
                log(f"   … {model} bận ({r.status_code}), đợi {wait}s rồi thử lại")
                time.sleep(wait)
                continue
            if r.status_code in (400, 401, 403) and re.search(r"credit|billing|quota|API_KEY_INVALID|PERMISSION_DENIED", r.text, re.I) \
                    and self._next_key(f"lỗi {r.status_code}"):
                continue
            if r.status_code != 200:
                raise RuntimeError(f"{model} HTTP {r.status_code}: {r.text[:300]}")
            return r.json()
        raise RuntimeError(f"{model}: hết lượt thử (rate limit)")

    def _next_key(self, why: str) -> bool:
        """Chuyển sang key dự phòng kế tiếp trong kho. Trả False nếu đã dùng hết key."""
        if self.ki + 1 >= len(self.keys):
            return False
        self.ki += 1
        self.key = self.keys[self.ki]
        self.dead.clear()
        log(f"   ↪ Key Gemini số {self.ki} {why}, chuyển sang key dự phòng số {self.ki + 1}/{len(self.keys)}")
        return True

    def _try_models(self, models: list[str], fn):
        last = None
        for m in [m for m in models if m not in self.dead] or models:
            try:
                return fn(m)
            except Exception as ex:
                last = ex
                if "quá ngắn" not in str(ex):
                    self.dead.add(m)
                log(f"   ! model {m} lỗi: {str(ex)[:200]} → thử model kế tiếp")
        raise RuntimeError(f"Tất cả model đều lỗi. Lỗi cuối: {last}")

    def text(self, models, system: str, prompt: str, json_mode=False) -> str:
        def call(m):
            cfg = {"temperature": 1.0}
            if json_mode:
                cfg["responseMimeType"] = "application/json"
            data = self._post(m, {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": cfg,
            })
            parts = data["candidates"][0]["content"]["parts"]
            out = "".join(p.get("text", "") for p in parts if not p.get("thought"))
            if not out.strip():
                raise RuntimeError("model trả về rỗng")
            return out
        return self._try_models(models, call)

    def tts(self, models, voice: str, style: str, text: str) -> bytes:
        if style.strip():
            prompt = (
                "# AUDIO PROFILE\n" + style.strip() + "\n\n"
                "# DIRECTOR'S NOTES\nRead ONLY the transcript below, in Vietnamese, word for word, exactly ONCE. "
                "Never repeat any sentence or phrase. Stop right after the last word. "
                "Do not read these notes or any headings aloud.\n\n"
                "# TRANSCRIPT\n" + text.strip()
            )
        else:
            # Giống hệt cách AI Studio gọi (Get code) → giọng ra y như lúc nghe thử
            prompt = "## Transcript:\n" + text.strip()

        def call(m):
            data = self._post(m, {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
                },
            }, timeout=300)
            pcm = b""
            for p in data["candidates"][0]["content"]["parts"]:
                if "inlineData" in p:
                    pcm += decode_audio(base64.b64decode(p["inlineData"]["data"]),
                                        p["inlineData"].get("mimeType", ""))
            # kiểm tra audio có độ dài hợp lý (≥ ~40% thời lượng ước tính)
            expected_sec = len(text) / 16
            got_sec = len(pcm) / (SAMPLE_RATE * 2)
            if got_sec < max(1.0, expected_sec * 0.4):
                raise RuntimeError(f"audio quá ngắn ({got_sec:.0f}s / ước tính {expected_sec:.0f}s)")
            return pcm
        return self._try_models(models, call)


EDITOR_SYSTEM = """Bạn là tổng biên tập một bản tin crypto tiếng Việt dành cho NHÀ ĐẦU TƯ.
Nhiệm vụ: từ danh sách tin thô (tiếng Anh/Việt, nhiều nguồn, có trùng lặp), chọn ra những tin
có GIÁ TRỊ THỰC cho investor, gộp các tin trùng nhau, rồi tóm tắt bằng tiếng Việt.

ƯU TIÊN (giá trị cao):
- Pháp lý & chính sách: SEC, CFTC, luật stablecoin/market structure, thuế, cấp phép sàn,
  chính sách crypto của Việt Nam và châu Á, các vụ kiện/phán quyết.
- Vĩ mô & chính trị có tác động thị trường: Fed/lãi suất, CPI, thuế quan, động thái chính phủ,
  quỹ dự trữ BTC quốc gia.
- Dòng tiền tổ chức: ETF flows, quỹ/doanh nghiệp mua bán BTC/ETH, treasury companies.
- Dự án: mainnet/upgrade, TGE, airdrop, token unlock lớn, listing/delisting sàn lớn,
  gọi vốn, M&A, buyback, thay đổi tokenomics, partnership THỰC CHẤT.
- Bảo mật: hack, exploit, depeg, sự cố sàn, kèm số tiền thiệt hại.
- On-chain/thị trường: biến động giá lớn KÈM nguyên nhân, liquidation lớn, cá voi.

LOẠI BỎ: quảng cáo, giveaway, shill, kêu gọi mua bán, tin giá thuần tuý không có nguyên nhân,
dự đoán giá vô căn cứ, tin rác, tin lặp lại, meme.

QUY TẮC DỊCH:
- Tiếng Việt tự nhiên, ngắn gọn, chính xác.
- THUẬT NGỮ: ưu tiên dùng đúng thuật ngữ tiếng Anh dân crypto hay dùng, KHÔNG dịch sang tiếng Việt:
  crypto (không viết "tiền điện tử/tiền mã hoá"), stablecoin (không "tiền ổn định"), token, coin,
  altcoin, memecoin, blockchain, DeFi, CeFi, NFT, Web3, ETF, spot, futures, perp, long, short,
  leverage, liquidation, funding rate, open interest, staking, restaking, airdrop, unlock, vesting,
  TGE, listing, delisting, mainnet, testnet, L1, L2, DEX, CEX, TVL, market cap, FDV, whale,
  on-chain, wallet, bridge, exploit, hack, rug pull, RWA, treasury, buyback, burn, fork, upgrade.
  Tên tổ chức/luật giữ nguyên: SEC, CFTC, Fed, FOMC, CPI, GENIUS Act, CLARITY Act...
- Giữ nguyên tên riêng, ticker ($BTC, $ETH...), con số, ngày tháng. Không bịa thêm thông tin
  không có trong tin gốc. Nếu tin chưa xác nhận thì ghi rõ "chưa xác nhận"."""

EDITOR_PROMPT = """CÁC TIN ĐÃ ĐƯA TRONG NHỮNG TẬP TRƯỚC (người nghe đã biết):
{history}

QUY TẮC CHỐNG LẶP (rất quan trọng):
- Tin mới nói về CÙNG sự kiện đã có ở danh sách trên mà KHÔNG có thông tin mới → BỎ HẲN,
  không đưa vào "stories" lẫn "other_news".
- Chỉ đưa lại khi có DIỄN BIẾN MỚI thật sự (số liệu mới, kết quả/phán quyết, động thái mới,
  giá biến động mạnh vì nó...). Khi đó đặt "is_update": true, tiêu đề bắt đầu bằng
  "Cập nhật:" và "detail" viết theo cấu trúc: 1 câu tóm tắt lại diễn biến trước đó (dựa vào
  danh sách tin đã đưa ở trên, để người nghe nhớ lại) + phần diễn biến mới nhất, có số liệu.
- Tin hoàn toàn mới → "is_update": false.

Danh sách tin thô hôm nay (mỗi tin có số [id]):

{items}

Đây là toàn bộ tin trong khoảng 24 giờ qua. Hãy chọn tối đa {max_stories} tin giá trị nhất, sắp theo mức độ quan trọng giảm dần.
Trả về DUY NHẤT JSON đúng cấu trúc:
{{
  "episode_title": "tiêu đề tập, ngắn, hấp dẫn, nêu 1-2 tin nóng nhất, đúng chính tả tiếng Việt",
  "summary": "tóm tắt cả tập trong 2 câu",
  "market_mood": "1 câu nhận định tâm lý thị trường dựa trên các tin",
  "stories": [
    {{
      "headline": "tiêu đề tiếng Việt",
      "category": "Pháp lý | Vĩ mô & Chính trị | Dòng tiền & ETF | Dự án | Bảo mật | Thị trường",
      "importance": 1-5,
      "detail": "2-4 câu tóm tắt nội dung chính, có số liệu",
      "why_it_matters": "1-2 câu: tin này ảnh hưởng gì tới nhà đầu tư",
      "tickers": ["BTC"],
      "is_update": false,
      "source_ids": [số id của các tin gốc liên quan]
    }}
  ],
  "other_news": [
    {{
      "summary": "1 câu tiếng Việt ngắn gọn, đủ ý, có số liệu nếu có",
      "is_update": false,
      "category": "Pháp lý | Vĩ mô & Chính trị | Dòng tiền & ETF | Dự án | Bảo mật | Thị trường",
      "source_id": số id của tin gốc
    }}
  ]
}}
"other_news" = các tin CÒN LẠI không nằm trong "stories" nhưng vẫn là tin thật, có thông tin
(tối đa {max_other} tin, ưu tiên tin quan trọng hơn). Vẫn loại bỏ quảng cáo, giveaway, shill,
kêu gọi mua bán, meme và tin trùng lặp (tin trùng với "stories" thì không đưa vào đây).
Nếu không có tin nào đáng giá, trả về "stories": []."""

SCRIPT_SYSTEM = """Bạn là biên kịch cho podcast tin tức crypto tiếng Việt "{name}".
MC là {host}: cô gái trẻ {region}, dễ thương, nhí nhảnh, hay cười, nói chuyện như kể chuyện
cho bạn thân nghe, nhưng thông tin phải chính xác và rõ ràng. {host} xưng "{host_short}",
gọi người nghe là "cả nhà".

YÊU CẦU KỊCH BẢN (văn NÓI, sẽ được đọc bằng máy):
- Chỉ viết lời thoại thuần. KHÔNG markdown, KHÔNG emoji, KHÔNG gạch đầu dòng, KHÔNG link,
  KHÔNG ký hiệu như *, #, (), [], /.
- Viết số theo cách đọc tự nhiên: "1,2 tỷ đô", "giảm 8 phần trăm", "ngày 7 tháng 11".
  Ticker đọc là tên coin: $BTC → Bitcoin, $ETH → Ethereum, $SOL → Solana.
- THUẬT NGỮ: ưu tiên dùng đúng thuật ngữ tiếng Anh dân crypto hay dùng, KHÔNG dịch sang tiếng Việt:
  crypto (không viết "tiền điện tử/tiền mã hoá"), stablecoin (không "tiền ổn định"), token, coin,
  altcoin, memecoin, blockchain, DeFi, CeFi, NFT, Web3, ETF, spot, futures, perp, long, short,
  leverage, liquidation, funding rate, open interest, staking, restaking, airdrop, unlock, vesting,
  TGE, listing, delisting, mainnet, testnet, L1, L2, DEX, CEX, TVL, market cap, FDV, whale,
  on-chain, wallet, bridge, exploit, hack, rug pull, RWA, treasury, buyback, burn, fork, upgrade.
  Tên tổ chức/luật giữ nguyên: SEC, CFTC, Fed, FOMC, CPI, GENIUS Act, CLARITY Act...
- Cấu trúc: chào mở đầu dễ thương (nhắc buổi {session} ngày {date}) → PHẦN 1 "tin chính":
  {deep} tin đầu tiên trong danh sách, mỗi tin 2-4 câu: chuyện gì xảy ra + vì sao nhà đầu tư cần
  quan tâm, có câu chuyển ý tự nhiên → PHẦN 2 "điểm nhanh": các tin còn lại, MỖI TIN ĐÚNG 1 CÂU
  ngắn, gom chung trong 1-2 đoạn → chốt lại tâm lý thị trường → nhắc "đây không phải lời khuyên
  đầu tư, cả nhà tự nghiên cứu kỹ nha" → chào tạm biệt đáng yêu.
- Tin có "is_update": true là tin đã kể ở tập trước: mở bằng "cập nhật tiếp về..." + 1 câu nhắc
  lại chuyện trước đó cho người nghe nhớ, rồi tập trung kể diễn biến mới nhất.
- Dùng từ ngữ, tiểu từ đúng chất người {region} ({particles}), chêm cảm thán dễ thương
  vừa phải, không lạm dụng.
- Độ dài BẮT BUỘC: cả kịch bản khoảng {chars} ký tự (đọc khoảng {minutes} phút),
  TUYỆT ĐỐI KHÔNG vượt quá {max_chars} ký tự. Đi thẳng vào ý chính. Mỗi tin chính là MỘT đoạn văn, các đoạn cách nhau bằng một dòng trống."""


def history_block(episodes: list[dict], n_eps: int = 3) -> str:
    """Danh sách tin đã đưa trong các tập gần nhất, để AI không nhắc lại tin cũ."""
    lines = []
    for e in (episodes or [])[:n_eps]:
        d = datetime.fromisoformat(e["date"]).strftime("%d/%m")
        for st in e.get("stories", []):
            lines.append(f"- [{d}] {st.get('headline', '')}: {st.get('detail', '')[:220]}")
        for b in e.get("briefs", []):
            lines.append(f"- [{d}] {b.get('summary', '')[:200]}")
    return "\n".join(lines) if lines else "(chưa có tập nào trước đó)"


def build_episode_content(gem: Gemini, cfg: dict, items: list[dict], now_vn: datetime,
                          episodes: list[dict] | None = None):
    pc, models = cfg["podcast"], cfg["models"]
    listing = "\n\n".join(
        f"[{n}] ({it['source']}, {it['time'].astimezone(VN_TZ):%d/%m %H:%M}) {it['text']}"
        for n, it in enumerate(items)
    )
    raw = gem.text(models["text"], EDITOR_SYSTEM,
                   EDITOR_PROMPT.format(items=listing, max_stories=pc.get("max_stories", 12),
                                       max_other=pc.get("max_other_news", 40),
                                       history=history_block(episodes, int(pc.get("history_episodes", 3)))),
                   json_mode=True)
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M)
    ed = json.loads(raw)
    stories = ed.get("stories") or []
    for s in stories:
        ids = [i for i in s.get("source_ids", []) if isinstance(i, int) and 0 <= i < len(items)]
        s["sources"] = [{"name": items[i]["source"], "url": items[i]["url"]} for i in ids][:4]
        s.pop("source_ids", None)
    briefs = []
    for b in ed.get("other_news") or []:
        i = b.get("source_id")
        if not b.get("summary") or not isinstance(i, int) or not 0 <= i < len(items):
            continue
        briefs.append({"summary": b["summary"], "category": b.get("category", "Thị trường"),
                       "is_update": bool(b.get("is_update")),
                       "source": {"name": items[i]["source"], "url": items[i]["url"]}})
    ed["briefs"] = briefs
    if not stories:
        return ed, [], ""

    session = "sáng" if now_vn.hour < 11 else ("trưa" if now_vn.hour < 14 else
                                               ("chiều" if now_vn.hour < 18 else "tối"))
    host = pc.get("host_name", "Bé Mai")
    system = SCRIPT_SYSTEM.format(
        name=pc["name"], host=host, host_short=host, session=session,
        region=pc.get("region", "Hà Nội"),
        particles=pc.get("particles", "nhé, nhỉ, đấy, ạ, ơi, ôi, hihi"),
        date=f"{now_vn.day} tháng {now_vn.month}", minutes=pc.get("target_minutes", 7),
        chars=int(pc.get("target_minutes", 7) * 850), max_chars=int(pc.get("target_minutes", 7) * 1000),
        deep=int(pc.get("deep_stories", 6)))
    brief = json.dumps({k: ed.get(k) for k in ("episode_title", "market_mood")} |
                       {"stories": [{k: s.get(k) for k in
                                     ("headline", "category", "detail", "why_it_matters", "tickers", "is_update")}
                                    for s in stories]}, ensure_ascii=False, indent=1)
    script = gem.text(models["text"], system, "Viết kịch bản từ bản tin sau:\n" + brief)
    script = sanitize_script(script)
    return ed, stories, script


DASHES = "\u2014\u2013\u2015\u2012\u2E3A\u2E3B\uFE58\uFE63\uFF0D"  # các loại gạch ngang dài (em dash, en dash, horizontal bar...)


def nodash(x):
    """KHÔNG BAO GIỜ dùng gạch ngang dài (em dash, en dash...) hay gạch nối đứng giữa câu ( - ): thay bằng dấu phẩy.
    Dùng cho mọi chữ: kịch bản, chữ trên video, phụ đề, SEO, tin Telegram. Áp dụng đệ quy cho list/dict."""
    if isinstance(x, str):
        x = re.sub(rf"\s*[{DASHES}]+\s*(?=\S)", ", ", x)
        x = re.sub(rf"\s*[{DASHES}]+\s*", "", x)
        x = re.sub(r"(?<=\S)\s+-{1,3}\s+(?=\S)", ", ", x)   # "a - b", "a -- b" → "a, b"
        x = re.sub(r",\s*,", ",", x).replace(" ,", ",")
        return re.sub(r"([.!?:;]),", r"\1", x)
    if isinstance(x, list):
        return [nodash(i) for i in x]
    if isinstance(x, tuple):
        return tuple(nodash(i) for i in x)
    if isinstance(x, dict):
        return {k: nodash(v) for k, v in x.items()}
    return x


# LỚP CHẶN CUỐI cho Telegram: MỌI tin nhắn / chú thích gửi qua api.telegram.org (từ bất kỳ file nào đã import podcast)
# đều đi qua nodash, nên không thể lọt gạch ngang dài vào Telegram dù code ở đâu quên lọc.
_raw_post = requests.post


def _tg_safe_post(url, *a, **kw):
    if "api.telegram.org" in str(url) and isinstance(kw.get("data"), dict):
        kw["data"] = {k: (nodash(v) if k in ("text", "caption") and isinstance(v, str) else v) for k, v in kw["data"].items()}
    return _raw_post(url, *a, **kw)


if getattr(requests.post, "__name__", "") != "_tg_safe_post":
    requests.post = _tg_safe_post


def sanitize_script(s: str) -> str:
    s = nodash(s)
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"[*#_`>\[\]{}|~]", "", s)
    s = re.sub(r"^\s*[-•]\s*", "", s, flags=re.M)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def chunk_script(s: str, max_chars=4200) -> list[str]:
    chunks, cur = [], ""
    for para in [p.strip() for p in s.split("\n\n") if p.strip()]:
        if len(para) > max_chars:  # đoạn quá dài → cắt theo câu
            sentences = re.split(r"(?<=[.!?…])\s+", para)
        else:
            sentences = [para]
        for piece in sentences:
            sep = "\n\n" if cur and piece is para else " "
            if cur and len(cur) + len(piece) + 2 > max_chars:
                chunks.append(cur.strip())
                cur = piece
            else:
                cur = f"{cur}{sep}{piece}" if cur else piece
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


# ---------------------------------------------------------------------------
# 3. AUDIO
# ---------------------------------------------------------------------------
def mp3_to_pcm(mp3: bytes) -> bytes:
    """Giải mã MP3 → PCM 16-bit mono 24kHz để ghép các đoạn."""
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-f", "s16le",
                        "-ac", "1", "-ar", str(SAMPLE_RATE), "pipe:1"],
                       input=mp3, capture_output=True, check=True)
    return r.stdout


def elevenlabs_tts(el: dict, text: str, prev_text: str = "", next_text: str = "") -> bytes:
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("Thiếu ELEVENLABS_API_KEY (thêm trong GitHub Secrets)")
    model = el.get("model", "eleven_multilingual_v2")
    body = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": float(el.get("stability", 0.45)),
            "similarity_boost": float(el.get("similarity_boost", 0.8)),
            "style": float(el.get("style", 0.35)),
            "use_speaker_boost": True,
            "speed": float(el.get("speed", 1.0)),
        },
    }
    if model != "eleven_v3":  # v3 không hỗ trợ nối ngữ cảnh
        if prev_text:
            body["previous_text"] = prev_text[-400:]
        if next_text:
            body["next_text"] = next_text[:400]
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{el['voice_id']}"
           "?output_format=mp3_44100_128")
    for attempt in range(3):
        r = requests.post(url, json=body, timeout=300,
                          headers={"xi-api-key": key, "Accept": "audio/mpeg"})
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(20 * (attempt + 1))
            continue
        if r.status_code != 200:
            raise RuntimeError(f"ElevenLabs HTTP {r.status_code}: {r.text[:300]}")
        return mp3_to_pcm(r.content)
    raise RuntimeError("ElevenLabs: hết lượt thử")


_vieneu = None


def vieneu_tts(text: str, voice: str) -> bytes:
    """Giọng VieNeu-TTS (mã nguồn mở, chạy trên CPU, không tốn lượt Gemini). Ra 48kHz → đổi về 24kHz."""
    global _vieneu
    if _vieneu is None:
        from vieneu import Vieneu
        log("   (tải mô hình VieNeu-TTS lần đầu…)")
        _vieneu = Vieneu()
    import numpy as np
    try:
        audio = _vieneu.infer(text, voice=voice) if voice else _vieneu.infer(text)
    except Exception as ex:   # tên giọng sai → dùng giọng mặc định
        log(f"   ! giọng VieNeu '{voice}' lỗi ({ex}) → dùng giọng mặc định")
        audio = _vieneu.infer(text)
    a = np.asarray(audio, dtype=np.float32).reshape(-1)
    raw = (np.clip(a, -1, 1) * 32767).astype("<i2").tobytes()
    return _ffmpeg_pcm(["-f", "s16le", "-ar", "48000", "-ac", "1"], raw)


def speak_chunk(gem, cfg, chunks, n) -> bytes:
    pc = cfg["podcast"]
    provider = pc.get("tts_provider", "gemini")
    ch = chunks[n]
    if provider == "vieneu":
        return vieneu_tts(ch, (cfg.get("vieneu") or {}).get("voice", "Mai Anh"))
    if provider == "elevenlabs":
        return elevenlabs_tts(cfg.get("elevenlabs") or {}, ch,
                              chunks[n - 1] if n > 0 else "",
                              chunks[n + 1] if n + 1 < len(chunks) else "")
    return gem.tts(cfg["models"]["tts"], pc.get("voice", "Leda"), pc.get("voice_style", ""), ch)


def synthesize(gem: Gemini, cfg: dict, script: str, mp3_path: Path) -> float:
    pc = cfg["podcast"]
    chunks = chunk_script(script)
    provider = pc.get("tts_provider", "gemini")
    voice = (cfg.get("elevenlabs") or {}).get("voice_id") if provider == "elevenlabs" else pc.get("voice")
    log(f"   Đọc {len(chunks)} đoạn bằng {provider} · giọng {voice}")
    gap = lambda sec: b"\x00\x00" * int(SAMPLE_RATE * sec)
    style = pc.get("transition", "pause")  # "pause" = ngắt nghỉ êm, "chime" = thêm tiếng chuông
    pcm = b""
    for n in range(len(chunks)):
        log(f"   ♪ đoạn {n + 1}/{len(chunks)} ({len(chunks[n])} ký tự)")
        pcm += clean_chunk(speak_chunk(gem, cfg, chunks, n))
        if n + 1 < len(chunks):
            if style == "chime":
                pcm += gap(0.45) + transition_sound() + gap(0.25)
            else:
                pcm += gap(0.8)
            if provider == "gemini":
                time.sleep(int(pc.get("tts_pause_seconds", 25)))  # gói free giới hạn số lần đọc mỗi phút
    pcm += gap(0.6)
    wav_path = mp3_path.with_suffix(".wav")
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path),
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ac", "1", "-ar", "44100",
                    "-codec:a", "libmp3lame", "-b:a", "80k", str(mp3_path)], check=True)
    wav_path.unlink()
    return len(pcm) / (SAMPLE_RATE * 2)


# ---------------------------------------------------------------------------
# 4. XUẤT BẢN: episodes.json, feed.xml, index.html, Telegram
# ---------------------------------------------------------------------------
def write_feed(out: Path, cfg: dict, episodes: list[dict], site_url: str):
    if not site_url:
        return
    pc = cfg["podcast"]
    base = site_url.rstrip("/")
    esc = html.escape
    items_xml = []
    for e in episodes:
        dt = datetime.fromisoformat(e["date"])
        items_xml.append(f"""  <item>
    <title>{esc(e['title'])}</title>
    <description>{esc(e['summary'])}</description>
    <guid isPermaLink="false">{e['id']}</guid>
    <pubDate>{format_datetime(dt)}</pubDate>
    <enclosure url="{base}/{e['audio']}" length="{e['size']}" type="audio/mpeg"/>
    <itunes:duration>{int(e['duration'])}</itunes:duration>
  </item>""")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
  <title>{esc(pc['name'])}</title>
  <link>{base}/</link>
  <language>vi</language>
  <description>Tin crypto chọn lọc cho nhà đầu tư, đọc bởi {esc(pc.get('host_name', ''))}. Agent build by @Trong0322.</description>
  <itunes:author>{esc(pc.get('author', ''))}</itunes:author>
  <itunes:image href="{base}/cover.png"/>
  <itunes:explicit>false</itunes:explicit>
{chr(10).join(items_xml)}
</channel>
</rss>
"""
    (out / "feed.xml").write_text(xml, encoding="utf-8")


def send_telegram(mp3: Path, ep: dict, cfg: dict, site_url: str):
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return
    esc = html.escape
    api = f"https://api.telegram.org/bot{token}"
    caption = f"🎙️ <b>{esc(ep['title'])}</b>\n{esc(ep['summary'])}"
    try:
        with open(mp3, "rb") as f:
            r = requests.post(f"{api}/sendAudio", timeout=120, data={
                "chat_id": chat, "caption": caption[:1000], "parse_mode": "HTML",
                "title": ep["title"][:60], "performer": cfg["podcast"].get("host_name", ""),
                "duration": int(ep["duration"]),
            }, files={"audio": (mp3.name, f, "audio/mpeg")})
        r.raise_for_status()
        lines = []
        for n, s in enumerate(ep["stories"], 1):
            src = " · ".join(f'<a href="{esc(x["url"])}">{esc(x["name"])}</a>' for x in s["sources"][:2])
            lines.append(f"<b>{n}. {esc(s['headline'])}</b>\n{esc(s.get('why_it_matters', ''))}\n{src}")
        msg = "\n\n".join(lines)
        if site_url:
            msg += f'\n\n🎧 <a href="{esc(site_url)}">Nghe trên web</a>'
        parts, cur = [], ""
        for block in msg.split("\n\n"):  # Telegram giới hạn 4096 ký tự/tin → chia nhiều tin
            if cur and len(cur) + len(block) + 2 > 3900:
                parts.append(cur)
                cur = block
            else:
                cur = f"{cur}\n\n{block}" if cur else block
        if cur:
            parts.append(cur)
        for part in parts:
            requests.post(f"{api}/sendMessage", timeout=60, data={
                "chat_id": chat, "text": part, "parse_mode": "HTML",
                "disable_web_page_preview": "true"}).raise_for_status()
        log("   ✓ Đã gửi Telegram")
    except Exception as ex:
        log(f"   ! Gửi Telegram lỗi: {ex}")


def publish_static(out: Path):
    for name in ("index.html", "cover.png", "logo.png"):
        for src in (ROOT / "site" / name, ROOT / name):
            if src.exists():
                shutil.copy(src, out / name)
                break


SAMPLE_TEXT = ("Ơ kìa, chào cả nhà, {host} đây ạ! Tối nay có tin nóng lắm nhé: SEC vừa duyệt thêm ETF "
               "Solana, dòng tiền vào quỹ đạt 1,2 tỷ đô chỉ trong một tuần. Trong khi đó, Hyperliquid "
               "sắp unlock 10 triệu token HYPE, cả nhà nhớ để ý áp lực bán ngắn hạn nhé! "
               "Đây không phải lời khuyên đầu tư đâu nha, cả nhà tự nghiên cứu kỹ nhé. Hihi, hẹn gặp lại!")


def test_voice(cfg: dict, args):
    pc = cfg["podcast"]
    if args.provider:
        pc["tts_provider"] = args.provider
    if args.voice:
        if pc.get("tts_provider") == "elevenlabs":
            cfg.setdefault("elevenlabs", {})["voice_id"] = args.voice
        else:
            pc["voice"] = args.voice
    if args.model:
        cfg.setdefault("elevenlabs", {})["model"] = args.model
    text = args.text.strip() or SAMPLE_TEXT.format(host=pc.get("host_name", "Mai Hương"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    gem = Gemini(os.getenv("GEMINI_API_KEY", ""))
    mp3 = out / "thu-giong.mp3"
    dur = synthesize(gem, cfg, text, mp3)
    log(f"✓ Đã tạo {mp3} ({dur:.0f} giây)")
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if token and chat:
        provider = pc.get("tts_provider", "gemini")
        voice = (cfg.get("elevenlabs") or {}).get("voice_id") if provider == "elevenlabs" else pc.get("voice")
        model = (cfg.get("elevenlabs") or {}).get("model", "") if provider == "elevenlabs" else ""
        with open(mp3, "rb") as f:
            requests.post(f"https://api.telegram.org/bot{token}/sendAudio", timeout=120, data={
                "chat_id": chat, "caption": f"🎙️ Thử giọng: {provider} · {voice} {model}".strip(),
                "title": f"Thử giọng {voice}"}, files={"audio": (mp3.name, f, "audio/mpeg")})
        log("✓ Đã gửi bản thử vào Telegram")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="public")
    ap.add_argument("--config", default=str(ROOT / "sources.yaml"))
    ap.add_argument("--hours", type=float, default=0, help="ép lấy tin trong N giờ gần nhất")
    ap.add_argument("--test-voice", action="store_true", help="chỉ đọc thử 1 đoạn mẫu")
    ap.add_argument("--provider", default="", help="gemini | elevenlabs (ghi đè sources.yaml)")
    ap.add_argument("--voice", default="", help="tên giọng Gemini hoặc Voice ID ElevenLabs")
    ap.add_argument("--model", default="", help="model ElevenLabs, vd eleven_v3")
    ap.add_argument("--text", default="", help="đoạn văn muốn đọc thử")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.test_voice:
        return test_voice(cfg, args)
    out = Path(args.out)
    (out / "audio").mkdir(parents=True, exist_ok=True)
    publish_static(out)

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit("Thiếu GEMINI_API_KEY (thêm trong GitHub → Settings → Secrets → Actions)")
    site_url = os.getenv("SITE_URL", "").strip()

    state_path, eps_path = out / "state.json", out / "episodes.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    episodes = json.loads(eps_path.read_text()) if eps_path.exists() else []
    seen_list = state.get("seen", [])
    seen = set(seen_list)

    now = datetime.now(timezone.utc)
    # Lịch tự động có nhiều mốc (Cloudflare Worker 5:00 + cron GitHub dự phòng):
    # hôm nay (giờ VN) đã có tập thì bỏ qua. Chạy tay (Run workflow) thì luôn chạy.
    auto_run = os.getenv("RUN_EVENT") == "schedule" or os.getenv("AUTO_TRIGGER") == "1"
    if auto_run and episodes:
        last_ep = datetime.fromisoformat(episodes[0]["date"]).astimezone(VN_TZ)
        if last_ep.date() == now.astimezone(VN_TZ).date():
            log(f"Hôm nay đã có tập lúc {last_ep:%H:%M %d/%m}, lượt tự động này bỏ qua.")
            return
    if args.hours:
        since = now - timedelta(hours=args.hours)
    elif state.get("last_run"):
        since = max(datetime.fromisoformat(state["last_run"]) - timedelta(hours=1),
                    now - timedelta(hours=float(cfg["podcast"].get("lookback_hours", 26))))
    else:
        since = now - timedelta(hours=12)
    log(f"① Gom tin từ {since.astimezone(VN_TZ):%d/%m %H:%M} (giờ VN)")
    items = collect(cfg, since, seen)
    log(f"   Tổng: {len(items)} tin mới")
    if len(items) < 3:
        log("Quá ít tin mới, bỏ qua tập này.")
        return

    gem = Gemini(key)
    now_vn = now.astimezone(VN_TZ)
    log("② AI lọc tin, dịch và viết kịch bản")
    ed, stories, script = build_episode_content(gem, cfg, items, now_vn, episodes)
    if not stories:
        log("Không có tin đủ giá trị, bỏ qua tập này.")
        state.update(seen=(seen_list + [i["id"] for i in items])[-4000:], last_run=now.isoformat())
        state_path.write_text(json.dumps(state))
        return
    log(f"   Chọn {len(stories)} tin · kịch bản {len(script)} ký tự (~{len(script) / 900:.1f} phút)")

    ep_id = now_vn.strftime("%Y%m%d-%H%M")
    mp3 = out / "audio" / f"{ep_id}.mp3"
    log("③ Đọc thành audio")
    duration = synthesize(gem, cfg, script, mp3)
    log(f"   ✓ {mp3.name}: {duration/60:.1f} phút, {mp3.stat().st_size/1e6:.1f} MB")

    ep = {
        "id": ep_id,
        "date": now_vn.isoformat(),
        "title": ed.get("episode_title") or f"Bản tin {now_vn:%d/%m}",
        "summary": ed.get("summary", ""),
        "mood": ed.get("market_mood", ""),
        "audio": f"audio/{mp3.name}",
        "duration": round(duration),
        "size": mp3.stat().st_size,
        "stories": stories,
        "briefs": ed.get("briefs", []),
        "script": script,
    }
    episodes.insert(0, ep)
    keep = int(cfg["podcast"].get("keep_episodes", 40))
    for old in episodes[keep:]:
        (out / old["audio"]).unlink(missing_ok=True)
    episodes = episodes[:keep]

    log("④ Xuất bản")
    eps_path.write_text(json.dumps(episodes, ensure_ascii=False, indent=1), encoding="utf-8")
    write_feed(out, cfg, episodes, site_url)
    (out / "meta.json").write_text(json.dumps({
        "name": cfg["podcast"]["name"], "host": cfg["podcast"].get("host_name", ""),
        "feed": bool(site_url)}, ensure_ascii=False), encoding="utf-8")
    state.update(seen=(seen_list + [i["id"] for i in items])[-4000:], last_run=now.isoformat())
    state_path.write_text(json.dumps(state))
    send_telegram(mp3, ep, cfg, site_url)
    log("✓ Xong!")


if __name__ == "__main__":
    main()
