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

def _rep(s: str, old: str, new: str) -> str:
    """Thay 1 đoạn trong PROMPT gốc; báo lỗi ngay nếu không tìm thấy (tránh âm thầm dùng prompt cũ)."""
    if old not in s:
        raise RuntimeError(f"PROMPT gốc đã đổi, không tìm thấy: {old[:60]}")
    return s.replace(old, new)


_P = I.PROMPT
_P = _rep(_P, '"hook": "câu mở màn ≤ 16 từ gây tò mò mạnh, đọc ~3 giây, không chào hỏi"',
          '"hook": "ĐÚNG 2 câu ngắn, tổng ≤ 24 từ, không chào hỏi. Câu 1 chứa MỘT con số gây sốc có thật trong bài '
          '(chính là hook_stat) và chạm vào nỗi đau/lợi ích người xem. Câu 2 hứa giá trị CỤ THỂ người xem nhận được '
          '(vd \'Đây là lý do, và 3 tiêu chí để lọc.\')"')
_P = re.sub(r'"hook_stat": "[^\n]*",', lambda m: '"hook_stat": "CHÍNH LÀ con số trong câu 1 của hook, viết y hệt '
            '(vd \'90%\'); hook không có số thật thì để trống",', _P, count=1)
_P = _rep(_P, '"hook_label": "giải thích ≤ 6 từ"', '"hook_label": "giải thích con số ≤ 6 từ"')
_P = _rep(_P, '"intro": "lời chào + giới thiệu tập (~300 ký tự)"',
          '"intro": "≤ 28 từ, đọc ≤ 8 giây: nửa câu ghi nguồn (vd \'Ý tưởng từ bài viết của @abc.\') rồi đọc NGUYÊN VĂN câu open_loop",\n'
          '  "open_loop": "câu vòng lặp mở ≤ 14 từ, hứa điều sẽ có ở CUỐI video, khớp actions (vd \'Cuối video, mình chỉ 3 tiêu chí lọc coin làm được ngay.\')"')
_P = _rep(_P, '"narration": "lời giảng 4-7 câu (~450-700 ký tự): insight là gì, vì sao đúng, ví dụ, cách áp dụng"',
          '"narration": "lời giảng 7-11 câu NGẮN, mỗi câu 10-15 từ, 1 ý = 1 câu. Câu ĐẦU TIÊN là câu hỏi hoặc con số '
          '(vd \'Vì sao Ethena tăng 95% trong 14 ngày?\'), KHÔNG mở bằng \'Theo Kyle trên X\' (nêu nguồn tự nhiên ở giữa phần). '
          'Gồm: insight là gì, vì sao đúng, 1 ví dụ đời thường, cách áp dụng"')
_P = _rep(_P, '"outro": "tổng kết 2-3 ý chính + nhắc không phải lời khuyên đầu tư + mời đăng ký (~280 ký tự)"',
          '"outro": "≤ 75 từ: đọc lần lượt 3 tiêu chí trong actions (Một là..., Hai là..., Ba là...), rồi đọc NGUYÊN VĂN câu question, '
          'nhắc không phải lời khuyên đầu tư, mời đăng ký",\n'
          '  "actions": ["ĐÚNG 3 tiêu chí/hành động người xem làm được NGAY, mỗi cái ≤ 7 từ (vd \'Có doanh thu thật\', '
          '\'Lịch unlock rõ ràng\', \'Có cơ chế buyback\')"],\n'
          '  "question": "1 câu hỏi ≤ 16 từ kéo bình luận, gắn chủ đề (vd \'Coin bạn đang giữ đạt mấy tiêu chí?\')"')
_P = _rep(_P, '"short_hooks": {{"số thứ tự section": "câu hook ≤ 12 từ đọc ~2 giây"}}',
          '"short_hooks": {{"số thứ tự section": "câu hook GÂY SỐC ≤ 10 từ hiện chữ to ở giây đầu video ngắn; nếu có số thì dùng '
          'đúng con số trong lời đọc phần đó"}}')
_P = _rep(_P, '"thumb_text": "3-5 từ IN HOA cho ảnh bìa", "thumb_stat": "con số ngắn cho ảnh bìa, có thể trống"}}',
          '"thumb_text": "2-5 từ IN HOA hứa GIÁ TRỊ HÀNH ĐỘNG ĐƯỢC (vd \'CÁCH LỌC COIN RÁC\', \'3 TIÊU CHÍ CHỌN ALTCOIN\'), '
          'KHÔNG giật tít tiêu cực kiểu \'SẮP CHẾT\', \'SẬP\', \'TOANG\'", '
          '"thumb_stat": "con số ngắn cho ảnh bìa (thường = hook_stat), có thể trống", '
          '"thumb_points": ["3 nhãn ≤ 3 từ rút gọn từ actions để hiện checklist trên ảnh bìa (vd \'Doanh thu thật\')"]}}')

