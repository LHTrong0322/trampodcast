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
                "title": "tiêu đề ngắn cho hình, ≤ 6 từ"}}}}''')
PROMPT += """
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


def save_images(lab: Path, plan: dict):
    img = lab / "img"
    credits = {}
    secs = plan["sections"]
    jobs = [("intro", {"visual_queries": [plan.get("theme", ""), "trader desk night screens", "city skyline night"],
                       "category": "Dự án"}, "landscape", 5)]
    for k, s in enumerate(secs):
        jobs.append((f"s{k}", {"visual_queries": s.get("visual_queries") or [], "category": "Dự án",
                               "visual_query": s.get("heading", "")}, "landscape", 6))
        jobs.append((f"s{k}v", {"visual_queries": s.get("visual_queries") or [], "category": "Dự án"}, "portrait", 4))
    for name, item, ori, n in jobs:
        files = []
        for i, (im, cr) in enumerate(V.find_images(item, ori, n)):
            fn = f"{name}_{i}.jpg"
            im.save(img / fn, quality=90)
            files.append(fn)
            credits[fn] = cr
        plan.setdefault("images", {})[name] = files
    plan["image_credits"] = credits


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
    gem = P.Gemini(key or os.getenv("GEMINI_API_KEY", ""))
    pcs = I.tts_parts(gem, cfg, parts)
    for i, pcm in enumerate(pcs):
        V.pcm_to_wav(pcm, outdir / f"{i:02d}.wav")
    return len(pcs) == len(parts)


def prepare(links: str, voices: str, out: Path):
    cfg = V.load_cfg()
    ic = cfg.get("insight") or {}
    tag = datetime.now(P.VN_TZ).strftime("%Y%m%d-%H%M")
    lab = out / tag
    lab.mkdir(parents=True, exist_ok=True)
    posts = [read_post(u, lab) for u in links.split() if u.strip()]
    gem = P.Gemini(os.getenv("INSIGHT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", ""))
    listing = "\n\n".join(f"[{i}] @{p['handle']} ({p['author']}) — {p.get('title', '')}:\n{p['text'][:9000]}"
                          for i, p in enumerate(posts))
    system = I.SYSTEM.format(name=ic.get("name", "Smart Penguin Insights"), host_desc=ic.get("host_desc", "điềm đạm, sâu sắc"),
                             self_word=ic.get("self_word", "mình"), audience=ic.get("audience", "mọi người"))
    log("② Viết kịch bản")
    plan = V.llm_json(gem, cfg, system, PROMPT.format(posts=listing, minutes=ic.get("target_minutes", 7),
                                                      max_sections=ic.get("max_sections", 6)))
    plan["sections"] = [s for s in plan.get("sections", []) if s.get("narration")]
    plan["posts"] = posts
    log("③ Dữ liệu thị trường + ảnh")
    (lab / "data.json").write_text(json.dumps(market_data(lab), ensure_ascii=False), encoding="utf-8")
    save_images(lab, plan)
    # các đoạn đọc: hook, intro, từng section, outro, hook của shorts
    sh = [i for i in plan.get("shorts", []) if isinstance(i, int) and 0 <= i < len(plan["sections"])][:3]
    shr = plan.get("short_hooks") or {}
    parts = [("hook", plan.get("hook", "")), ("intro", plan.get("intro", ""))]
    parts += [(f"s{k}", s["narration"]) for k, s in enumerate(plan["sections"])]
    parts += [("outro", plan.get("outro", ""))]
    parts += [(f"sh{i}", str(shr.get(str(i)) or shr.get(i) or "")) for i in sh]
    parts = [(k, P.sanitize_script(t)) for k, t in parts if t and t.strip()]
    plan["parts"] = [{"key": k, "text": t} for k, t in parts]
    plan["shorts"] = sh
    plan["voices"] = {}
    for v in [x.strip() for x in voices.split(",") if x.strip()]:
        log(f"④ Đọc giọng {v}")
        try:
            ok = speak(cfg, v, [t for _, t in parts], lab / "audio" / re.sub(r"\W+", "_", v))
        except Exception as ex:
            log(f"   ! lỗi: {ex}")
            ok = False
        plan["voices"][v] = re.sub(r"\W+", "_", v) if ok else None
    (lab / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    zp = shutil.make_archive(str(out / f"lab-{tag}"), "zip", lab)
    repo = os.getenv("GITHUB_REPOSITORY")
    if repo and os.getenv("GH_TOKEN"):
        subprocess.run(["gh", "release", "create", f"lab-{tag}", zp, "-R", repo, "--prerelease",
                        "--title", f"Lab nguyên liệu {tag}", "--notes", plan.get("title", "")], check=True)
    log(f"✓ Xong: lab-{tag} · giọng: {plan['voices']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare"])
    ap.add_argument("--links", default="")
    ap.add_argument("--voices", default="vieneu:Hải Đăng,gemini:Ludo")
    ap.add_argument("--out", default="lab")
    a = ap.parse_args()
    prepare(a.links, a.voices, Path(a.out))


if __name__ == "__main__":
    main()
