#!/usr/bin/env python3
"""
TRẠM INSIGHT LAB — chuẩn bị "nguyên liệu" để thử nhiều kiểu dựng video từ cùng 1 kịch bản.

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
      "project": {{"name": "tên dự án/coin CHÍNH được bàn trong phần này (vd Hyperliquid), trống nếu không có", "ticker": "vd HYPE"}}}}''')
PROMPT += """
Độ dài: nếu bài nguồn đủ ý, viết đủ {max_sections} phần, mỗi phần 130-180 từ; hook ≤ 2 câu thật cuốn.
Không nhắc đến AI, máy, bot hay "nội dung tổng hợp" ở bất kỳ đâu trong lời đọc.
Gợi ý chọn data.type: nói về tâm lý thị trường → fear_greed; về altcoin vs bitcoin, dòng tiền → dominance;
về coin cụ thể → coin_chart; so sánh 2-4 thứ có số → stat_compare (điền items); danh sách việc cần làm /
tiêu chí đánh giá → checklist (điền items, value để trống); bức tranh toàn thị trường → market_heatmap."""


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


def prepare(posts_or_links, out: Path, voices: list[str] | None = None, release: bool = False,
            notes: list[str] | None = None) -> Path:
    """Viết kịch bản + lấy dữ liệu/ảnh + đọc giọng. Giọng: thử lần lượt theo danh sách (Gemini Ludo trước,
    hết lượt thì VieNeu Hải Đăng) — cả video luôn dùng MỘT giọng."""
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
    listing = "\n\n".join(f"[{i}] @{p['handle']} ({p['author']}) — {p.get('title', '')}:\n{p['text'][:9000]}"
                          for i, p in enumerate(posts))
    system = I.SYSTEM.format(name=ic.get("name", "Smart Penguin Insights"), host_desc=ic.get("host_desc", "điềm đạm, sâu sắc"),
                             self_word=ic.get("self_word", "mình"), audience=ic.get("audience", "mọi người"))
    log("② Viết kịch bản")
    prompt = PROMPT.format(posts=listing, minutes=ic.get("target_minutes", 7), max_sections=ic.get("max_sections", 6))
    if notes:
        prompt += "\nRút kinh nghiệm từ review các video trước (áp dụng):\n" + "\n".join(f"- {n}" for n in notes)
    plan = V.llm_json(gem, cfg, system, prompt)
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
    parts = [(k, P.sanitize_script(t)) for k, t in parts if t and t.strip()]
    plan["parts"] = [{"key": k, "text": t} for k, t in parts]
    plan["shorts"] = [i for i in plan.get("shorts", []) if isinstance(i, int) and 0 <= i < len(plan["sections"])][
                     : int(ic.get("shorts", 3))]
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