PROMPT = _P.replace(
    '"source_ids": [id bài nguồn]}}',
    '''"source_ids": [id bài nguồn],
      "bullets": ["2-3 ý chính hiện chữ trên màn hình, mỗi ý ≤ 7 từ, tiếng Việt, kiểu ghi chú"],
      "quote": "1 câu ngắn ≤ 18 từ tóm ý đắt nhất của tác giả (diễn giải lại bằng tiếng Việt), có thể trống",
      "data": {{"type": "chọn 1 hình dữ liệu THẬT hợp nhất cho phần này: coin_chart | fear_greed | dominance | market_heatmap | stat_compare | checklist | none",
                "tickers": ["ticker coin nếu type=coin_chart, vd 'BTC'"],
                "items": [{{"label": "≤ 5 từ", "value": "con số/kiểu tiếng Anh ngắn hoặc trống"}}],
                "title": "tiêu đề ngắn cho hình, ≤ 6 từ",
                "period_days": "CHỈ cho coin_chart nói về 1 SỰ KIỆN giá trong quá khứ: số ngày của sự kiện (vd 14 nếu 'tăng 95% trong 14 ngày'), không rõ thì null",
                "end_days_before_post": "sự kiện đó kết thúc bao nhiêu ngày TRƯỚC ngày đăng bài nguồn (0 nếu kéo dài tới lúc đăng), không rõ thì null",
                "claim_pct": "% thay đổi giá mà lời đọc khẳng định (vd 95 hoặc -40), không nói thì null"}},
      "project": {{"name": "tên dự án/coin CHÍNH được bàn trong phần này (vd Hyperliquid), trống nếu không có", "ticker": "vd HYPE"}},
      "x_quotes": [{{"text": "1-2 câu highlight NGUYÊN VĂN của tác giả, COPY CHÍNH XÁC từng chữ từ bài nguồn (giữ tiếng Anh), mỗi câu ≤ 30 từ", "vi": "bản dịch tiếng Việt tự nhiên, sát nghĩa, đọc mượt (đây là chữ hiện trên video)"}}],
      "emphasis": ["3-5 cụm từ QUAN TRỌNG NHẤT trong lời đọc phần này (2-4 từ mỗi cụm, chép ĐÚNG từng chữ trong narration) để in đậm trên phụ đề"],
      "terms": [{{"term": "thuật ngữ crypto khó xuất hiện trong lời đọc phần này (vd FDV, Low Float), tối đa 2", "explain": "giải thích ≤ 12 từ bằng TIẾNG VIỆT dễ hiểu"}}]}}''')
PROMPT += """
Độ dài: nếu bài nguồn đủ ý, viết đủ {max_sections} phần, mỗi phần 120-170 từ.
Không nhắc đến AI, máy, bot hay "nội dung tổng hợp" ở bất kỳ đâu trong lời đọc.
key_stat mỗi phần phải là con số/bằng chứng MỚI, KHÔNG lặp lại hook_stat.
Gợi ý chọn data.type: lời đọc phần đó nói trực tiếp về tâm lý thị trường HIỆN TẠI → fear_greed (không dùng làm hình minh hoạ chung chung); về altcoin vs bitcoin, dòng tiền → dominance;
về giá 1 coin cụ thể → coin_chart; so sánh 2-4 thứ có số → stat_compare (điền items); danh sách việc cần làm,
tiêu chí đánh giá → checklist (điền items, value để trống); bức tranh toàn thị trường → market_heatmap.
stat_compare CHỈ dùng khi MỌI value là con số cùng đơn vị, so sánh được (vd doanh thu dự án A vs B); không trộn % với ngày;
value là chữ thì dùng checklist.
coin_chart nói về sự kiện giá trong QUÁ KHỨ (vd "ENA tăng 95% trong 14 ngày") thì BẮT BUỘC điền period_days,
end_days_before_post, claim_pct để vẽ đúng khoảng thời gian đó; không xác định được thời gian thì chọn type none.
hook_stat / thumb_stat: con số THẬT trong bài, nói về THỊ TRƯỜNG hoặc DỰ ÁN và gắn trực tiếp với luận điểm chính của video
(vd % altcoin sụt giảm, doanh thu dự án, % tăng sau khi đổi tokenomics). TUYỆT ĐỐI không lấy số về thu nhập/lợi nhuận cá nhân,
số người đăng ký, quảng cáo của tác giả, hay điểm số kiểu "10/10". Không chắc thì để trống. Cả video chỉ xoay quanh MỘT
con số mở màn; số liệu mỗi phần phải khớp đúng bài nguồn (không làm tròn khác nhau giữa các chỗ).
Giữa video (cuối phần 2) chèn 1 câu ngắn mời người xem bình luận ý kiến của họ.
Thuật ngữ crypto (DCA, FDV, unlock, buyback, tokenomics, airdrop...) giữ tiếng Anh. Thuật ngữ KHÔNG thuộc crypto
(vd PTSD, lemon market, survivorship bias, sunk cost) PHẢI nói bằng TIẾNG VIỆT trong lời đọc và mọi chữ trên hình
(vd PTSD → "sang chấn tâm lý", lemon market → "thị trường chanh, nơi hàng tốt bị hàng xấu đè"), không để nguyên tiếng Anh.
Không dùng dấu gạch ngang dài ở bất kỳ trường nào; dùng dấu phẩy hoặc hai chấm.
Lời đọc: câu ngắn 10-15 từ, nhiều từ nối kiểu "Nhưng...", "Tại sao?", "Kết quả là..." để giữ nhịp; không lan man."""

