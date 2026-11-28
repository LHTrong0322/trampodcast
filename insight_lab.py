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
      "edu": "true nếu phần này giảng một kiến thức/khái niệm quan trọng (giọng tự đọc chậm 5%), không thì false",
      "emphasis": "nhãn ≤ 4 từ nếu đây là phần hook đã hứa riêng (vd CÂU NGƯỜI TA BỎ QUA), không thì trống",
      "beats": [{{"at": "3-5 chữ CHÉP NGUYÊN từ lời đọc, hình hiện đúng lúc giọng nói cụm này",
                 "type": "bignum | versus | dots | flow | logos | race | chart | matrix | statement",
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
Ảnh bìa (Trọng 26/11, kiểu viral sạch: 1 con số làm nhân vật chính, chữ ít, câu hỏi gây tò mò, nhãn vàng nổi):
  thumb_stat = 1 con số gây sốc (vd "-$6T", "79%", "$0"); thumb_text = câu hỏi/lời hứa ≤ 24 ký tự, viết thường có dấu như câu nói,
  không IN HOA cả câu, nên kết bằng "?", không lặp y nguyên tiêu đề; thumb_tag = nhãn nổi ≤ 24 ký tự (vd "CÙNG ĐỎ", "đúng 1 thứ", "vẫn lỗ?");
  thumb_kicker = dòng nhỏ phía trên ≤ 30 ký tự (vd "Nếu bắt đầu lại từ"); thumb_points = tối đa 3 chip 1-2 từ;
  so sánh 2 phía thì điền "thumb_vs"; câu chuyện trước/sau thì điền "thumb_before" và "thumb_after" dạng {{"label", "value"}}
  (vd {{"label": "Mỗi năm bỏ vào", "value": "$10K"}} và {{"label": "Sau 30 năm", "value": "$1.6M"}}).
  Có thể chỉ định "thumb_style": stat | pill | vs | before | question.
Tiêu đề short (short_hooks) phải có con số hoặc dấu hỏi, ≤ 60 ký tự, tự đứng được một mình.
Đoạn đầu MỖI short (câu hook và câu đọc đầu tiên, tức cụm "from" của short_spans) luôn là HIGHLIGHT đắt nhất để tạo tò mò:
con số sốc, nghịch lý hoặc kết luận bất ngờ. CẤM mở bằng tên tác giả hay @handle (vd KHÔNG "Kyle gọi crypto là...",
mà "95% altcoin sẽ về 0, chỉ 1 thước đo lọc được coin sống sót"). Tên tác giả nhắc sau, nếu cần.
Gợi ý chọn data.type: nói về tâm lý thị trường → fear_greed; về altcoin vs bitcoin, dòng tiền → dominance;
về coin cụ thể → coin_chart; so sánh 2-4 thứ có số → stat_compare (điền items); danh sách việc cần làm /
tiêu chí đánh giá → checklist (điền items, value để trống); bức tranh toàn thị trường → market_heatmap.
TUYỆT ĐỐI KHÔNG dùng dấu gạch ngang dài (em dash, en dash) ở bất kỳ đâu; cần ngắt ý thì dùng dấu phẩy hoặc dấu chấm.
CẤM HOÀN TOÀN (chủ kênh yêu cầu): KHÔNG nhắc tới ENA / Ethena và chuyện "ENA tăng 95% trong 14 ngày nhờ một thay đổi
duy nhất" ở bất kỳ đâu: không trong hook, intro, lời đọc, tiêu đề, bullets, quote, key_stat, hook_stat, thumb_text,
thumb_stat, short_hooks; không làm phần nào về Ethena; không dùng con số 95% hay mốc 14 ngày. Hãy khai thác các ý khác
của bài (thị trường lemon/coin rác, FDV, PMF, token alignment, Hyperliquid, tâm lý nhà đầu tư, cách chọn tài sản...)."""

# Trọng 23/11: TIN NÓNG dạng short (news_flash.py). Cùng bộ khung Smart Penguin Insights, nhưng là 1 video ngắn 9:16.
NEWS_PROMPT = """
CHẾ ĐỘ TIN NÓNG (ghi đè các yêu cầu độ dài ở trên): đây KHÔNG phải tập insight dài mà là 1 VIDEO NGẮN 9:16 về MỘT tin
quan trọng vừa xảy ra, đăng TikTok/Shorts/Reels. Viết ĐÚNG 1 phần (sections có 1 phần tử), "shorts": [0].
- short_hooks {{"0": "..."}}: câu mở ≤ 12 từ, là HIGHLIGHT của tin, CẤM mở bằng tên tác giả, có con số hoặc điều bất ngờ của tin (vd "BlackRock vừa gom thêm $500M BTC trong 1 ngày").
- narration của phần: 95-130 từ (khoảng 35-45 giây), câu ngắn, nhịp nhanh, theo khuôn: chuyện gì vừa xảy ra (ai, bao nhiêu, khi nào)
  → vì sao quan trọng (bối cảnh 1-2 câu, giải thích nửa câu nếu tên lạ) → ảnh hưởng tới nhà đầu tư/ giá coin liên quan
  → 1 câu kết hỏi ý kiến người xem để bình luận. KHÔNG dự đoán giá, KHÔNG hô mua bán, KHÔNG phóng đại quá mức tin gốc.
LUẬT GIÁ TRỊ (Trọng chốt 27/11, áp dụng cho MỌI câu lời đọc, MỌI thẻ hình, ảnh, chữ trên màn hình, kể cả câu mở và câu kết):
từng câu, từng hình có xứng với thời gian người xem bỏ ra không? Mỗi câu phải mang lại 1 điều MỚI: thông tin mới, con số mới,
bối cảnh, nguyên nhân, hệ quả, hoặc việc người xem làm được. KHÔNG ĐÁNG (phải đập đi viết lại, không được giữ):
nhắc lại con số hay ý đã nói (vd đã nói "gần 5 tỷ" thì không nói lại "4 tỷ 940 triệu"); câu đệm, câu chuyển rỗng, câu chỉ để kéo dài;
câu hỏi tu từ không được trả lời; thẻ hình chỉ nhắc lại chữ của phụ đề hoặc tiêu đề mà không thêm số liệu hay hình mới;
ảnh minh hoạ chung chung không liên quan nội dung.
CÁCH LÀM ĐÚNG (gỡ xung đột với luật "chữ trên hình khớp lời đọc"): mỗi câu lời đọc mang 1 con số hoặc 1 so sánh, và thẻ hình VẼ chính con số đó (số to, so sánh 2 bên, biểu đồ, logo), không chép lại câu chữ. Câu không có gì để vẽ thì viết lại câu cho có số, hoặc bỏ câu.
- Nêu nguồn tin bằng tên báo/kênh trong lời đọc nếu cần (vd "theo CoinDesk"), KHÔNG nhắc @handle nào; số liệu CHỈ lấy từ tin nguồn, không bịa.
- beats: 9-13 beats, cứ khoảng 3 đến 4 giây đổi một hình; ưu tiên bignum có số thật của tin, logo dự án/coin, chart giá liên quan.
  Thêm 2-3 beat {{"type": "photo", "query": "2-4 từ tiếng Anh chung, KHÔNG tên người (vd 'computer chip closeup', 'stock market red screen', 'data center servers')", "label": "chú thích ngắn ≤ 40 ký tự"}}.
  Thẻ versus: nhãn 2 bên ngắn (≤ 16 ký tự, cùng 1 dòng), thêm "note" nhỏ dưới số (vd "+103% so với cùng kỳ") nếu nguồn có số đó.
  Mỗi con số trong lời đọc có đúng 1 thẻ hiện cùng lúc; thẻ chữ không khẳng định mạnh hơn nguồn.
- short_title: tiêu đề hiện trên đầu short, ≤ 44 ký tự (tối đa 2 dòng), có con số.
- hook, intro, outro giữ thật ngắn (intro 1 câu, outro 1 câu "không phải lời khuyên đầu tư"); chúng chỉ dùng cho bản 16:9 phụ.
- title ≤ 70 ký tự kiểu tin nóng, có con số; thumb_text ≤ 24 ký tự (viết thường có dấu, nên là câu hỏi); thumb_stat là con số sốc nhất; thumb_tag "TIN NÓNG".
"""

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


STOCKS = {"NVDA": "Nvidia", "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Google", "AMZN": "Amazon", "META": "Meta", "TSLA": "Tesla",
          "AMD": "AMD", "AVGO": "Broadcom", "TSM": "TSMC", "COIN": "Coinbase", "MSTR": "Strategy", "HOOD": "Robinhood", "CRCL": "Circle",
          "ORCL": "Oracle", "PLTR": "Palantir", "INTC": "Intel", "NFLX": "Netflix"}
INDEXES = {"VIX", "SPX", "SPY", "QQQ", "NDX", "DXY", "DJI", "S&P"}
INDEX_NAMES = {"SPX": "S&P 500", "S&P": "S&P 500", "NDX": "Nasdaq 100", "DJI": "Dow Jones", "VIX": "VIX", "DXY": "DXY"}
NAME_TICKER = {"nvidia": "NVDA", "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL", "amazon": "AMZN", "tesla": "TSLA",
               "coinbase": "COIN", "microstrategy": "MSTR", "robinhood": "HOOD", "broadcom": "AVGO", "oracle": "ORCL", "palantir": "PLTR",
               "uniswap": "UNI", "hyperliquid": "HYPE", "aave": "AAVE", "ethena": "ENA", "solana": "SOL", "bitcoin": "BTC",
               "ethereum": "ETH", "chainlink": "LINK", "pendle": "PENDLE", "virtuals": "VIRTUAL", "arbitrum": "ARB", "celestia": "TIA", "sui": "SUI"}


def _days(v) -> int:
    """Số ngày lấy giá: số nguyên, hoặc "ytd" = từ 1/1 năm nay."""
    if str(v).lower() == "ytd":
        now = datetime.now()
        return max(30, (now - datetime(now.year, 1, 1)).days)
    try:
        return max(7, min(365, int(v)))
    except Exception:
        return 30


def live_numbers(plan: dict, data: dict):
    """Thay số giá trong kịch bản bằng số thật lúc dựng, để lời đọc, biểu đồ, ảnh bìa và short khớp nhau.
    {YTD:HYPE} = % thay đổi từ 1/1 (trị tuyệt đối, làm tròn 5, chữ "tăng/giảm" do kịch bản viết sẵn),
    {YTDS:HYPE} = có dấu (+135 / -40), {DATE} = ngày dựng dd/mm. Đổi dấu so với kịch bản thì báo trong log."""
    coins = data.get("coins") or {}
    now = datetime.now()
    jan1 = (now - datetime(now.year, 1, 1)).days

    def ytd(t):
        c = coins.get(t.upper()) or {}
        ser, days = c.get("series") or [], c.get("days") or 30
        if len(ser) < 5 or days < jan1 - 3:
            return None
        k = max(2, round(len(ser) * jan1 / days))
        pct = (ser[-1] / ser[-k] - 1) * 100
        return pct

    def fill(x):
        if isinstance(x, dict):
            return {k: fill(v) for k, v in x.items()}
        if isinstance(x, list):
            return [fill(v) for v in x]
        if not isinstance(x, str) or "{" not in x:
            return x
        x = x.replace("{DATE}", datetime.now(P.VN_TZ).strftime("%d/%m"))   # ngày theo giờ Việt Nam

        def rep(m):
            v = ytd(m.group(2))
            if v is None:
                raise RuntimeError(f"Không có giá {m.group(2)} để điền {m.group(0)}, dừng dựng (không xuất video có '?')")
            before = m.string[max(0, m.start() - 25):m.start()].lower()
            if m.group(1) == "YTD" and (("giảm" in before and v > 0) or ("tăng" in before and v < 0)):
                raise RuntimeError(f"Giá {m.group(2)} từ 1/1 là {v:+.0f}% nhưng kịch bản viết '{before.strip()}', cần sửa kịch bản trước khi dựng")
            r = int(5 * round(abs(v) / 5)) if abs(v) >= 10 else round(abs(v))
            return (("+" if v >= 0 else "-") + str(r)) if m.group(1) == "YTDS" else str(r)
        return re.sub(r"\{(YTDS?):([A-Z0-9]+)(?:\|([^}]*))?\}", rep, x)
    plan = fill(plan)
    for t, c in coins.items():
        v = ytd(t)
        if v is not None:
            log(f"   Giá thật {t} từ 1/1: {v:+.0f}%")
    return plan


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
        # Trọng 23/11: lời đọc nói "từ 1957 tăng 10%/năm" mà biểu đồ chỉ 1 năm là lệch. Cổ phiếu/chỉ số được vẽ nhiều năm ("years": 30)
        if b.get("type") == "chart" and b.get("ticker") and b.get("years"):
            want[str(b["ticker"]).lstrip("$").upper()] = max(400, min(100, int(b["years"])) * 365)
        for x in [b, b.get("left") or {}, b.get("right") or {}] + list(b.get("items") or []) + list(b.get("cols") or []):   # logo coin trong nhịp hình
            if isinstance(x, dict) and x.get("logo"):
                tick.append(str(x["logo"]).lstrip("$").upper())
        if b.get("type") == "chart" and b.get("ticker"):
            tick.append(str(b["ticker"]).lstrip("$").upper())
        for t in (b.get("tickers") or []) if b.get("type") == "race" else []:   # biểu đồ đua % (Trọng 22/11)
            t = str(t).lstrip("$").upper()
            tick.append(t)
            want[t] = max(want.get(t, 30), _days(b.get("days")))
    data.setdefault("coins", {})
    # Trọng 22/11: bản 0427 bị CoinGecko chặn vì gọi quá nhiều (thêm logo cho mọi tên dự án) → hook ra "?%", biểu đồ trống.
    # Giờ: coin CẦN SỐ (biểu đồ, so sánh, ô điền {YTD}) lấy trước, gọi lại khi bị chặn; coin chỉ cần logo thì không lấy giá;
    # thiếu số cần thiết thì DỪNG dựng, không bao giờ xuất video thiếu dữ liệu.
    # cổ phiếu/chỉ số (NVDA, SPY, VIX...) không có trên CoinGecko → lấy giá từ Yahoo Finance/Stooq (Trọng 22/11: cổ phiếu dùng chart cũng được).
    # Lấy không được thì bỏ hình đó (ghi log) thay vì dừng cả bản dựng.
    stock_need = set()
    for sec in [plan] + list(plan.get("sections", [])):
        for b in sec.get("hook_beats" if sec is plan else "beats") or []:
            tks = [b.get("ticker")] if b.get("type") == "chart" else (b.get("tickers") or []) if b.get("type") == "race" else []
            stock_need |= {str(x).lstrip("$").upper() for x in tks if x and str(x).lstrip("$").upper() in (set(STOCKS) | INDEXES | set(COMMOD))}
    stock_need |= {t for t in re.findall(r"\{YTDS?:([A-Z0-9&^.]+)", json.dumps(plan, ensure_ascii=False)) if t in set(STOCKS) | INDEXES}
    for t in sorted(stock_need):
        ser = _stock_series(t, want.get(t, 30))
        if ser:
            ent = data["coins"].setdefault(t, {"name": STOCKS.get(t) or INDEX_NAMES.get(t) or COMMOD.get(t, t), "logo": None, "color": "#4F5BD5", "stock": True,
                                               "index": t in INDEXES})   # chỉ số: hiện điểm, không hiện $ (video index fund 23/11)
            ent.update({"price": ser[-1], "series": ser[:: max(1, len(ser) // 120)], "days": want.get(t, 30)})
            log(f"   Giá cổ phiếu/chỉ số {t}: {len(ser)} điểm")
    noprice = {t for t in set(STOCKS) | INDEXES | set(COMMOD) if not (data["coins"].get(t) or {}).get("series")}
    for sec in [plan] + list(plan.get("sections", [])):
        key = "hook_beats" if sec is plan else "beats"
        keep = []
        for b in sec.get(key) or []:
            tks = {str(x).lstrip("$").upper() for x in ([b.get("ticker")] if b.get("type") == "chart" else b.get("tickers") or [] if b.get("type") == "race" else []) if x}
            if tks & noprice:
                log(f"   ! bỏ hình {b.get('type')} '{b.get('at')}': {', '.join(tks & noprice)} là cổ phiếu/chỉ số, không có giá CoinGecko")
                continue
            keep.append(b)
        if sec.get(key) is not None:
            sec[key] = keep
    for t in list(want):
        if t in noprice:
            want.pop(t)
    raw = json.dumps(plan, ensure_ascii=False)
    need = (set(want) | set(re.findall(r"\{YTDS?:([A-Z0-9]+)", raw))) - noprice
    for x in plan.get("thumb_vs") or []:
        if x.get("logo"):
            need.add(str(x["logo"]).lstrip("$").upper())
    for s_ in plan.get("sections", []):
        d_ = s_.get("data") or {}
        if d_.get("type") == "coin_chart":
            need |= {str(t).lstrip("$").upper() for t in d_.get("tickers") or []}
    order = [t for t in dict.fromkeys(list(need) + tick) if re.fullmatch(r"[A-Z0-9]{2,10}", t) and (t != "ENA" or plan.get("allow_ena"))]
    for t in order:
        if t in INDEXES:   # chỉ số (VIX, S&P...) không có logo coin: không tra CoinGecko (bản AI bubble bị gắn nhầm logo token tên VIX)
            own = Path(__file__).parent / "assets" / "logos" / f"{'SPX' if t == 'S&P' else t}.png"   # logo Trọng gửi (S&P 500, 23/11)
            if own.exists() and t in data["coins"]:
                (lab / "logos").mkdir(exist_ok=True)
                (lab / "logos" / f"{t}.png").write_bytes(own.read_bytes())
                data["coins"][t].update({"logo": f"logos/{t}.png", "color": "#D6001C"})
                log(f"   Logo chỉ số {t} (assets/logos)")
            continue
        if t in STOCKS:    # cổ phiếu (Trọng 22/11: nhắc NVDA phải có logo): lấy logo công ty, không tra CoinGecko
            lp = lab / "logos" / f"{t}.png"
            lp.parent.mkdir(exist_ok=True)
            for url in (f"https://financialmodelingprep.com/image-stock/{t}.png", f"https://assets.parqet.com/logos/symbol/{t}?format=png"):
                try:
                    r = requests.get(url, timeout=20)
                    if r.ok and r.headers.get("content-type", "").startswith("image") and len(r.content) > 400:
                        lp.write_bytes(r.content)
                        break
                except Exception:
                    pass
            if lp.exists():
                data["coins"].setdefault(t, {"name": STOCKS[t], "stock": True})
                data["coins"][t].update({"logo": f"logos/{t}.png", "color": brand_color(lp)})
                log(f"   Logo cổ phiếu {t}")
            else:
                log(f"   ! không lấy được logo cổ phiếu {t}")
            continue
        info = _cg_search(t)
        if not info:
            log(f"   ! không tìm thấy coin {t}")
            continue
        (lab / "logos").mkdir(exist_ok=True)
        if info.get("large") and not (lab / "logos" / f"{t}.png").exists():
            try:
                (lab / "logos" / f"{t}.png").write_bytes(requests.get(info["large"], timeout=20).content)
            except Exception as ex:
                log(f"   ! logo {t} lỗi: {ex}")
        lg = f"logos/{t}.png" if (lab / "logos" / f"{t}.png").exists() else None
        entry = {"name": info.get("name", t), "logo": lg, "color": BRAND_OVERRIDE.get(t) or (brand_color(lab / "logos" / f"{t}.png") if lg else "#4F5BD5")}
        if t in need or len([c for c in data["coins"].values() if c.get("series")]) < 4:
            ch = _cg(f"https://api.coingecko.com/api/v3/coins/{info['id']}/market_chart",
                     {"vs_currency": "usd", "days": want.get(t, 30)})
            pts = [p[1] for p in (ch or {}).get("prices", [])]
            if len(pts) >= 10:
                entry.update({"price": pts[-1], "series": pts[::max(1, len(pts) // 120)], "days": want.get(t, 30)})
                log(f"   Coin {t}: {len(pts)} điểm giá")
            else:
                log(f"   ! giá {t} không lấy được")
        data["coins"][t] = entry
    miss = sorted(t for t in need if not (data["coins"].get(t) or {}).get("series"))
    spoken = set(re.findall(r"\{YTDS?:([A-Z0-9&^.=]+)", json.dumps(plan, ensure_ascii=False)))
    drop = set(miss) - spoken
    if drop:   # biểu đồ/so sánh thiếu giá: bỏ hình đó, không dừng cả bản dựng (con số đọc trong lời thì vẫn bắt buộc)
        for sec in [plan] + list(plan.get("sections", [])):
            key = "hook_beats" if sec is plan else "beats"
            if sec.get(key) is None:
                continue
            keep = []
            for b in sec[key]:
                tks = {str(x).lstrip("$").upper() for x in ([b.get("ticker")] if b.get("type") == "chart" else b.get("tickers") or [] if b.get("type") == "race" else []) if x}
                if tks & drop:
                    log(f"   ! bỏ hình {b.get('type')} '{b.get('at')}': không lấy được giá {', '.join(tks & drop)}")
                    continue
                keep.append(b)
            sec[key] = keep
        miss = sorted(set(miss) & spoken)
    if miss:
        raise RuntimeError(f"Thiếu giá thật của {', '.join(miss)} (CoinGecko không trả), dừng dựng để không xuất video thiếu số liệu")


YAHOO = {"S&P": "^GSPC", "SPX": "^GSPC", "VIX": "^VIX", "NDX": "^NDX", "DXY": "DX-Y.NYB", "DJI": "^DJI"}
# hàng hoá (giá dầu, vàng...): Yahoo có, CoinGecko không (lỗi 23/11: bot thêm biểu đồ CL=F làm dừng bản dựng)
COMMOD = {"USO": "Quỹ dầu USO", "UNG": "Quỹ khí đốt UNG", "GLD": "Quỹ vàng GLD", "SLV": "Quỹ bạc SLV", "CL=F": "Dầu WTI", "BZ=F": "Dầu Brent", "GC=F": "Vàng", "SI=F": "Bạc", "OIL": "Dầu WTI", "WTI": "Dầu WTI", "GOLD": "Vàng", "XAU": "Vàng"}
YAHOO.update({"OIL": "CL=F", "WTI": "CL=F", "GOLD": "GC=F", "XAU": "GC=F"})


def _btc_weekly() -> list:
    """Giá đóng cửa BTC theo TUẦN, càng dài càng tốt (cần >350 tuần để tính 350WMA): [(ngày 'YYYY-MM-DD', giá)].
    Log 23/11: Yahoo range=max interval=1wk chỉ trả 147 điểm, Stooq và CryptoCompare trả 0 trên máy GitHub.
    Giờ: Yahoo giá NGÀY từ 2014 rồi gộp tuần, dự phòng Binance (data-api.binance.vision, không chặn theo vùng), Kraken."""
    import time as _t

    def weekly(rows):   # gộp giá ngày thành giá đóng cửa mỗi 7 ngày, mốc cuối là ngày mới nhất
        return rows[::-7][::-1] if len(rows) > 2600 else rows
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD",
                         params={"period1": 1410000000, "period2": int(_t.time()), "interval": "1d"},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=40)
        res = ((r.json().get("chart") or {}).get("result") or [{}])[0]
        ts = res.get("timestamp") or []
        cl = (((res.get("indicators") or {}).get("quote") or [{}])[0].get("close")) or []
        out = weekly([(datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"), c) for t, c in zip(ts, cl) if c])
        if len(out) > 400:
            return out
        log(f"   ! Yahoo BTC chỉ có {len(out)} điểm tuần")
    except Exception as ex:
        log(f"   ! Yahoo BTC: {ex}")
    try:
        js = requests.get("https://data-api.binance.vision/api/v3/klines",
                          params={"symbol": "BTCUSDT", "interval": "1w", "limit": 1000}, timeout=30).json()
        out = [(datetime.utcfromtimestamp(k[0] / 1000).strftime("%Y-%m-%d"), float(k[4])) for k in js if isinstance(k, list)]
        if len(out) > 400:
            return out
        log(f"   ! Binance BTC tuần chỉ có {len(out)} điểm")
    except Exception as ex:
        log(f"   ! Binance BTC tuần: {ex}")
    try:
        js = requests.get("https://api.kraken.com/0/public/OHLC", params={"pair": "XBTUSD", "interval": 10080}, timeout=30).json()
        rows = next(iter((js.get("result") or {}).values()), [])
        out = [(datetime.utcfromtimestamp(k[0]).strftime("%Y-%m-%d"), float(k[4])) for k in rows if isinstance(k, list)]
        if len(out) > 400:
            return out
        log(f"   ! Kraken BTC tuần chỉ có {len(out)} điểm")
    except Exception as ex:
        log(f"   ! Kraken BTC tuần: {ex}")
    return []


def _btc_daily() -> list:
    """Trọng 28/11: Dow khung D. Giá đóng cửa BTC theo NGÀY: Yahoo, dự phòng Binance 1d (1000 nến gần nhất)."""
    import time as _t
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD",
                         params={"period1": 1577836800, "period2": int(_t.time()), "interval": "1d"},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=40)
        res = ((r.json().get("chart") or {}).get("result") or [{}])[0]
        ts = res.get("timestamp") or []
        cl = (((res.get("indicators") or {}).get("quote") or [{}])[0].get("close")) or []
        out = [(datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"), c) for t, c in zip(ts, cl) if c]
        if len(out) > 400:
            return out
        log(f"   ! Yahoo BTC ngày chỉ có {len(out)} điểm")
    except Exception as ex:
        log(f"   ! Yahoo BTC ngày: {ex}")
    try:
        js = requests.get("https://data-api.binance.vision/api/v3/klines",
                          params={"symbol": "BTCUSDT", "interval": "1d", "limit": 1000}, timeout=30).json()
        out = [(datetime.utcfromtimestamp(k[0] / 1000).strftime("%Y-%m-%d"), float(k[4])) for k in js if isinstance(k, list)]
        if len(out) > 200:
            return out[:-1]   # bỏ nến ngày đang chạy
    except Exception as ex:
        log(f"   ! Binance BTC ngày: {ex}")
    return []


def _gtrends(keyword: str, since: str = "2019-01-01") -> list:
    """Google Trends (toàn cầu) cho 1 từ khoá: [(ngày 'YYYY-MM-DD', điểm 0-100)], theo tuần/tháng tuỳ độ dài.
    Gọi thẳng API của trang trends.google.com (cách pytrends làm), thử lại khi bị 429. Lỗi thì trả []."""
    import time as _t
    sess = requests.Session()
    sess.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    end = datetime.utcnow().strftime("%Y-%m-%d")
    for attempt in range(4):
        try:
            sess.get("https://trends.google.com/trends/explore", params={"q": keyword}, timeout=20)
            req = {"comparisonItem": [{"keyword": keyword, "geo": "", "time": f"{since} {end}"}], "category": 0, "property": ""}
            r = sess.get("https://trends.google.com/trends/api/explore",
                         params={"hl": "en-US", "tz": 0, "req": json.dumps(req)}, timeout=20)
            if r.status_code == 429:
                raise RuntimeError("429")
            w = next(x for x in json.loads(r.text[r.text.index("{"):])["widgets"] if x.get("id") == "TIMESERIES")
            r = sess.get("https://trends.google.com/trends/api/widgetdata/multiline",
                         params={"hl": "en-US", "tz": 0, "req": json.dumps(w["request"]), "token": w["token"]}, timeout=20)
            if r.status_code == 429:
                raise RuntimeError("429")
            rows = json.loads(r.text[r.text.index("{"):])["default"]["timelineData"]
            out = [(datetime.utcfromtimestamp(int(x["time"])).strftime("%Y-%m-%d"), int(x["value"][0])) for x in rows if x.get("value")]
            if len(out) > 20:
                return out
        except Exception as ex:
            log(f"   ! Google Trends '{keyword}' lần {attempt + 1}: {ex}")
        _t.sleep(6 * (attempt + 1))
    return []


def trend_data(plan: dict, data: dict):
    """Trọng 24/11: câu "Google Trends cho Bitcoin thấp nhất từ 2020" phải có biểu đồ Google Trends thật (beat type "trend",
    "keyword"). Không lấy được dữ liệu thì bỏ beat (ghi log), thẻ số bên cạnh vẫn còn."""
    secs = [("hook_beats", plan)] + [("beats", s) for s in plan.get("sections", [])]
    kws = {b.get("keyword") or "Bitcoin" for k, s in secs for b in (s.get(k) or []) if b.get("type") == "trend"}
    if not kws:
        return
    data["trends"] = {}
    for kw in kws:
        rows = _gtrends(kw)
        if rows:
            data["trends"][kw] = {"dates": [d for d, _ in rows], "values": [v for _, v in rows]}
            log(f"   Google Trends '{kw}': {len(rows)} điểm, hiện tại {rows[-1][1]}, thấp nhất từ 2020: "
                f"{min(v for d, v in rows if d >= '2020')}")
    for k, s in secs:
        if s.get(k):
            keep = [b for b in s[k] if b.get("type") != "trend" or (b.get("keyword") or "Bitcoin") in data["trends"]]
            if len(keep) < len(s[k]):
                log("   ! bỏ biểu đồ Google Trends: không lấy được dữ liệu")
            s[k] = keep


def wma_data(plan: dict, data: dict):
    """Trọng 23/11 (video 100y): biểu đồ giá BTC theo tuần + đường trung bình 200 tuần và 350 tuần (beat type "wma").
    Số trên hình là dữ liệu THẬT tính từ giá tuần. Không lấy được giá thì bỏ beat đó (ghi log), không dừng cả bản dựng."""
    secs = [("hook_beats", plan)] + [("beats", s) for s in plan.get("sections", [])]
    if not any(b.get("type") == "wma" for k, s in secs for b in (s.get(k) or [])):
        return
    rows = _btc_weekly()
    if len(rows) > 400:
        px = [p for _, p in rows]

        def ma(n):
            return [None if i + 1 < n else sum(px[i + 1 - n: i + 1]) / n for i in range(len(px))]
        m200, m350 = ma(200), ma(350)
        keep = min(len(px), 290)   # khoảng 5,5 năm gần nhất: thấy rõ đáy 2022 và hiện tại
        win = slice(len(px) - keep, len(px))
        data["wma"] = {"dates": [d for d, _ in rows][win], "price": px[win], "ma200": m200[win], "ma350": m350[win],
                       "now": px[-1], "now200": m200[-1], "now350": m350[-1]}
        log(f"   Giá BTC tuần: {len(px)} điểm, giá {px[-1]:,.0f}, 200WMA {m200[-1]:,.0f}, 350WMA {m350[-1]:,.0f} "
            f"({(px[-1] / m200[-1] - 1) * 100:+.1f}% so với 200WMA)")
        return
    for k, s in secs:
        if s.get(k):
            before = len(s[k])
            s[k] = [b for b in s[k] if b.get("type") != "wma"]
            if len(s[k]) < before:
                log("   ! bỏ biểu đồ 200WMA: không lấy được giá BTC theo tuần")


def dow_key(b: dict) -> str:
    """Khoá dữ liệu của 1 beat dow, khớp với beats.tsx: "from:k" (khung tuần) hoặc "from:k:D[:to]" (khung ngày)."""
    tf = str(b.get("tf") or "W").upper()
    if b.get("last"):   # Trọng 28/11: chart đỉnh đáy phải ZOOM gần (vài tháng gần nhất) cho người xem hiểu
        return f"last{int(b['last'])}:{int(b.get('k') or 4)}:{tf}"
    k = f"{b.get('from') or '2018'}:{int(b.get('k') or 4)}"
    return k if tf != "D" else k + ":D" + (f":{b['to']}" if b.get("to") else "")


def dow_data(plan: dict, data: dict):
    """Trọng 27/11: chart lý thuyết Dow trên giá BTC thật (beat type "dow": đỉnh đáy HH, HL, LH, LL).
    Beat: {"type": "dow", "from": "2018" hoặc "2025-06", "k": 4, "tf": "W" | "D", "to": "2025-10" (tuỳ chọn), "last": 150 (tuỳ chọn:
    chỉ lấy 150 nến gần nhất)}. Trọng 28/11: chart đỉnh đáy phải zoom gần, vài tháng, k nhỏ (4 đến 6), để thấy rõ 3 đến 6 đỉnh đáy.
    Trọng 28/11: bỏ backtest; thêm khung D (giá ngày). Không lấy được giá thì bỏ beat (ghi log)."""
    import dow_lab as DL
    secs = [("hook_beats", plan), ("intro_beats", plan)] + [("beats", s) for s in plan.get("sections", [])]
    beats = [b for k, s in secs for b in (s.get(k) or []) if b.get("type") == "dow"]
    if not beats:
        return
    rows = {"W": None, "D": None}
    data["dow"] = {}
    drop = set()
    for b in beats:
        tf = "D" if str(b.get("tf") or "W").upper() == "D" else "W"
        if rows[tf] is None:
            rows[tf] = _btc_daily() if tf == "D" else _btc_weekly()
        r = rows[tf]
        if len(r) < 200:
            drop.add(id(b))
            log(f"   ! bỏ chart Dow khung {tf}: không lấy được giá BTC")
            continue
        key = dow_key(b)
        if key in data["dow"]:
            continue
        frm, to, k = str(b.get("from") or "2018"), str(b.get("to") or "9999"), int(b.get("k") or 4)
        keep = [(i, d, p) for i, (d, p) in enumerate(r) if d[:len(frm)] >= frm and d[:len(to)] <= to]
        if b.get("last"):
            keep = [(i, d, p) for i, (d, p) in enumerate(r)][-int(b["last"]):]
        if len(keep) < 30:
            drop.add(id(b))
            continue
        lo, hi = keep[0][0], keep[-1][0]
        px = [p for _, p in r[:hi + 1]]
        sw = [{**x, "i": x["i"] - lo} for x in DL.label_swings(DL.pivots(px, k)) if x["i"] >= lo]
        data["dow"][key] = {"dates": [d for _, d, _ in keep], "price": [p for _, _, p in keep], "swings": sw,
                            "states": DL.states(px, k)[lo:], "tf": tf}
        log(f"   Dow BTC khung {tf} {keep[0][1]} tới {keep[-1][1]} (k={k}): {len(sw)} đỉnh đáy")
    if drop:
        for k, s in secs:
            if s.get(k):
                s[k] = [b for b in s[k] if id(b) not in drop]


def _stock_series(t: str, days: int) -> list:
    """Giá đóng cửa ngày của cổ phiếu/chỉ số: Yahoo Finance, dự phòng Stooq. Trả [] nếu không lấy được."""
    sym = YAHOO.get(t, t)
    rng = "1y" if days > 185 else "6mo" if days > 95 else "3mo" if days > 35 else "1mo"
    step, per = "1d", 5 / 7
    if days > 400:   # nhiều năm: lấy giá tháng (Trọng 23/11, biểu đồ S&P 500 dài hạn)
        rng, step, per = ("max" if days > 7300 else "10y" if days > 1830 else "5y"), "1mo", 1 / 30.4
    try:
        r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}", params={"range": rng, "interval": step},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        res = (r.json().get("chart") or {}).get("result") or []
        if res and days > 400:
            # Lỗi 23/11: range=max của Yahoo trả giá QUÝ, cắt theo số điểm ra 42 năm mà biểu đồ ghi "30 năm" (+3714%).
            # Cắt theo NGÀY THẬT trong timestamp để số năm và % tăng đúng với nhãn.
            import time as _t
            ts = res[0].get("timestamp") or []
            cl = ((res[0].get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
            since = _t.time() - days * 86400
            closes = [c for t_, c in zip(ts, cl) if c and t_ >= since]
            if len(closes) >= 10:
                return closes
        closes = [x for x in ((res[0].get("indicators") or {}).get("quote") or [{}])[0].get("close") or [] if x] if res else []
        if len(closes) >= 10 and days <= 400:
            return closes[-max(10, int(days * per)):]
    except Exception as ex:
        log(f"   ! Yahoo {t}: {ex}")
    try:
        st = {"^GSPC": "^spx", "^VIX": "^vix", "^NDX": "^ndx"}.get(sym, sym.lower() + ".us")
        txt = requests.get("https://stooq.com/q/d/l/", params={"s": st, "i": "d"}, timeout=30).text
        closes = [float(l.split(",")[4]) for l in txt.strip().splitlines()[1:] if l.count(",") >= 4]
        if days > 400:
            closes = closes[-int(days * 5 / 7):][::21]
            return closes if len(closes) >= 10 else []
        if len(closes) >= 10:
            return closes[-max(10, int(days * 5 / 7)):]
    except Exception as ex:
        log(f"   ! Stooq {t}: {ex}")
    return []


def _cg(url: str, params: dict | None = None):
    """Gọi CoinGecko, bị chặn (429) hay lỗi mạng thì đợi rồi gọi lại, tối đa 5 lần."""
    import time
    for i in range(5):
        try:
            time.sleep(2.0)
            r = requests.get(url, params=params, timeout=30, headers={"User-Agent": "SmartPenguinInsights/1.0"})
            if r.status_code == 200:
                return r.json()
            log(f"   CoinGecko {r.status_code}, đợi rồi thử lại ({i + 1}/5)")
        except Exception as ex:
            log(f"   CoinGecko lỗi mạng: {ex} ({i + 1}/5)")
        time.sleep(15 * (i + 1))
    return None


_CG_INFO: dict = {}


def _cg_search(t: str):
    if t not in _CG_INFO:
        js = _cg("https://api.coingecko.com/api/v3/search", {"query": t}) or {}
        # bỏ token "cổ phiếu hoá" trùng mã cổ phiếu/ETF (lỗi 23/11: USO ra "United States Oil Fund, Robinhood Token" sai giá)
        fake = re.compile(r"tokeni[sz]ed|robinhood|xstock|ondo|backed|\bstock\b|\bfund\b|\betf\b", re.I)
        _CG_INFO[t] = next((c for c in js.get("coins", [])[:8] if c.get("symbol", "").upper() == t and c.get("market_cap_rank")
                            and not fake.search(str(c.get("name", "")))), None)
    return _CG_INFO[t]


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


# Trọng 24/11 "thêm nhiều ảnh hơn": thẻ "photo" lấy ảnh từ Pixabay, Pexels, Wikimedia, Openverse (nhiều nguồn cho đa dạng),
# nhưng KHÔNG tìm theo tên người thật: video không đưa ảnh người thật lấy từ mạng (chặn ở _PERSON_HINT và video_lint).
_PERSON_HINT = re.compile(r"\b(jensen|huang|trump|musk|powell|saylor|cz|vitalik|buterin|biden|gensler|bessent)\b", re.I)


def photo_beats(lab: Path, plan: dict):
    img = lab / "img"
    img.mkdir(parents=True, exist_ok=True)
    k = 0
    for sec in plan.get("sections", []):
        for b in sec.get("beats") or []:
            if b.get("type") != "photo" or b.get("src"):
                continue
            q = str(b.get("query") or "").strip()
            if not q or _PERSON_HINT.search(q):
                log(f"   ! bỏ ảnh '{q}': không tìm ảnh theo tên người thật")
                b.update(type="statement", text=b.get("label") or "")
                continue
            res = None
            for ori in ("landscape", "portrait"):
                res = (V.search_pixabay(q, ori) or V.search_pexels(q, ori)
                       or V.search_wikimedia(q, ori) or V.search_openverse(q, ori))
                if res:
                    break
            if not res:
                log(f"   ! không tìm được ảnh kho cho '{q}', đổi thành thẻ chữ")
                b.update(type="statement", text=b.get("label") or "")
                continue
            im, cred = res
            fn = f"photo_{k}.jpg"
            im.convert("RGB").save(img / fn, quality=90)
            b["src"] = f"img/{fn}"
            plan.setdefault("image_credits", {})[fn] = cred
            k += 1
    if k:
        log(f"   Ảnh kho cho thẻ hình: {k} ảnh")


def speak(cfg: dict, voice: str, parts: list[str], outdir: Path) -> bool:
    prov, name = voice.split(":", 1)
    outdir.mkdir(parents=True, exist_ok=True)
    cfg["podcast"]["tts_provider"] = prov
    if prov == "vieneu":
        cfg.setdefault("vieneu", {})["voice"] = name
        import voice_ab as VA   # chuẩn hoá số, tiền, S&P 500 như giọng Gemini (Trọng 23/11)
        for i, t in enumerate(parts):
            V.pcm_to_wav(V.tts_once(None, cfg, VA.speakable(t)), outdir / f"{i:02d}.wav")
        return True
    key = os.getenv("INSIGHT_GEMINI_API_KEY", "")
    if not key and os.getenv("ALLOW_MAIN_KEY") != "1":
        log(f"   ⚠️ Chưa có INSIGHT_GEMINI_API_KEY → bỏ qua giọng Gemini {name} để giữ lượt cho podcast")
        return False
    # "Ludo@kol": giọng Ludo + lời dặn phong cách (Trọng chọn mẫu N "vibe KOL crypto" 21/11)
    # Trọng chốt 15:56 23/11: giọng Ludo KOL giọng Bắc nghiêm túc (index fund v8) dùng cho MỌI video về sau.
    # Gọi "gemini:Ludo" trơn (không lời dặn) thì tự gắn @kol, tránh lặp lỗi 22/11 đọc ra giọng miền Nam.
    if name == "Ludo":
        name = "Ludo@kol"
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
            V.pcm_to_wav(pcm, raw)
            ok, why = tts_qa.check(str(raw), txt)
            if not ok and ("lặp" in why or "thừa" in why):
                # đo 23/11: Gemini đọc cả đoạn 2 lần liền. Cắt bỏ lần thứ 2 rồi nghe lại, khỏi tốn thêm lượt đọc
                cut = tts_qa.double_cut(str(raw))
                if cut:
                    V.pcm_to_wav(pcm[: int(cut * P.SAMPLE_RATE) * 2], raw)
                    ok, why2 = tts_qa.check(str(raw), txt)
                    why = f"cắt lần đọc thừa ở giây {cut}: {why2}" if ok else why
            if ok and len(open(raw, "rb").read()) / (P.SAMPLE_RATE * 2) > len(txt.split()) / 150 * 60 * 1.35:
                ok, why = False, "dài bất thường"
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
    # Trọng 22/11 (video AI bubble đọc sai "Revenue trên mỗi cổ phiếu"): lợi nhuận của cổ phiếu (EPS, P/E) là EARNINGS, không phải revenue;
    # "rủi ro so với lợi nhuận" là risk/reward. Chỉ lợi nhuận của dự án crypto mới đổi thành revenue.
    (r"(?i)tỷ lệ rủi ro so với lợi nhuận", "tỷ lệ risk/reward"),
    (r"(?i)(?<=lần )lợi nhuận", "earnings"),
    (r"(?i)lợi nhuận trên mỗi cổ phiếu", "earnings trên mỗi cổ phiếu"),
    (r"(?i)(?<!hứa )(?<!cam kết )lợi nhuận", "revenue"),
]
STOCK_HINT = re.compile(r"\bEPS\b|P/E|cổ phiếu|S&P|Nasdaq|Nvidia|Big Tech", re.I)


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
            if rep == "revenue" and _STOCK_CTX:
                rep = "earnings"   # bài về cổ phiếu: lợi nhuận = earnings
            obj = re.sub(pat, rep, obj)
        return re.sub(r"(^|[.!?]\s+)(insider|retail|unlock|revenue|earnings)\b", lambda m: m.group(1) + m.group(2).capitalize(), obj)
    return obj


_STOCK_CTX = False


def fix_terms_plan(plan: dict) -> dict:
    """Đổi từ cho cả kịch bản, tự nhận bài cổ phiếu/vĩ mô (EPS, P/E, cổ phiếu...) để dùng earnings thay revenue."""
    global _STOCK_CTX
    _STOCK_CTX = len(STOCK_HINT.findall(json.dumps(plan.get("sections") or [], ensure_ascii=False))) >= 3
    try:
        return fix_terms(plan)
    finally:
        _STOCK_CTX = False


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
    news = os.getenv("INSIGHT_FORMAT", "").strip().lower() == "news"   # Trọng 23/11: tin nóng dạng short
    prompt = PROMPT.format(posts=listing, minutes=1 if news else ic.get("target_minutes", 7),
                           max_sections=1 if news else ic.get("max_sections", 6))
    if news:
        prompt += NEWS_PROMPT.format()
    min_secs = 1 if news else 3

    def write(sys_: str, pr: str) -> dict:
        """Tin nóng cần nhanh (23/11 Gemini quá tải 503 cả 40 phút): Claude viết trước, Gemini dự phòng.
        Video insight dài giữ nguyên Gemini viết."""
        if news and (os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")):
            try:
                import script_review as SR
                old_m = os.environ.get("SCRIPT_REVIEW_MODEL")
                os.environ["SCRIPT_REVIEW_MODEL"] = os.getenv("NEWS_WRITER_MODEL", "sonnet")
                try:
                    return SR.run_claude(sys_ + "\n\n" + pr)
                finally:
                    if old_m is None:
                        os.environ.pop("SCRIPT_REVIEW_MODEL", None)
                    else:
                        os.environ["SCRIPT_REVIEW_MODEL"] = old_m
            except Exception as ex:
                log(f"   ! Claude viết kịch bản lỗi, chuyển sang Gemini: {str(ex)[:200]}")
        return V.llm_json(gem, cfg, sys_, pr)

    def as_news(pl: dict) -> dict:
        if news:
            pl["sections"] = [x for x in pl.get("sections", []) if x.get("narration")][:1]
            pl.update(format="short", news=True, shorts=[0], own_source=True,
                      short_cta=P.nodash(str((cfg.get("news_flash") or {}).get("short_cta") or pl.get("short_cta") or "")))
            pl["thumb_tag"] = pl.get("thumb_tag") or "TIN NÓNG"
        return pl
    if notes:
        prompt += "\nRút kinh nghiệm từ review các video trước (áp dụng):\n" + "\n".join(f"- {n}" for n in notes)
    plan = {}
    approved = os.getenv("INSIGHT_SCRIPT", "").strip()   # kịch bản Trọng đã duyệt (JSON) → dựng đúng lời đọc, không để AI viết lại
    if approved:
        plan = P.nodash(json.loads(Path(approved).read_text(encoding="utf-8")))
        log(f"   Dùng kịch bản đã duyệt: {approved} ({len(plan.get('sections', []))} phần)")
        # Trọng 22/11: video giáo dục tự viết, không có bài X gốc → nguồn số liệu ghi trong kịch bản ("source_post")
        if not posts and plan.get("source_post"):
            posts = [plan["source_post"]]
            log(f"   Không có link X, dùng nguồn số liệu trong kịch bản: {posts[0].get('url', '')}")
    for attempt in range(0 if approved else 3):
        plan = as_news(P.nodash(write(system, prompt)))
        top = {k: plan.get(k) for k in ("title", "hook", "hook_stat", "intro", "thumb_text", "thumb_stat")}
        n_ok = len([s for s in plan.get("sections", []) if s.get("narration") and not _banned(s)])
        if not _banned(top) and n_ok >= min_secs:
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
            plan = as_news(P.nodash(write(system, fix)))
        plan["script_score"] = rv.get("score")
        plan["script_review"] = {k: rv.get(k) for k in ("score", "scores", "nhan_xet", "pass")}
    plan = scrub_plan(plan)
    plan = fix_terms_plan(plan)   # Trọng chốt 21/11: tự đổi từ Việt sang từ chuyên ngành tiếng Anh
    try:   # Trọng 22/11: soát khung (nhịp đổi hình, biểu đồ, đếm ý, ảnh bìa, short) trước khi tốn lượt giọng đọc
        import video_lint as VL
        plan["lint"] = VL.lint(plan)
        log(f"   Soát khung: {len(plan['lint'])} chỗ cần sửa" + "".join(f"\n     - {x}" for x in plan["lint"][:12]))
    except Exception as ex:
        log(f"   ! soát khung lỗi: {ex}")
    if len([s for s in plan.get("sections", []) if s.get("narration")]) < (1 if news else 2) or not plan.get("hook"):
        raise RuntimeError("Kịch bản không đủ nội dung sau khi bỏ đoạn ENA")
    plan["sections"] = [s for s in plan.get("sections", []) if s.get("narration")][: int(ic.get("max_sections", 6))]
    if os.getenv("INSIGHT_SCRIPT_ONLY") == "1":   # Trọng 23/11: tin nóng phải được duyệt kịch bản trên Telegram trước khi dựng
        plan["source_post"] = plan.get("source_post") or (posts[0] if posts else {})
        (lab / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"✓ Chỉ viết kịch bản (chờ duyệt): {lab / 'plan.json'}")
        return lab
    plan["posts"] = posts
    log("③ Dữ liệu thị trường + ảnh (AI lọc ảnh lạc đề)")
    md = market_data(lab)
    coin_data(lab, plan, md)
    wma_data(plan, md)   # biểu đồ BTC tuần + 200WMA/350WMA (Trọng 23/11)
    dow_data(plan, md)   # chart lý thuyết Dow trên BTC tuần (Trọng 27/11, 28/11 bỏ backtest)
    trend_data(plan, md)   # biểu đồ Google Trends (Trọng 24/11)
    plan = live_numbers(plan, md)   # Trọng 22/11: hook, biểu đồ, ảnh bìa, short dùng CÙNG một bộ số giá thật
    (lab / "data.json").write_text(json.dumps(md, ensure_ascii=False), encoding="utf-8")
    save_images(lab, plan, gem, cfg)
    photo_beats(lab, plan)
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
