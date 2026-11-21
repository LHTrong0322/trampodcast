#!/usr/bin/env python3
"""
TRẠM INSIGHT LAB, chuẩn bị "nguyên liệu" để thử nhiều kiểu dựng video từ cùng 1 kịch bản.

  python insight_lab.py prepare --links "<link X>" --voices "vieneu:Hải Đăng,gemini:Ludo"

Kết quả: thư mục lab/<tag>/ (kịch bản, bài gốc, dữ liệu thị trường thật, ảnh, giọng đọc từng đoạn)
được nén và đưa lên GitHub Release "lab-<tag>".
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import requests

import podcast as P
import video as V
import insight as I

log = P.log
SR = V.SR

PROMPT = I.PROMPT.replace(
    '"source_ids": [id bài nguồn]}}',
    '''"source_ids": [id bài nguồn],
      "bullets": ["2-3 ý chính hiện chữ trên màn hình, mỗi ý ≤ 7 từ, tiếng Việt, kiểu ghi chú"],
      "quote": "1 câu ngắn ≤ 18 từ tóm ý đắt nhất của tác giả (diễn giải lại bằng tiếng Việt), có thể trống",
      "data": {{"type": "chọn 1 hình dữ liệu THẬT hợp nhất cho phần này: coin_chart | fear_greed | dominance | market_heatmap | stat_compare | checklist | none",
                "tickers": ["ticker coin nếu type=coin_chart, vd 'BTC'"],
                "items": [{{"label": "≤ 5 từ", "value": "con số/kiểu tiếng Anh ngắn hoặc trống"}}],
                "title": "tiêu đề ngắn cho hình, ≤ 6 từ"}},
      "project": {{"name": "tên dự án/coin CHÍNH được bàn trong phần này (vd Hyperliquid), trống nếu không có", "ticker": "vd HYPE"}},
      "emphasis": "nhãn ≤ 4 từ nếu đây là phần hook đã hứa riêng (vd CÂU NGƯỜI TA BỎ QUA), không thì trống",
      "beats": [{{"at": "3-5 chữ CHÉP NGUYÊN từ lời đọc, hình hiện đúng lúc giọng nói cụm này",
                 "type": "bignum | versus | dots | flow | logos | race | chart | statement | question",
                 "value": "số to (bignum)", "label": "chú thích ngắn", "logo": "TICKER", "tone": "up | down | flat",
                 "left": {{"label": "AAVE", "value": "-25%", "logo": "AAVE", "tone": "down"}}, "right": {{"...": "(versus)"}},
                 "steps": ["(flow) đúng số ý lời đọc nhắc"], "step_at": ["cụm chữ lời đọc cho từng bước"],
                 "tickers": ["(race) 2-3 coin so % cùng kỳ"], "days": "ytd hoặc số ngày (race/chart)", "ticker": "(chart)",
                 "text": "(statement/question) ≤ 10 từ", "hold": "(tuỳ chọn) giữ HÌNH thêm vài giây", "music": "(tuỳ chọn) 2-3 giây giọng nghỉ, nhạc nền dâng lên, cho kết quả quan trọng"}}]}}''')
PROMPT += """
Độ dài: nếu bài nguồn đủ ý, viết đủ {max_sections} phần, mỗi phần 130-180 từ; hook ≤ 2 câu thật cuốn.
Không nhắc đến AI, máy, bot hay "nội dung tổng hợp" ở bất kỳ đâu trong lời đọc.
KHUNG HÌNH (Trọng 22/11, để bot review chấm ≥ 7 mọi mục): mỗi phần 4-6 beats, cứ tối đa 8 giây lời đọc (khoảng 26 chữ) phải có 1 beat mới;
beat đầu gắn vào câu đầu của phần; thẻ question chỉ đứng ≤ 5 giây rồi tới số liệu/ví dụ; không 2 beat liền nhau cùng kiểu;
cả video có ít nhất 1 beat race hoặc chart khi nói về giá (race cho so sánh 2 coin cùng kỳ, days "ytd" nếu nói "từ đầu năm");
lời đọc nói "N thứ/điều/bước" thì flow phải đủ đúng N steps; outro_points đúng bằng số câu đã hứa ở hook;
mỗi phần theo khuôn: câu hỏi 1 câu → 1 con số → 1 ví dụ coin thật → kết luận 1 dòng; nói thẳng "Câu 3: ..." thay vì câu đệm "Câu hỏi thứ ba là".
Ảnh bìa: thumb_text ≤ 24 ký tự, thêm "thumb_tag" (vd "4 CÂU HỎI TRƯỚC KHI MUA"), so sánh thì điền "thumb_vs".
Tiêu đề short (short_hooks) phải có con số hoặc dấu hỏi, ≤ 60 ký tự, tự đứng được một mình.
Gợi ý chọn data.type: nói về tâm lý thị trường → fear_greed; về altcoin vs bitcoin, dòng tiền → dominance;
về coin cụ thể → coin_chart; so sánh 2-4 thứ có số → stat_compare (điền items); danh sách việc cần làm /
tiêu chí đánh giá → checklist (điền items, value để trống); bức tranh toàn thị trường → market_heatmap.
TUYỆT ĐỐI KHÔNG dùng dấu gạch ngang dài (em dash, en dash) ở bất kỳ đâu; cần ngắt ý thì dùng dấu phẩy hoặc dấu chấm.
CẤM HOÀN TOÀN (chủ kênh yêu cầu): KHÔNG nhắc tới ENA / Ethena và chuyện "ENA tăng 95% trong 14 ngày nhờ một thay đổi
duy nhất" ở bất kỳ đâu: không trong hook, intro, lời đọc, tiêu đề, bullets, quote, key_stat, hook_stat, thumb_text,
thumb_stat, short_hooks; không làm phần nào về Ethena; không dùng con số 95% hay mốc 14 ngày. Hãy khai thác các ý khác
của bài (thị trường lemon/coin rác, FDV, PMF, token alignment, Hyperliquid, tâm lý nhà đầu tư, cách chọn tài sản...)."""

# Nội dung chủ kênh cấm đưa vào video (Trọng chốt 20/11): đoạn ENA/Ethena tăng 95% trong 14 ngày
# 19:09 20/11: Trọng đã duyệt kịch bản có nhắc Ethena/ENA (4 việc tự sửa), chỉ cấm con số 95% và mốc 14 ngày
BANNED = re.compile(r"\b95\s*%|\b95\s*phần trăm|chín mươi lăm phần trăm|\b14\s*(ngày|days?)\b|mười bốn ngày", re.I)


def _banned(x) -> bool:
    return bool(BANNED.search(json.dumps(x, ensure_ascii=False) if not isinstance(x, str) else x))


def _scrub_text(t: str) -> str:
    """Bỏ hẳn các câu có nhắc nội dung bị cấm."""
    if not isinstance(t, str) or not _banned(t):
        return t
    sents = re.split(r"(?<=[.!?])\s+", t)
    return " ".join(x for x in sents if not _banned(x)).strip()


def scrub_plan(plan: dict) -> dict:
    """Lọc bằng code: bỏ section/quote/key_stat/hook_stat/thumb_stat... có nhắc ENA 95% hay 14 ngày."""
    secs = plan.get("sections") or []
    keep = [i for i, s in enumerate(secs) if not _banned(s)]
    remap = {old: new for new, old in enumerate(keep)}
    plan["sections"] = [secs[i] for i in keep]
    plan["shorts"] = [remap[i] for i in (plan.get("shorts") or []) if isinstance(i, int) and i in remap]
    sh = plan.get("short_hooks") or {}
    if isinstance(sh, dict):
        nh = {}
        for k, v in sh.items():
            try:
                ki = int(k)
            except Exception:
                continue
            if ki in remap and not _banned(v):
                nh[str(remap[ki])] = v
        plan["short_hooks"] = nh
    for k in ("hook_stat", "hook_label", "thumb_stat", "thumb_text", "thumb", "key_stat", "x_quote"):
        if k in plan and _banned(plan.get(k)):
            plan[k] = ""
    if not plan.get("hook_stat"):
        plan["hook_label"] = ""
    for k in ("title", "description", "theme", "hook", "intro", "outro"):
        if isinstance(plan.get(k), str):
            plan[k] = _scrub_text(plan[k])
    return plan


def fx_raw(url: str) -> dict:
    m = I.X_RE.search(url)
    if not m:
        return {}
    r = requests.get(f"https://api.fxtwitter.com/{m.group(1)}/status/{m.group(2)}", timeout=30,
                     headers={"User-Agent": P.UA})
    return r.json() if r.ok else {}


BRAND_OVERRIDE = {  # màu nhận diện chuẩn của vài dự án lớn (logo đơn sắc khó tự lấy màu)
    "BTC": "#F7931A", "ETH": "#8C9EFF", "SOL": "#14F195", "BNB": "#F3BA2F", "HYPE": "#97FCE4", "ENA": "#F2F2F2",
    "XRP": "#5DB2FF", "DOGE": "#E0C068", "TON": "#3AA6F5", "SUI": "#6FBCF0", "ARB": "#28A0F0", "OP": "#FF0420",
    "AAVE": "#B6509E", "UNI": "#FF007A", "LINK": "#5B8DEF", "PENDLE": "#5BC0DE", "TRX": "#FF3B4B", "AVAX": "#E84142",
}


def brand_color(png: Path) -> str | None:
    """Lấy màu nhận diện từ logo: màu đậm, tươi xuất hiện nhiều nhất (bỏ trắng/đen/xám)."""
    try:
        import colorsys
        from PIL import Image
        im = Image.open(png).convert("RGBA").resize((64, 64))
        cnt = {}
        for r, g, b, a in im.getdata():
            if a < 200:
                continue
            h, l, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if sat < 0.35 or l < 0.18 or l > 0.88:
                continue
            k = (r // 24, g // 24, b // 24)
            cnt[k] = cnt.get(k, 0) + 1
        if not cnt or max(cnt.values()) < 40:
            return None
        r, g, b = [x * 24 + 12 for x in max(cnt, key=cnt.get)]
        h, l, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        r, g, b = colorsys.hls_to_rgb(h, max(l, 0.55), min(1, sat * 1.05))  # đủ sáng trên nền tối
        return "#%02X%02X%02X" % (int(r * 255), int(g * 255), int(b * 255))
    except Exception:
        return None


def gem_vision(gem, cfg, prompt: str, images: list[tuple[str, bytes]]) -> dict:
    """Gửi nhiều ảnh nhỏ + câu hỏi cho Gemini (model chữ), nhận JSON."""
    import base64
    parts = [{"text": prompt}]
    for label, b in images:
        parts += [{"text": f"[{label}]"}, {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(b).decode()}}]

    def call(m):
        data = gem._post(m, {"contents": [{"role": "user", "parts": parts}],
                             "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"}})
        txt = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"] if not p.get("thought"))
        return json.loads(re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M))
    return gem._try_models(cfg["models"]["text"], call)


def _texts(node, out: list):
    """Gom mọi đoạn chữ trong cấu trúc bài Article của X (khối nội dung lồng nhau)."""
    if isinstance(node, dict):
        if isinstance(node.get("text"), str) and node["text"].strip():
            out.append(node["text"].strip())
        for k, v in node.items():
            if k != "text":
                _texts(v, out)
    elif isinstance(node, list):
        for v in node:
            _texts(v, out)


def read_post(url: str, lab: Path) -> dict:
    raw = fx_raw(url)
    (lab / "post_raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    t = raw.get("tweet") or {}
    a = t.get("author") or {}
    art = t.get("article") or {}
    body = []
    if art:
        _texts(art.get("content") or art.get("blocks") or {}, body)
    text = "\n".join(dict.fromkeys(body)).strip()
    if len(text) < 600:
        text = "\n".join(x for x in [art.get("title", ""), art.get("preview_text", ""),
                                     (t.get("raw_text") or {}).get("text") or t.get("text") or "", text] if x)
    # bài quá ngắn → thử mở link trong bài (substack, blog…)
    if len(text) < 1500:
        for u in re.findall(r"https?://\S+", json.dumps(t.get("raw_text") or {}) + " " + (t.get("text") or "")):
            u = u.rstrip('",)')
            if "x.com" in u or "twitter.com" in u:
                continue
            w = I.read_web(u)
            if w and len(w["text"]) > len(text):
                text += "\n\n[Bài đầy đủ] " + w["text"]
                break
    post = {"author": a.get("name") or "", "handle": a.get("screen_name") or "", "url": url,
            "text": text[:12000], "title": art.get("title", ""), "likes": t.get("likes"),
            "retweets": t.get("retweets"), "views": t.get("views"), "created": t.get("created_at", ""),
            "followers": a.get("followers")}
    img = lab / "img"
    img.mkdir(exist_ok=True)
    for name, u in [("avatar", (a.get("avatar_url") or "").replace("_normal", "_400x400")),
                    ("cover", ((art.get("cover_media") or {}).get("media_info") or {}).get("original_img_url")
                     or ((art.get("cover_media") or {}).get("url")) or "")]:
        if u:
            try:
                (img / f"{name}.jpg").write_bytes(requests.get(u, timeout=30).content)
                post[name] = f"img/{name}.jpg"
            except Exception as ex:
                log(f"   ! tải {name} lỗi: {ex}")
    log(f"   Bài gốc: @{post['handle']} · {len(post['text'])} ký tự")
    return post


def market_data(lab: Path) -> dict:
    d: dict = {}
    g = lambda u, **kw: requests.get(u, timeout=30, headers={"User-Agent": P.UA}, **kw).json()
    try:
        d["fear_greed"] = [{"v": int(x["value"]), "label": x["value_classification"], "ts": int(x["timestamp"])}
                           for x in g("https://api.alternative.me/fng/", params={"limit": 30})["data"]]
    except Exception as ex:
        log(f"   ! F&G lỗi: {ex}")
    try:
        gl = g("https://api.coingecko.com/api/v3/global")["data"]
        d["global"] = {"mcap": gl["total_market_cap"]["usd"], "vol": gl["total_volume"]["usd"],
                       "mcap_chg": gl.get("market_cap_change_percentage_24h_usd"),
                       "dominance": gl["market_cap_percentage"]}
    except Exception as ex:
        log(f"   ! global lỗi: {ex}")
    try:
        mk = g("https://api.coingecko.com/api/v3/coins/markets", params={
            "vs_currency": "usd", "order": "market_cap_desc", "per_page": 30, "sparkline": "true",
            "price_change_percentage": "24h,7d,30d"})
        logos = lab / "logos"
        logos.mkdir(exist_ok=True)
        d["markets"] = []
        for c in mk:
            sym = c["symbol"].upper()
            if sym == "ENA":   # Trọng cấm đoạn ENA trong video
                continue
            try:
                (logos / f"{sym}.png").write_bytes(requests.get(c["image"], timeout=20).content)
            except Exception:
                pass
            d["markets"].append({"sym": sym, "name": c["name"], "price": c["current_price"],
                                 "mcap": c["market_cap"], "chg24": c.get("price_change_percentage_24h_in_currency"),
                                 "chg7": c.get("price_change_percentage_7d_in_currency"),
                                 "chg30": c.get("price_change_percentage_30d_in_currency"),
                                 "spark": (c.get("sparkline_in_7d") or {}).get("price", [])[::4]})
    except Exception as ex:
        log(f"   ! markets lỗi: {ex}")
    try:
        ch = g("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart", params={"vs_currency": "usd", "days": 90})
        d["btc_90d"] = [p[1] for p in ch["prices"]][::6]
    except Exception as ex:
        log(f"   ! btc chart lỗi: {ex}")
    log(f"   Dữ liệu thật: {', '.join(d)}")
    return d


NAME_TICKER = {"uniswap": "UNI", "hyperliquid": "HYPE", "aave": "AAVE", "ethena": "ENA", "solana": "SOL", "bitcoin": "BTC",
               "ethereum": "ETH", "chainlink": "LINK", "pendle": "PENDLE", "jupiter": "JUP", "lido": "LDO", "maker": "MKR",
               "sky": "SKY", "virtuals": "VIRTUAL", "arbitrum": "ARB", "optimism": "OP", "celestia": "TIA", "sui": "SUI"}


def _days(v) -> int:
    """Số ngày lấy giá: số nguyên, hoặc "ytd" = từ 1/1 năm nay."""
    if str(v).lower() == "ytd":
        now = datetime.now()
        return max(30, (now - datetime(now.year, 1, 1)).days)
    try:
        return max(7, min(365, int(v)))
    except Exception:
        return 30


def coin_data(lab: Path, plan: dict, data: dict):
    """Giá 30 ngày + logo cho các coin AI nhắc trong phần biểu đồ (vd ENA)."""
    import time
    tick = []
    for s in plan.get("sections", []):
        d = s.get("data") or {}
        if d.get("type") == "coin_chart":
            tick += [str(t).lstrip("$").upper() for t in d.get("tickers") or []]
        pj = (s.get("project") or {}).get("ticker")
        if pj:
            tick.append(str(pj).lstrip("$").upper())
    want: dict = {}
    import voice_ab as VA   # coin được nhắc bằng ticker viết hoa trong lời đọc cũng lấy logo (Trọng 22/11: nhắc dự án là có logo)
    for s_ in plan.get("sections", []):
        for w in re.findall(r"\b[A-Z][A-Z0-9]{2,9}\b", s_.get("narration", "")):
            if w not in VA.SPELL:
                tick.append(w)
        low = s_.get("narration", "").lower()
        tick += [t for n, t in NAME_TICKER.items() if re.search(r"\b" + n + r"\b", low)]
    for b in [b for s in plan.get("sections", []) for b in (s.get("beats") or [])] + (plan.get("hook_beats") or []):
        if b.get("type") == "chart" and b.get("ticker") and b.get("days"):
            want[str(b["ticker"]).lstrip("$").upper()] = _days(b.get("days"))
        for x in [b, b.get("left") or {}, b.get("right") or {}] + list(b.get("items") or []):   # logo coin trong nhịp hình
            if x.get("logo"):
                tick.append(str(x["logo"]).lstrip("$").upper())
        if b.get("type") == "chart" and b.get("ticker"):
            tick.append(str(b["ticker"]).lstrip("$").upper())
        for t in (b.get("tickers") or []) if b.get("type") == "race" else []:   # biểu đồ đua % (Trọng 22/11)
            t = str(t).lstrip("$").upper()
            tick.append(t)
            want[t] = max(want.get(t, 30), _days(b.get("days")))
    data.setdefault("coins", {})
    for t in dict.fromkeys(x for x in tick if re.fullmatch(r"[A-Z0-9]{2,10}", x) and (x != "ENA" or plan.get("allow_ena"))):
        info = V.coin_info(t)
        if not info:
            log(f"   ! không tìm thấy coin {t}")
            continue
        try:
            time.sleep(1.5)
            ch = requests.get(f"https://api.coingecko.com/api/v3/coins/{info['id']}/market_chart",
                              params={"vs_currency": "usd", "days": want.get(t, 30)}, timeout=30).json()
            pts = [p[1] for p in ch.get("prices", [])]
            if len(pts) < 10:
                continue
            (lab / "logos").mkdir(exist_ok=True)
            if info.get("large"):
                (lab / "logos" / f"{t}.png").write_bytes(requests.get(info["large"], timeout=20).content)
            data["coins"][t] = {"name": info.get("name", t), "price": pts[-1], "series": pts[::max(1, len(pts) // 120)],
                                "days": want.get(t, 30), "logo": f"logos/{t}.png" if (lab / "logos" / f"{t}.png").exists() else None,
                                "color": BRAND_OVERRIDE.get(t) or brand_color(lab / "logos" / f"{t}.png")}
            log(f"   Coin {t}: {len(pts)} điểm giá")
        except Exception as ex:
            log(f"   ! giá {t} lỗi: {ex}")


def save_images(lab: Path, plan: dict, gem=None, cfg=None):
    """Tìm ảnh cho từng phần rồi nhờ AI xem từng ảnh: chỉ giữ ảnh ĐÚNG nội dung (loại ảnh đời sống/truyền thống lạc đề)."""
    import io
    img = lab / "img"
    credits = {}
    secs = plan["sections"]
    jobs = [("intro", {"visual_queries": (plan.get("visual_queries") or []) + [plan.get("theme", ""), "cryptocurrency trading chart screen"],
                       "category": "Dự án"}, "landscape", 6)]
    for k, s in enumerate(secs):
        jobs.append((f"s{k}", {"visual_queries": s.get("visual_queries") or [], "category": "Dự án",
                               "visual_query": s.get("heading", "")}, "landscape", 6))
    topics = {"intro": plan.get("title", "")}
    for k, s in enumerate(secs):
        topics[f"s{k}"] = s.get("heading", "")
    thumbs = []
    for name, item, ori, n in jobs:
        files = []
        for i, (im, cr) in enumerate(V.find_images(item, ori, n)):
            fn = f"{name}_{i}.jpg"
            im.save(img / fn, quality=90)
            files.append(fn)
            credits[fn] = cr
            t = im.copy()
            t.thumbnail((384, 384))
            b = io.BytesIO()
            t.convert("RGB").save(b, "JPEG", quality=70)
            thumbs.append((fn, b.getvalue()))
        plan.setdefault("images", {})[name] = files
    plan["image_credits"] = credits
    if gem and thumbs:
        try:
            ask = ("Bạn là biên tập viên hình ảnh cho video YouTube về crypto/đầu tư. Chủ đề từng nhóm ảnh:\n"
                   + "\n".join(f"- {k}: {v}" for k, v in topics.items())
                   + "\nVới MỖI ảnh (nhãn dạng <nhóm>_<số>.jpg), chấm 0-10 mức LIÊN QUAN trực tiếp tới chủ đề nhóm đó và tới "
                     "crypto/tài chính/công nghệ. Chấm thấp (≤4) ảnh đời sống, truyền thống, phong cảnh, động vật, đồ ăn, "
                     "trẻ em, ảnh văn phòng chung chung không ăn nhập, ảnh có chữ/logo thương hiệu khác. "
                     'Trả JSON: {"scores": {"<nhãn>": số}}')
            sc = gem_vision(gem, cfg, ask, thumbs).get("scores", {})
            for name in list(plan["images"]):
                keep = [f for f in plan["images"][name] if float(sc.get(f, 0)) >= 7]
                drop = [f for f in plan["images"][name] if f not in keep]
                plan["images"][name] = keep
                for f in drop:
                    (img / f).unlink(missing_ok=True)
            log(f"   Lọc ảnh bằng AI: giữ {sum(len(v) for v in plan['images'].values())}/{len(thumbs)} ảnh")
        except Exception as ex:
            log(f"   ! lọc ảnh lỗi ({ex}) → không dùng ảnh kho")
            plan["images"] = {k: [] for k in plan["images"]}


def speak(cfg: dict, voice: str, parts: list[str], outdir: Path) -> bool:
    prov, name = voice.split(":", 1)
    outdir.mkdir(parents=True, exist_ok=True)
    cfg["podcast"]["tts_provider"] = prov
    if prov == "vieneu":
        cfg.setdefault("vieneu", {})["voice"] = name
        for i, t in enumerate(parts):
            V.pcm_to_wav(V.tts_once(None, cfg, t), outdir / f"{i:02d}.wav")
        return True
    key = os.getenv("INSIGHT_GEMINI_API_KEY", "")
    if not key and os.getenv("ALLOW_MAIN_KEY") != "1":
        log(f"   ⚠️ Chưa có INSIGHT_GEMINI_API_KEY → bỏ qua giọng Gemini {name} để giữ lượt cho podcast")
        return False
    # "Ludo@kol": giọng Ludo + lời dặn phong cách (Trọng chọn mẫu N "vibe KOL crypto" 21/11)
    name, _, style = name.partition("@")
    cfg["podcast"]["voice"] = name
    cfg["podcast"]["voice_style"] = ""
    if style:
        import voice_ludo2 as VL
        cfg["podcast"]["voice_style"] = VL.STYLE[style]
    gem = P.Gemini(key or os.getenv("GEMINI_API_KEY", ""))
    import subprocess
    import time
    # mỗi đoạn đọc riêng 1 lượt → không bao giờ bị cắt giữa câu khi chia lại audio
    for i, t in enumerate(parts):
        if i:
            time.sleep(int(cfg["podcast"].get("tts_pause_seconds", 25)))
        if not style:
            V.pcm_to_wav(V.tts_once(gem, cfg, t), outdir / f"{i:02d}.wav")
            continue
        import voice_ab as VA
        import voice_master as VM
        import tts_qa
        # đoạn ngắn để nguyên 1 dòng (tách dòng làm máy dễ đọc lặp câu mở đầu, log 21/11)
        txt = VA.speakable(t) if len(t.split()) < 60 else VL.lines(VA.speakable(t))
        # Kho giọng đã đọc (nhánh podcast-data): đoạn nào đã đọc đạt rồi thì lần dựng sau dùng lại, không tốn lượt Gemini
        import hashlib
        cache = Path(os.getenv("TTS_CACHE", "public/insight/tts-cache"))
        key = hashlib.sha1(f"{name}|{style}|{cfg['podcast'].get('voice_style','')}|{txt}".encode()).hexdigest()[:20]
        hit = cache / f"{key}.wav"
        if hit.exists():
            shutil.copy(hit, outdir / f"{i:02d}.wav")
            log(f"   ♻ đoạn {i}: dùng lại giọng đã đọc (không tốn lượt)")
            continue
        raw = outdir / f"{i:02d}.raw.wav"
        # Trọng chốt 21/11: nghe lại từng đoạn trước khi dựng, lặp/thiếu/thừa thì đọc lại (tối đa 4 lần)
        for attempt in range(4):
            pcm = V.tts_once(gem, cfg, txt)
            sec = len(pcm) / (P.SAMPLE_RATE * 2)
            if sec > len(txt.split()) / 150 * 60 * 1.35:
                why = f"dài bất thường {sec:.0f}s"
            else:
                V.pcm_to_wav(pcm, raw)
                ok, why = tts_qa.check(str(raw), t)
                if ok:
                    log(f"   ✓ đoạn {i}: {why}")
                    break
            log(f"   ! đoạn {i} lỗi ({why}), đọc lại lần {attempt + 2}")
            time.sleep(10)
        else:
            raise RuntimeError(f"đoạn {i} đọc lỗi 4 lần ({why}), dừng dựng để không gửi video lỗi")
        # làm đẹp giọng kiểu studio, giữ nguyên tốc độ
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", VM.CHAIN.format(tempo=1.0),
                        "-ar", str(P.SAMPLE_RATE), "-ac", "1", "-c:a", "pcm_s16le", str(outdir / f"{i:02d}.wav")],
                       check=True)
        raw.unlink()
        try:
            cache.mkdir(parents=True, exist_ok=True)
            shutil.copy(outdir / f"{i:02d}.wav", hit)
            import time as _t
            for old_f in cache.glob("*.wav"):   # giữ kho gọn: xoá file quá 10 ngày
                if _t.time() - old_f.stat().st_mtime > 10 * 86400:
                    old_f.unlink()
        except Exception as ex:
            log(f"   ! không lưu được kho giọng: {ex}")
    return True


# Trọng chốt 21/11 (sau video zeroxkyle): luôn dùng từ tiếng Anh cho các khái niệm này, kể cả kịch bản đã duyệt
TERM_FIX = [
    (r"(?i)(các |những )?nhà đầu tư nhỏ lẻ", "retail"),
    (r"(?i)người chơi nhỏ lẻ", "retail"),
    (r"(?i)\bnhỏ lẻ\b", "retail"),
    (r"(?i)những người trong cuộc|người trong cuộc", "insider"),
    (r"(?i)mở kho[áa]", "unlock"),
    (r"(?i)(?<!hứa )(?<!cam kết )lợi nhuận", "revenue"),
]


def fix_terms(obj, key: str = ""):
    """Đổi từ ở mọi chữ trong kịch bản (lời đọc + chữ trên hình), trừ bài gốc và link."""
    if key in ("posts", "url", "urls", "source_ids", "visual_queries"):
        return obj
    if isinstance(obj, dict):
        return {k: fix_terms(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fix_terms(v, key) for v in obj]
    if isinstance(obj, str):
        for pat, rep in TERM_FIX:
            obj = re.sub(pat, rep, obj)
        return re.sub(r"(^|[.!?]\s+)(insider|retail|unlock|revenue)\b", lambda m: m.group(1) + m.group(2).capitalize(), obj)
    return obj


def prepare(posts_or_links, out: Path, voices: list[str] | None = None, release: bool = False,
            notes: list[str] | None = None) -> Path:
    """Viết kịch bản + lấy dữ liệu/ảnh + đọc giọng. Giọng: thử lần lượt theo danh sách (Gemini Ludo trước,
    hết lượt thì VieNeu Hải Đăng), cả video luôn dùng MỘT giọng."""
    cfg = V.load_cfg()
    ic = cfg.get("insight") or {}
    env_v = os.getenv("INSIGHT_VOICE", "").strip()
    # Trọng chốt 20/11: chỉ dùng giọng Ludo, hết lượt Gemini thì DỪNG (không tự đổi sang giọng khác)
    voices = voices or [env_v or ic.get("voice_primary", "gemini:Ludo")]
    tag = datetime.now(P.VN_TZ).strftime("%Y%m%d-%H%M")
    lab = out / tag
    lab.mkdir(parents=True, exist_ok=True)
    (lab / "img").mkdir(exist_ok=True)
    if isinstance(posts_or_links, str):
        posts = [read_post(u, lab) for u in posts_or_links.split() if u.strip()]
    else:
        posts = []
        for p in posts_or_links:  # bài từ hộp thư Telegram: đọc lại bản đầy đủ nếu là link X
            full = read_post(p["url"], lab) if I.X_RE.search(p.get("url", "")) else None
            posts.append(full if full and len(full["text"]) >= len(p.get("text", "")) else
                         {"author": p.get("author", ""), "handle": p.get("handle", ""), "url": p.get("url", ""),
                          "text": p.get("text", ""), "title": p.get("title", "")})
    gem = P.Gemini(os.getenv("INSIGHT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", ""))
    listing = "\n\n".join(f"[{i}] @{p['handle']} ({p['author']}), {p.get('title', '')}:\n{p['text'][:9000]}"
                          for i, p in enumerate(posts))
    system = I.SYSTEM.format(name=ic.get("name", "Smart Penguin Insights"), host_desc=ic.get("host_desc", "điềm đạm, sâu sắc"),
                             self_word=ic.get("self_word", "mình"), audience=ic.get("audience", "mọi người"))
    log("② Viết kịch bản")
    prompt = PROMPT.format(posts=listing, minutes=ic.get("target_minutes", 7), max_sections=ic.get("max_sections", 6))
    if notes:
        prompt += "\nRút kinh nghiệm từ review các video trước (áp dụng):\n" + "\n".join(f"- {n}" for n in notes)
    plan = {}
    approved = os.getenv("INSIGHT_SCRIPT", "").strip()   # kịch bản Trọng đã duyệt (JSON) → dựng đúng lời đọc, không để AI viết lại
    if approved:
        plan = P.nodash(json.loads(Path(approved).read_text(encoding="utf-8")))
        log(f"   Dùng kịch bản đã duyệt: {approved} ({len(plan.get('sections', []))} phần)")
    for attempt in range(0 if approved else 3):
        plan = P.nodash(V.llm_json(gem, cfg, system, prompt))
        top = {k: plan.get(k) for k in ("title", "hook", "hook_stat", "intro", "thumb_text", "thumb_stat")}
        n_ok = len([s for s in plan.get("sections", []) if s.get("narration") and not _banned(s)])
        if not _banned(top) and n_ok >= 3:
            break
        log(f"   ! kịch bản còn nhắc ENA/95%/14 ngày (lần {attempt + 1}), viết lại")
    if not approved and os.getenv("CLAUDE_CODE_OAUTH_TOKEN"):
        # Trọng chốt 21/11: VÒNG 1, Claude chấm kịch bản, dưới 8 điểm thì viết lại theo góp ý (tối đa 2 lần)
        import script_review as SR
        src = "\n\n".join(p.get("text", "")[:6000] for p in posts)
        rv = {}
        for rnd in range(3):
            try:
                import video_lint as VL
                lint = VL.lint(plan)
                rv = SR.review(json.dumps(plan, ensure_ascii=False, indent=1) +
                               ("\n\nLỖI KHUNG MÁY TỰ PHÁT HIỆN (mỗi lỗi trừ hinh_anh và giu_chan, phải sửa hết):\n" + "\n".join(f"- {x}" for x in lint) if lint else ""), src)
            except Exception as ex:
                log(f"   ! chấm kịch bản lỗi: {str(ex)[:150]}")
                break
            log(f"   Vòng 1 chấm kịch bản lần {rnd + 1}: {rv.get('score')} điểm")
            if rv.get("pass") or rnd == 2:
                break
            fix = prompt + "\nBản trước bị chấm " + str(rv.get("score")) + "/10. Sửa ĐÚNG các điểm sau:\n" + \
                "\n".join(f"- {x}" for x in rv.get("fixes", []))
            plan = P.nodash(V.llm_json(gem, cfg, system, fix))
        plan["script_score"] = rv.get("score")
    plan = scrub_plan(plan)
    plan = fix_terms(plan)   # Trọng chốt 21/11: tự đổi từ Việt sang từ chuyên ngành tiếng Anh
    try:   # Trọng 22/11: soát khung (nhịp đổi hình, biểu đồ, đếm ý, ảnh bìa, short) trước khi tốn lượt giọng đọc
        import video_lint as VL
        plan["lint"] = VL.lint(plan)
        log(f"   Soát khung: {len(plan['lint'])} chỗ cần sửa" + "".join(f"\n     - {x}" for x in plan["lint"][:12]))
    except Exception as ex:
        log(f"   ! soát khung lỗi: {ex}")
    if len([s for s in plan.get("sections", []) if s.get("narration")]) < 2 or not plan.get("hook"):
        raise RuntimeError("Kịch bản không đủ nội dung sau khi bỏ đoạn ENA")
    plan["sections"] = [s for s in plan.get("sections", []) if s.get("narration")][: int(ic.get("max_sections", 6))]
    plan["posts"] = posts
    log("③ Dữ liệu thị trường + ảnh (AI lọc ảnh lạc đề)")
    md = market_data(lab)
    coin_data(lab, plan, md)
    (lab / "data.json").write_text(json.dumps(md, ensure_ascii=False), encoding="utf-8")
    save_images(lab, plan, gem, cfg)
    parts = [("hook", plan.get("hook", "")), ("intro", plan.get("intro", ""))]
    parts += [(f"s{k}", s["narration"]) for k, s in enumerate(plan["sections"])]
    parts += [("outro", plan.get("outro", ""))]
    plan["shorts"] = [i for i in plan.get("shorts", []) if isinstance(i, int) and 0 <= i < len(plan["sections"])][
                     : int(ic.get("shorts", 3))]
    # Trọng 22/11: cuối MỌI short có câu mời xem full video (đọc 1 lần, ghép vào cuối từng short)
    if plan["shorts"]:
        plan["short_cta"] = P.nodash(str(plan.get("short_cta") or ic.get("short_cta") or "")).strip()
        parts += [("short_cta", plan["short_cta"])]
    parts = [(k, P.sanitize_script(t)) for k, t in parts if t and t.strip()]
    plan["parts"] = [{"key": k, "text": t} for k, t in parts]
    plan["voices"] = {}
    for v in voices:
        log(f"④ Đọc giọng {v}")
        vd = re.sub(r"\W+", "_", v)
        try:
            ok = speak(cfg, v, [t for _, t in parts], lab / "audio" / vd)
        except Exception as ex:
            log(f"   ! giọng {v} lỗi: {str(ex)[:300]} → chuyển giọng dự phòng")
            ok = False
        if ok:
            plan["voices"][v] = vd
            plan["voice"] = v
            break
    if not plan.get("voice"):
        raise RuntimeError("Không đọc được giọng nào")
    (lab / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    if release and os.getenv("GITHUB_REPOSITORY") and os.getenv("GH_TOKEN"):
        zp = shutil.make_archive(str(out / f"lab-{tag}"), "zip", lab)
        subprocess.run(["gh", "release", "create", f"lab-{tag}", zp, "-R", os.environ["GITHUB_REPOSITORY"], "--prerelease",
                        "--title", f"Lab nguyên liệu {tag}", "--notes", plan.get("title", "")], check=True)
    log(f"✓ Nguyên liệu xong: {lab} · giọng {plan['voice']}")
    return lab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare"])
    ap.add_argument("--links", default="")
    ap.add_argument("--voices", default="")
    ap.add_argument("--out", default="lab")
    a = ap.parse_args()
    prepare(a.links, Path(a.out), [v.strip() for v in a.voices.split(",") if v.strip()] or None, release=True)


if __name__ == "__main__":
    main()