# thuật ngữ KHÔNG thuộc crypto → tiếng Việt (lưới an toàn sau khi AI viết kịch bản)
NONCRYPTO_VI = {
    r"PTSD": "sang chấn tâm lý",
    r"post[- ]traumatic stress(?: disorder)?": "sang chấn tâm lý",
    r"lemons? markets?|market for lemons|market of lemons": "thị trường chanh",
    r"adverse selection": "lựa chọn bất lợi",
    r"information asymmetry|asymmetric information": "bất cân xứng thông tin",
    r"survivorship bias": "thiên kiến kẻ sống sót",
    r"confirmation bias": "thiên kiến xác nhận",
    r"sunk cost(?: fallacy)?": "chi phí chìm",
    r"opportunity cost": "chi phí cơ hội",
    r"game theory": "lý thuyết trò chơi",
    r"burn ?out": "kiệt sức",
    r"trauma": "sang chấn",
    r"learned helplessness": "bất lực tập nhiễm",
}


def vi_terms(x, skip=("posts", "visual_queries")):
    """Đổi thuật ngữ không thuộc crypto sang tiếng Việt trong mọi chữ của kịch bản (đệ quy).
    Câu trích nguyên văn tiếng Anh (x_quotes.text) giữ nguyên để còn đối chiếu bài gốc; bản dịch (vi) thì đổi."""
    if isinstance(x, str):
        for pat, vi in NONCRYPTO_VI.items():
            x = re.sub(rf"(?i)(?<![\w]){pat}(?![\w])", vi, x)
        # "thị trường chanh (thị trường chanh)" → bỏ phần lặp
        return re.sub(r"([^()\n]{3,40}?)\s*\(\s*\1\s*\)", r"\1", x)
    if isinstance(x, list):
        return [vi_terms(i, skip) for i in x]
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            if k in skip:
                out[k] = v
            elif k == "x_quotes" and isinstance(v, list):
                out[k] = [{**q, "vi": vi_terms(q.get("vi", ""))} if isinstance(q, dict) else q for q in v]
            else:
                out[k] = vi_terms(v, skip)
        return out
    return x


def fx_raw(url: str) -> dict:
    m = I.X_RE.search(url)
    if not m:
        return {}
    r = requests.get(f"https://api.fxtwitter.com/{m.group(1)}/status/{m.group(2)}", timeout=30,
                     headers={"User-Agent": P.UA})
    return r.json() if r.ok else {}


