#!/usr/bin/env python3
"""
TRẠM INSIGHT — biến các bài X (tweet/thread/research) bạn gửi vào bot Telegram thành
video CHIA SẺ INSIGHT / KIẾN THỨC / KINH NGHIỆM: 1 video dài YouTube + video ngắn highlight.

  python insight.py inbox  --out public    # đọc tin nhắn Telegram mới, lưu link, báo đã nhận
  python insight.py cook   --out public    # đủ link → dựng video, gửi Telegram + GitHub Release
         [--force]                          # dựng ngay dù chưa đủ số link tối thiểu

Gemini key: dùng INSIGHT_GEMINI_API_KEY (project riêng) nếu có, không thì GEMINI_API_KEY.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

import podcast as P
import video as V
import motion as M
import music as MU

log = P.log
SR = V.SR
URL_RE = re.compile(r"https?://\S+")
X_RE = re.compile(r"https?://(?:www\.|mobile\.)?(?:x|twitter)\.com/([A-Za-z0-9_]+)/status/(\d+)")


# ---------------------------------------------------------------------------
# kho dữ liệu
# ---------------------------------------------------------------------------
def store_path(out: Path) -> Path:
    return out / "insight" / "store.json"


def load_store(out: Path) -> dict:
    p = store_path(out)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"offset": 0, "posts": [], "videos": [], "force": False}


def save_store(out: Path, st: dict):
    p = store_path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    st["posts"] = st["posts"][-400:]
    p.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def tg(method: str, **data):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return None
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", data=data, timeout=60)
    return r.json() if r.ok else None


# ---------------------------------------------------------------------------
# đọc nội dung bài X (không cần X API): fxtwitter → oEmbed → trang web thường
# ---------------------------------------------------------------------------
def read_x(url: str) -> dict | None:
    m = X_RE.search(url)
    if not m:
        return None
    user, pid = m.group(1), m.group(2)
    try:
        r = requests.get(f"https://api.fxtwitter.com/{user}/status/{pid}", timeout=25,
                         headers={"User-Agent": P.UA})
        if r.ok:
            t = r.json().get("tweet") or {}
            text = (t.get("raw_text") or {}).get("text") or t.get("text") or ""
            art = t.get("article") or {}
            if art:
                text = (art.get("title", "") + "\n" + (art.get("preview_text") or "") + "\n" + text).strip()
            if t.get("quote"):
                text += "\n[Trích dẫn] " + (t["quote"].get("text") or "")
            if text.strip():
                a = t.get("author") or {}
                return {"author": a.get("name") or user, "handle": a.get("screen_name") or user,
                        "text": text.strip()[:6000], "url": url}
    except Exception as ex:
        log(f"   ! fxtwitter lỗi: {ex}")
    try:
        r = requests.get("https://publish.twitter.com/oembed", params={"url": url, "omit_script": 1},
                         timeout=25, headers={"User-Agent": P.UA})
        if r.ok:
            j = r.json()
            text = P.clean_text(re.sub(r"<a [^>]*>pic\.twitter\.com[^<]*</a>", "", j.get("html", "")), 6000)
            text = re.sub(r"— .*$", "", text).strip()
            if text:
                return {"author": j.get("author_name", user), "handle": user, "text": text, "url": url}
    except Exception as ex:
        log(f"   ! oEmbed lỗi: {ex}")
    return None


def read_web(url: str) -> dict | None:
    try:
        r = requests.get(url, timeout=25, headers={"User-Agent": P.UA})
        r.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        title = (soup.find("meta", property="og:title") or {}).get("content") or (soup.title.string if soup.title else "")
        paras = " ".join(p.get_text(" ") for p in soup.find_all("p"))
        text = re.sub(r"\s+", " ", f"{title}. {paras}").strip()[:6000]
        host = re.sub(r"^www\.", "", url.split("/")[2])
        return {"author": host, "handle": host, "text": text, "url": url} if len(text) > 200 else None
    except Exception as ex:
        log(f"   ! đọc trang lỗi: {ex}")
        return None


# ---------------------------------------------------------------------------
# 1. HỘP THƯ: nhận link từ Telegram
# ---------------------------------------------------------------------------
def inbox(out: Path, cfg: dict, extra_links: str = "") -> dict:
    st = load_store(out)
    owner = str(os.getenv("TELEGRAM_CHAT_ID", "")).strip()
    res = tg("getUpdates", offset=st["offset"] + 1, timeout=0, allowed_updates='["message"]') or {}
    if extra_links.strip():   # link nhập trực tiếp khi bấm chạy trên GitHub
        res.setdefault("result", []).append({"update_id": st["offset"],
                                             "message": {"chat": {"id": owner}, "text": extra_links}})
    known = {p["url"] for p in st["posts"]}
    added = 0
    for up in res.get("result", []):
        st["offset"] = max(st["offset"], up["update_id"])
        msg = up.get("message") or {}
        chat = str((msg.get("chat") or {}).get("id", ""))
        if owner and chat != owner:          # chỉ nhận tin của chủ bot
            continue
        text = msg.get("text") or msg.get("caption") or ""
        if text.strip().lower().startswith("/cook"):
            st["force"] = True
            tg("sendMessage", chat_id=chat, text="👨‍🍳 Ok! Lần chạy kế tiếp (trong ~3 tiếng) bot sẽ cook video Insight ngay.")
            continue
        if text.strip().lower().startswith("/list"):
            pend = [p for p in st["posts"] if not p.get("used")]
            tg("sendMessage", chat_id=chat, text=f"📥 Đang chờ {len(pend)} link:\n" +
               "\n".join(f"• {p.get('handle', '')}: {p['url']}" for p in pend[-20:]))
            continue
        for url in URL_RE.findall(text):
            url = url.rstrip(").,]")
            url = re.sub(r"\?.*$", "", url) if X_RE.search(url) else url
            if url in known:
                continue
            post = read_x(url) or read_web(url)
            if not post:
                tg("sendMessage", chat_id=chat, text=f"⚠️ Không đọc được nội dung link này (private hoặc bị chặn):\n{url}")
                continue
            post.update(received=datetime.now(P.VN_TZ).isoformat(), used=False, note=URL_RE.sub("", text).strip()[:500])
            st["posts"].append(post)
            known.add(url)
            added += 1
    pend = [p for p in st["posts"] if not p.get("used")]
    need = int((cfg.get("insight") or {}).get("min_posts", 3))
    if added:
        tg("sendMessage", chat_id=owner, text=(
            f"✅ Đã nhận {added} link mới · đang chờ {len(pend)} link.\n"
            + (f"Đủ {need} link → tối nay bot sẽ cook video Insight." if len(pend) >= need
               else f"Cần thêm {need - len(pend)} link nữa để cook (hoặc gửi /cook để làm ngay).")))
    save_store(out, st)
    log(f"   Hộp thư: +{added} link, đang chờ {len(pend)}")
    return st


def should_cook(st: dict, cfg: dict, force: bool) -> bool:
    ic = cfg.get("insight") or {}
    pend = [p for p in st["posts"] if not p.get("used")]
    if not pend:
        return False
    if force or st.get("force"):
        return True
    now = datetime.now(P.VN_TZ)
    lo, hi = ic.get("cook_hours", [19, 23])
    last = st["videos"][-1]["date"] if st["videos"] else None
    cooked_today = bool(last) and datetime.fromisoformat(last).date() == now.date()
    return len(pend) >= int(ic.get("min_posts", 3)) and lo <= now.hour <= hi and not cooked_today


# ---------------------------------------------------------------------------
# 2. VIẾT KỊCH BẢN
# ---------------------------------------------------------------------------
SYSTEM = """Bạn là biên kịch cho kênh video tiếng Việt "{name}" — chuỗi CHIA SẺ INSIGHT, KIẾN THỨC,
KINH NGHIỆM đầu tư crypto, giọng {host_desc}. Xưng "{self_word}", gọi người xem là "{audience}".
Nguyên liệu là các bài viết/thread chất lượng trên X do chủ kênh chọn. Nhiệm vụ: rút ra bài học,
khung tư duy, kinh nghiệm thực chiến có thể áp dụng; giải thích dễ hiểu (khái niệm khó thì giải
thích ngay bằng lời đơn giản), có ví dụ cụ thể. KHÔNG đọc nguyên văn bài gốc, phải diễn giải lại
bằng lời của mình; luôn ghi nhận ý tưởng thuộc về ai (vd "theo chia sẻ của @abc").
Không hô hào mua bán, không hứa lợi nhuận. Lời văn NÓI, đọc bằng máy: không markdown, không
emoji, không link; số đọc tự nhiên. """ + V.TERMS

PROMPT = """Các bài viết nguồn (mỗi bài có số [id]):
{posts}