BRAND_OVERRIDE = {  # màu nhận diện chuẩn của vài dự án lớn (logo đơn sắc khó tự lấy màu)
    "BTC": "#F7931A", "ETH": "#8C9EFF", "SOL": "#14F195", "BNB": "#F3BA2F", "HYPE": "#97FCE4", 
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
    data.setdefault("coins", {})
    for t in dict.fromkeys(x for x in tick if re.fullmatch(r"[A-Z0-9]{2,10}", x)):
        info = V.coin_info(t)
        if not info:
            log(f"   ! không tìm thấy coin {t}")
            continue
        try:
            time.sleep(1.5)
            ch = requests.get(f"https://api.coingecko.com/api/v3/coins/{info['id']}/market_chart",
                              params={"vs_currency": "usd", "days": 30}, timeout=30).json()
            pts = [p[1] for p in ch.get("prices", [])]
            if len(pts) < 10:
                continue
            (lab / "logos").mkdir(exist_ok=True)
            if info.get("large"):
                (lab / "logos" / f"{t}.png").write_bytes(requests.get(info["large"], timeout=20).content)
            data["coins"][t] = {"name": info.get("name", t), "price": pts[-1], "series": pts[::max(1, len(pts) // 120)],
                                "days": 30, "logo": f"logos/{t}.png" if (lab / "logos" / f"{t}.png").exists() else None,
                                "color": BRAND_OVERRIDE.get(t) or brand_color(lab / "logos" / f"{t}.png")}
            log(f"   Coin {t}: {len(pts)} điểm giá")
        except Exception as ex:
            log(f"   ! giá {t} lỗi: {ex}")
    event_charts(plan, data)


def post_date(plan: dict):
    """Ngày đăng bài nguồn (fxtwitter: 'Sun Oct 04 02:25:05 +0000 2026')."""
    for p in plan.get("posts") or []:
        c = p.get("created") or ""
        for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(c.replace("Z", "+0000"), fmt)
            except Exception:
                pass
    return None


def _num(x):
    try:
        return float(str(x).replace("%", "").replace("+", "").strip())
    except Exception:
        return None


def event_charts(plan: dict, data: dict):
    """Biểu đồ KHỚP MẠCH KỂ: sự kiện giá trong quá khứ (vd 'ENA tăng 95% trong 14 ngày') → lấy giá đúng khoảng
    thời gian đó (CoinGecko market_chart/range, tính từ ngày đăng bài). Không xác định được, hoặc giá thật trái
    ngược lời nói → bỏ biểu đồ (cảnh đó dùng thẻ số liệu). Kết quả: data['charts']['s<k>']."""
    import time
    from datetime import timedelta
    pd = post_date(plan)
    data.setdefault("charts", {})
    for k, s in enumerate(plan.get("sections", [])):
        d = s.get("data") or {}
        if d.get("type") != "coin_chart":
            continue
        t = str((d.get("tickers") or [""])[0] or "").lstrip("$").upper()
        days, endb, claim = _num(d.get("period_days")), _num(d.get("end_days_before_post")), _num(d.get("claim_pct"))
        key = f"s{k}"
        if not days:
            # biểu đồ "giá gần đây" chỉ được dùng khi lời đọc không khẳng định % tăng/giảm nào
            c = (data.get("coins") or {}).get(t)
            if c and c.get("series") and claim is None:
                data["charts"][key] = {"ticker": t, "series": c["series"], "days": c.get("days", 30), "recent": True,
                                       "end": datetime.now(P.VN_TZ).strftime("%d/%m/%Y")}
            else:
                log(f"   Biểu đồ {key} ({t}): lời đọc nói {claim}% nhưng không rõ thời điểm → dùng thẻ số liệu")
            continue
        info = V.coin_info(t) if pd else None
        if not info:
            log(f"   Biểu đồ {key} ({t}): thiếu ngày đăng bài hoặc không tìm thấy coin → thẻ số liệu")
            continue
        end = pd - timedelta(days=endb or 0)
        start = end - timedelta(days=days)
        pts = []
        for attempt in range(3):  # CoinGecko miễn phí hay báo 429 (gọi quá nhanh) → chờ rồi thử lại
            try:
                time.sleep(2 + 8 * attempt)
                r = requests.get(f"https://api.coingecko.com/api/v3/coins/{info['id']}/market_chart/range", timeout=30,
                                 params={"vs_currency": "usd", "from": int(start.timestamp()), "to": int(end.timestamp())},
                                 headers={"User-Agent": P.UA})
                if r.ok:
                    pts = [p[1] for p in r.json().get("prices", [])]
                    break
                log(f"   ! giá {t} theo khoảng: HTTP {r.status_code} {r.text[:120]}")
            except Exception as ex:
                log(f"   ! giá {t} theo khoảng lỗi: {ex}")
        if len(pts) < 5:
            log(f"   Biểu đồ {key} ({t}): không có giá {start:%d/%m/%Y}→{end:%d/%m/%Y} → thẻ số liệu")
            continue
        chg = (pts[-1] / pts[0] - 1) * 100
        if claim is not None and (chg * claim < 0 or abs(chg - claim) > max(15, 0.35 * abs(claim))):
            log(f"   Biểu đồ {key} ({t}): giá thật {chg:+.0f}% khác lời đọc {claim:+.0f}% → thẻ số liệu")
            continue
        data["charts"][key] = {"ticker": t, "series": pts[::max(1, len(pts) // 120)], "days": int(days),
                               "start": start.strftime("%d/%m/%Y"), "end": end.strftime("%d/%m/%Y")}
        log(f"   Biểu đồ {key} ({t}): {start:%d/%m/%Y}→{end:%d/%m/%Y}, {chg:+.0f}% (khớp lời đọc)")


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
            plan["image_scores"] = {k: float(v) for k, v in sc.items() if isinstance(v, (int, float, str)) and str(v).replace(".", "", 1).isdigit()}
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
    cfg["podcast"]["voice"] = name
    cfg["podcast"]["voice_style"] = ""
    gem = P.Gemini(key or os.getenv("GEMINI_API_KEY", ""))
    import time
    # mỗi đoạn đọc riêng 1 lượt → không bao giờ bị cắt giữa câu khi chia lại audio
    for i, t in enumerate(parts):
        if i:
            time.sleep(int(cfg["podcast"].get("tts_pause_seconds", 25)))
        V.pcm_to_wav(V.tts_once(gem, cfg, t), outdir / f"{i:02d}.wav")
    return True


PROGRESS = None  # hàm báo tiến độ (pct, ghi chú) do insight.py gắn vào


def _pg(p, note):
    if PROGRESS:
        try:
            PROGRESS(p, note)
        except Exception:
            pass


def prepare(posts_or_links, out: Path, voices: list[str] | None = None, release: bool = False,
            notes: list[str] | None = None) -> Path:
    """Viết kịch bản + lấy dữ liệu/ảnh + đọc giọng. Giọng: thử lần lượt theo danh sách (Gemini Ludo trước,
    hết lượt thì VieNeu Hải Đăng), cả video luôn dùng MỘT giọng."""
    cfg = V.load_cfg()
    ic = cfg.get("insight") or {}
    voices = voices or [ic.get("voice_primary", "gemini:Ludo"), ic.get("voice_fallback", "vieneu:Hải Đăng")]
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
    plan = V.llm_json(gem, cfg, system, prompt)
    plan = P.nodash(plan)  # triệt gạch ngang dài ngay từ kịch bản
    plan = vi_terms(plan)  # thuật ngữ không thuộc crypto (PTSD...) → tiếng Việt
    _pg(25, "đã viết xong kịch bản, đang lấy dữ liệu + ảnh")
    plan["sections"] = [s for s in plan.get("sections", []) if s.get("narration")][: int(ic.get("max_sections", 6))]
    plan["posts"] = posts
    # chữ hiện trên hình phải khớp lời đọc: vòng lặp mở nằm trong intro, câu hỏi kéo bình luận nằm trong outro
    _n = lambda s: re.sub(r"\W+", " ", (s or "").lower()).strip()
    if plan.get("open_loop") and _n(plan["open_loop"]) not in _n(plan.get("intro")):
        plan["intro"] = (plan.get("intro", "").rstrip() + " " + plan["open_loop"].strip()).strip()
    plan["actions"] = [a for a in (plan.get("actions") or []) if isinstance(a, str) and a.strip()][:3]
    if plan.get("question") and _n(plan["question"]) not in _n(plan.get("outro")):
        plan["outro"] = (plan.get("outro", "").rstrip() + " " + plan["question"].strip()).strip()
    log("③ Dữ liệu thị trường + ảnh (AI lọc ảnh lạc đề)")
    md = market_data(lab)
    coin_data(lab, plan, md)
    (lab / "data.json").write_text(json.dumps(md, ensure_ascii=False), encoding="utf-8")
    save_images(lab, plan, gem, cfg)
    parts = [("hook", plan.get("hook", "")), ("intro", plan.get("intro", ""))]
    parts += [(f"s{k}", s["narration"]) for k, s in enumerate(plan["sections"])]
    parts += [("outro", plan.get("outro", ""))]
    parts = [(k, P.sanitize_script(t)) for k, t in parts if t and t.strip()]
    plan["parts"] = [{"key": k, "text": t} for k, t in parts]
    plan["shorts"] = [i for i in plan.get("shorts", []) if isinstance(i, int) and 0 <= i < len(plan["sections"])][
                     : int(ic.get("shorts", 3))]
    plan["voices"] = {}
    _pg(40, "đang đọc giọng")
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
                        "--title", f"Lab nguyên liệu {tag}", "--notes", P.nodash(plan.get("title", ""))], check=True)
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