Viết 1 tập video dài khoảng {minutes} phút. Có thể gom các bài cùng chủ đề; bỏ bài kém giá trị.
Trả về DUY NHẤT JSON:
{{"title": "tiêu đề YouTube hấp dẫn, đúng chính tả, ≤ 90 ký tự",
  "description": "mô tả 2-3 câu",
  "theme": "chủ đề chung của tập, ≤ 6 từ (vd 'Quản trị rủi ro khi trade')",
  "hook": "câu mở màn ≤ 16 từ gây tò mò mạnh, đọc ~3 giây, không chào hỏi",
  "hook_stat": "con số ngắn hiện chữ to (vd '90%', '\\$1M'); CHỈ điền khi là số liệu thật có trong bài nguồn và người xem hiểu ngay ý nghĩa, nếu không để trống",
  "hook_label": "giải thích ≤ 6 từ",
  "intro": "lời chào + giới thiệu tập (~300 ký tự)",
  "sections": [
    {{"heading": "tên insight ngắn, ≤ 60 ký tự",
      "key_stat": "con số/cụm từ đắt giá nhất phần này (kiểu tiếng Anh: '\\$400M', '3x', '80%'), có thể trống",
      "key_label": "giải thích ≤ 6 từ",
      "narration": "lời giảng 4-7 câu (~450-700 ký tự): insight là gì, vì sao đúng, ví dụ, cách áp dụng",
      "visual_queries": ["4 từ khoá TIẾNG ANH tìm ảnh stock, 2-4 từ, mô tả VẬT/CẢNH CỤ THỂ nhìn thấy được và đúng chủ đề tài chính/công nghệ (vd 'revenue growth chart', 'business handshake contract', 'trader laptop charts'); tránh từ trừu tượng dễ ra ảnh lạc đề"],
      "source_ids": [id bài nguồn]}}
  ],
  "outro": "tổng kết 2-3 ý chính + nhắc không phải lời khuyên đầu tư + mời đăng ký (~280 ký tự)",
  "shorts": [số thứ tự (bắt đầu từ 0) của 2-3 section hay nhất để cắt video ngắn],
  "short_hooks": {{"số thứ tự section": "câu hook ≤ 12 từ đọc ~2 giây"}},
  "thumb_text": "3-5 từ IN HOA cho ảnh bìa", "thumb_stat": "con số ngắn cho ảnh bìa, có thể trống"}}
Số section: 3 đến {max_sections}."""


def write_script(gem, cfg: dict, posts: list[dict]) -> dict:
    ic = cfg.get("insight") or {}
    listing = "\n\n".join(f"[{i}] @{p.get('handle', '')} ({p.get('author', '')})"
                          + (f" — ghi chú của chủ kênh: {p['note']}" if p.get("note") else "")
                          + f":\n{p['text'][:3500]}" for i, p in enumerate(posts))
    system = SYSTEM.format(name=ic.get("name", "Smart Penguin Insights"), host_desc=ic.get("host_desc", "điềm đạm, sâu sắc, gần gũi"),
                           self_word=ic.get("self_word", "mình"), audience=ic.get("audience", "mọi người"))
    return V.llm_json(gem, cfg, system, PROMPT.format(posts=listing, minutes=ic.get("target_minutes", 7),
                                                      max_sections=ic.get("max_sections", 6)))


def tts_parts(gem, cfg, parts: list[str], max_chars=3600) -> list[bytes]:
    """Đọc nhiều đoạn bằng ít lượt nhất (gộp đến ~3.600 ký tự/lượt), rồi tự cắt lại từng đoạn."""
    out, batch = [], []

    def flush():
        if not batch:
            return
        pcm = V.tts_once(gem, cfg, "\n\n".join(batch))
        for a, b in V.split_points(pcm, batch):
            out.append(V.slice_pcm(pcm, a, b))
        batch.clear()
        if cfg["podcast"].get("tts_provider", "gemini") == "gemini":
            time.sleep(int(cfg["podcast"].get("tts_pause_seconds", 25)))
    for ptxt in parts:
        if batch and sum(map(len, batch)) + len(ptxt) > max_chars:
            flush()
        batch.append(ptxt)
    flush()
    return out


# ---------------------------------------------------------------------------
# 3. DỰNG VIDEO
# ---------------------------------------------------------------------------
def cook(out: Path, cfg: dict, gem, st: dict) -> dict:
    ic = cfg.get("insight") or {}
    vcfg = cfg.get("video") or {}
    V.BRAND.update(name=ic.get("brand", "SMART PENGUIN INSIGHTS").upper(), title_tag=ic.get("title_tag", "INSIGHT CRYPTO"),
                   outro_line=ic.get("outro_line", "Đăng ký kênh để nhận insight crypto mỗi tuần"),
                   cta_v=ic.get("cta_v", "Xem full trên YouTube · @Trong0322"), thumb_tag="{week}",
                   tg_header="Video Insight: {week}", tag_prefix="insight")
    V.CAT_COLORS.setdefault("Insight", (123, 92, 255))
    posts = [p for p in st["posts"] if not p.get("used")][: int(ic.get("max_posts", 8))]
    log(f"② Viết kịch bản Insight từ {len(posts)} bài")
    plan = write_script(gem, cfg, posts)
    secs = [s for s in plan.get("sections", []) if s.get("narration")][: int(ic.get("max_sections", 6))]
    if not secs:
        raise RuntimeError("AI không trả về nội dung")
    theme = plan.get("theme") or "Insight crypto"
    hook = P.sanitize_script(plan.get("hook", ""))
    intro, outro = P.sanitize_script(plan.get("intro", "")), P.sanitize_script(plan.get("outro", ""))
    narr = [P.sanitize_script(s["narration"]) for s in secs]
    sh_idx = [i for i in plan.get("shorts", []) if isinstance(i, int) and 0 <= i < len(secs)][: int(ic.get("shorts", 3))]
    sh_raw = plan.get("short_hooks") or {}
    sh_lines = {i: P.sanitize_script(str(sh_raw.get(str(i)) or sh_raw.get(i) or "")) for i in sh_idx}

    # 1-2 lượt đọc cho cả tập
    parts = ([hook] if hook else []) + [intro] + narr + [outro] + [sh_lines[i] for i in sh_idx if sh_lines[i]]
    log(f"③ Đọc giọng ({sum(map(len, parts))} ký tự)")
    pcs = tts_parts(gem, cfg, parts)
    hook_pcm = pcs.pop(0) if hook else b""
    intro_pcm = pcs.pop(0)
    sec_pcm = [pcs.pop(0) for _ in narr]
    outro_pcm = pcs.pop(0)
    sh_pcm = {i: pcs.pop(0) for i in sh_idx if sh_lines[i] and pcs}

    now = datetime.now(P.VN_TZ)
    authors = []
    items = []
    for k, (s, pcm) in enumerate(zip(secs, sec_pcm)):
        srcs = [posts[i] for i in s.get("source_ids", []) if isinstance(i, int) and 0 <= i < len(posts)]
        handles = list(dict.fromkeys(f"@{p['handle']}" for p in srcs))
        authors += handles
        items.append({
            "headline": V.en_money(s.get("heading", "")), "key_stat": V.en_money(s.get("key_stat", "")),
            "key_label": V.en_money(s.get("key_label", "")), "narration": narr[k],
            "sub_text": V.en_money(narr[k]), "category": "Insight", "importance": 5, "tickers": [],
            "is_update": False, "date": now.isoformat(),
            "date_text": ("Nguồn: " + ", ".join(handles[:2])) if handles else theme,
            "visual_queries": s.get("visual_queries") or [], "visual_query": theme,
            "pcm": pcm, "speech_dur": len(pcm) / SR / 2, "hook": sh_lines.get(k, ""), "coin_chart": None,
            "sources": [{"name": "@" + p["handle"], "url": p["url"]} for p in srcs]})

    every = float(vcfg.get("image_seconds", 4.0))
    log("   🖼  Tìm ảnh minh hoạ")
    credits = []
    for k, it in enumerate(items):
        n = max(2, min(10, int(math.ceil((it["speech_dur"] + 0.6) / every))))
        it["imgs_h"] = V.find_images(it, "landscape", n)
        it["imgs_v"] = V.find_images(it, "portrait", n) if k in sh_idx else []
        credits += [c for _, c in it["imgs_h"] + it["imgs_v"]]
    intro_imgs = V.find_images({"visual_queries": [theme, "thinking strategy chess", "notebook planning desk"],
                                "category": "Dự án"}, "landscape", 4)
    credits += [c for _, c in intro_imgs]

    tmp = Path(tempfile.mkdtemp())
    rd = out / "insight" / "render"
    rd.mkdir(parents=True, exist_ok=True)
    tag = now.strftime("%Y%m%d-%H%M")
    title = V.en_money(plan.get("title") or theme)
    wl = f"Insight · {theme}"
    T = 0.6
    scenes = []
    if hook_pcm:
        hd = len(hook_pcm) / SR / 2 + 0.35
        scenes.append({"dur": hd, "pcm": hook_pcm + V.gap(0.35), "wipe": False,
                       "draw": V.scene_hook(V.en_money(hook), V.en_money(plan.get("hook_stat", "")),
                                            V.en_money(plan.get("hook_label", "")), hd, intro_imgs)})
    idur = len(intro_pcm) / SR / 2 + T
    scenes.append({"dur": idur, "pcm": intro_pcm + V.gap(T), "wipe": bool(hook_pcm),
                   "draw": V.scene_title(title, theme, cfg["insight"].get("host_name", "") or "", idur, intro_imgs)})
    marks = [(0, "Mở đầu")]
    tcur = sum(s_["dur"] for s_ in scenes)
    for k, it in enumerate(items, 1):
        a_ = it["pcm"] + V.gap(T)
        dur = len(a_) / SR / 2
        marks.append((tcur, it["headline"][:70]))
        scenes.append({"dur": dur, "pcm": a_, "draw": V.scene_story_h(it, k, len(items), wl, dur, it["imgs_h"], every)})
        tcur += dur
    marks.append((tcur, "Tổng kết"))
    o_ = outro_pcm + V.gap(2.5)
    scenes.append({"dur": len(o_) / SR / 2, "pcm": o_, "draw": V.scene_outro()})
    for sc in scenes:
        n = int(round(sc["dur"] * M.FPS))
        sc["pcm"] = (sc["pcm"] + V.gap(1))[: int(n / M.FPS * SR) * 2]
        sc["dur"] = n / M.FPS
    seed = int(now.strftime("%y%j"))
    total_s = sum(s_["dur"] for s_ in scenes)
    log(f"④ Dựng video dài ({total_s / 60:.1f} phút)")
    h_mp4 = M.render(scenes, 1920, 1080, rd / f"insight-{tag}-16x9.mp4", tmp, log=log,
                     watermark=V.watermark_layer(False),
                     music_pcm=MU.make_music(total_s + 1, seed) if vcfg.get("music", True) else None,
                     music_vol=float(vcfg.get("music_volume", 0.22)))

    v_files = []
    speed = float(vcfg.get("shorts_speed", 1.08))
    for n, k in enumerate(sh_idx, 1):
        it = dict(items[k])
        body = P._ffmpeg_pcm(["-f", "s16le", "-ar", str(SR), "-ac", "1"], it["pcm"], f"atempo={speed}")
        sents = [x for x in re.split(r"(?<=[.!?…])\s+", it["narration"]) if x.strip()]
        hk = sh_pcm.get(k, b"")
        budget = float(ic.get("shorts_max_seconds", 45)) - 2.6 - len(hk) / SR / 2 - 0.2
        if len(body) / SR / 2 > budget and len(sents) > 1:
            b_ = V.chunk_bounds({"pcm": body}, [s_.split() for s_ in sents], len(body) / SR / 2)
            keep = max(1, len([1 for a, b in b_ if b <= budget]))
            body = body[: int(b_[keep - 1][1] * SR) * 2]
            sents = sents[:keep]
        text = " ".join(sents)
        it["narration"] = ((sh_lines[k] + " ") if hk else "") + text
        it["sub_text"] = V.en_money(it["narration"])
        it["pcm"] = (hk + V.gap(0.15) if hk else b"") + body
        it["speech_dur"] = len(it["pcm"]) / SR / 2
        a_ = it["pcm"] + V.gap(0.4)
        dur = len(a_) / SR / 2
        vs = [{"dur": dur, "pcm": a_, "draw": V.scene_story_v(it, dur, wl, it["imgs_v"], every * 0.8), "wipe": False},
              {"dur": 2.2, "pcm": V.gap(2.2), "draw": V.scene_outro(vertical=True)}]
        for sc in vs:
            kk = int(round(sc["dur"] * M.FPS))
            sc["pcm"] = (sc["pcm"] + V.gap(1))[: int(kk / M.FPS * SR) * 2]
            sc["dur"] = kk / M.FPS
        tot = sum(s_["dur"] for s_ in vs)
        v = M.render(vs, 1080, 1920, rd / f"insight-short-{tag}-{n}.mp4", tmp, log=lambda *a: None,
                     watermark=V.watermark_layer(True),
                     music_pcm=MU.make_music(tot + 1, seed + n) if vcfg.get("music", True) else None,
                     music_vol=float(vcfg.get("music_volume", 0.22)) * 1.15)
        v_files.append((v, it))
        log(f"   ✓ Short {n}: {tot:.0f}s")

    thumb = rd / f"insight-thumb-{tag}.png"
    bg = items[0]["imgs_h"][0][0] if items[0].get("imgs_h") else (intro_imgs[0][0] if intro_imgs else None)
    V.make_thumbnail(V.en_money(plan.get("thumb_text") or theme), V.en_money(plan.get("thumb_stat", "")),
                     theme.upper(), bg).save(thumb)

    src_lines = "\n".join(f"• @{p['handle']}: {p['url']}" for p in posts)
    desc = (plan.get("description", "") + "\n\n" + V.youtube_chapters(marks)
            + "\n\nÝ tưởng tham khảo từ các bài viết (đã diễn giải lại):\n" + src_lines
            + "\n\nAgent build by @Trong0322 · Nội dung do AI tổng hợp, không phải lời khuyên đầu tư."
            + ("\n\nNguồn ảnh (giấy phép miễn phí): " + "; ".join(dict.fromkeys(credits)) if credits else ""))
    for p in posts:
        p["used"] = True
    st["force"] = False
    st["videos"].append({"date": now.isoformat(), "title": title, "posts": [p["url"] for p in posts]})
    return {"tag": tag, "title": title, "description": desc, "week": theme, "h": h_mp4,
            "shorts": v_files, "thumb": thumb}


def produce(out: Path, cfg: dict, st: dict, links: str = ""):
    """Quy trình chính thức (kiểu video 2): nguyên liệu → dựng Remotion → SEO + Release + Telegram → bot review."""
    import insight_lab as L
    import insight_render as R
    import insight_publish as PB
    ic = cfg.get("insight") or {}
    posts = [p for p in st["posts"] if not p.get("used")][: int(ic.get("max_posts", 8))]
    if links.strip():
        src = links
    elif posts:
        src = posts
    else:
        log("Không có link nào đang chờ.")
        return
    # rút kinh nghiệm từ 3 lần review gần nhất
    rp = out / "insight" / "reviews.json"
    tips = []
    if rp.exists():
        for r in json.loads(rp.read_text(encoding="utf-8"))[-3:]:
            tips += r.get("script_tips") or []
    forced = [v.strip() for v in os.getenv("INSIGHT_VOICE", "").split(",") if v.strip()]
    lab = L.prepare(src, Path("lab"), voices=forced or None, notes=tips[-6:])
    res = R.render(lab, Path("render_out"))
    PB.publish(lab, res, Path("render_out"), data_dir=out)
    for p in st["posts"]:
        if (links.strip() and p.get("url") and p["url"].split("?")[0] in links) or (not links.strip() and p in posts):
            p["used"] = True
    st["force"] = False
    st["videos"].append({"date": datetime.now(P.VN_TZ).isoformat(), "title": res["plan"].get("title", ""),
                         "posts": [p.get("url") for p in res["plan"].get("posts", [])]})
    save_store(out, st)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["inbox", "cook"])
    ap.add_argument("--out", default="public")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--links", default="", help="thêm link trực tiếp (cách nhau bởi dấu cách)")
    ap.add_argument("--voice-provider", default="", help="gemini | vieneu")
    ap.add_argument("--voice-name", default="")
    args = ap.parse_args()
    out = Path(args.out)
    cfg = V.load_cfg()
    if not (cfg.get("insight") or {}).get("enabled", True):
        log("Trạm Insight đang tắt trong sources.yaml")
        return
    if args.mode == "inbox":
        st = inbox(out, cfg, args.links)
        go = should_cook(st, cfg, args.force)
        log(f"   Cook hôm nay: {'CÓ' if go else 'chưa'}")
        if os.getenv("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"cook={'true' if go else 'false'}\n")
        return
    st = load_store(out)
    if not should_cook(st, cfg, True if args.force else st.get("force", False)) and not args.force:
        if not [p for p in st["posts"] if not p.get("used")]:
            log("Không có link nào đang chờ.")
            return
    produce(out, cfg, st, args.links)
    log("✓ Xong video Insight!")


if __name__ == "__main__":
    main()
