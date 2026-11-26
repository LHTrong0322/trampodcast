"""Smart Penguin Insights, xuất bản: ảnh bìa, gói SEO (YouTube + TikTok), GitHub Release, gửi Telegram,
và BOT REVIEW (AI xem khung hình, chấm điểm, gợi ý cải tiến cho video sau)."""
from __future__ import annotations

import time
import base64
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
import insight_render as R
from hashtags import with_tags   # hashtag không trùng (Trọng 22/11)

log = P.log


def ts(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600}:{sec // 60 % 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60:02d}:{sec % 60:02d}"


# ---------------------------------------------------------------------------
# SEO
# ---------------------------------------------------------------------------
SEO_SYSTEM = """Bạn là chuyên gia SEO YouTube & TikTok mảng crypto/đầu tư tại Việt Nam (khán giả Việt, tìm kiếm bằng
tiếng Việt lẫn từ khoá tiếng Anh như crypto, altcoin, DCA, tokenomics...). Viết chuẩn thuật toán: từ khoá chính nằm
đầu tiêu đề và 2 câu đầu mô tả; tiêu đề gây tò mò nhưng KHÔNG câu view sai sự thật; không hứa lợi nhuận;
không nhắc AI/bot. Tên kênh: {brand}."""

SEO_PROMPT = """Video dài ({minutes:.1f} phút): "{title}"
Chủ đề: {theme}
Các ý chính:
{points}
{source_line}Video ngắn (9:16) cắt từ các ý: {shorts}

Trả JSON:
{{
  "keyword": "từ khoá chính",
  "yt_titles": ["3 phương án tiêu đề YouTube ≤ 70 ký tự, có từ khoá chính ở đầu"],
  "yt_intro": "2-3 câu mở đầu mô tả (chứa từ khoá chính, nói rõ người xem nhận được gì)",
  "yt_takeaways": ["3-5 gạch đầu dòng: điều người xem học được"],
  "yt_tags": ["18-25 tag, trộn tiếng Việt có dấu, không dấu và tiếng Anh, tổng < 450 ký tự"],
  "hashtags": ["3 hashtag cho YouTube, vd #crypto"],
  "pinned_comment": "1 bình luận ghim kèm câu hỏi kéo tương tác",
  "shorts": [{{"yt_title": "tiêu đề Shorts ≤ 80 ký tự kèm #Shorts", "tiktok_caption": "caption TikTok ≤ 150 ký tự, có câu hỏi/CTA", "tiktok_hashtags": ["5-7 hashtag TikTok, trộn rộng + ngách: #crypto #dautu ..."]}}]
}}"""


def seo_pack(gem, cfg, res: dict) -> dict:
    plan = res["plan"]
    ic = cfg.get("insight") or {}
    post = (plan.get("posts") or [{}])[0]
    # Trọng 22/11: video own_source là SẢN PHẨM CỦA TRỌNG: mô tả trên mọi mạng xã hội không nhắc tác giả/bài gốc
    own = bool(plan.get("own_source"))
    pts = "\n".join(f"- {s['heading']}: {'; '.join(s.get('bullets') or [])}" for s in plan["sections"])
    sh = ", ".join(s["title"] for s in res["shorts"]) or "không có"
    try:
        seo = V.llm_json(gem, cfg, SEO_SYSTEM.format(brand=ic.get("brand", "Smart Penguin Insights")),
                         SEO_PROMPT.format(minutes=res["duration"] / 60, title=plan.get("title", ""), theme=plan.get("theme", ""),
                                           points=pts, shorts=sh,
                                           source_line="" if own else f"Nguồn ý tưởng: @{post.get('handle', '')}\n"))
    except Exception as ex:
        log(f"   ! SEO lỗi: {ex}")
        seo = {"yt_titles": [plan.get("title", "")], "yt_intro": plan.get("description", ""), "yt_tags": [], "hashtags": ["#crypto"]}
    chapters = "\n".join(f"{ts(t)} {name}" for t, name in res["chapters"])
    used = {x for k, v in (plan.get("images") or {}).items() for x in v}
    credits = "; ".join(dict.fromkeys(v for k, v in (plan.get("image_credits") or {}).items() if k in used and v))
    src = "\n".join(f"• @{p.get('handle', '')}: {p.get('url', '')}" for p in plan.get("posts") or [])
    desc = (seo.get("yt_intro", "") + "\n\n"
            + ("Trong video:\n" + "\n".join(f"✅ {x}" for x in seo.get("yt_takeaways", [])) + "\n\n" if seo.get("yt_takeaways") else "")
            + "⏱ Chương:\n" + chapters + "\n\n"
            + ("" if own else "📌 Source (ý tưởng gốc, đã diễn giải lại):\n" + src + "\n")
            + "📊 Dữ liệu thị trường: CoinGecko, alternative.me\n"
            + (f"🖼 Ảnh: {credits}\n" if credits else "")
            + "\n⚠️ Không phải lời khuyên đầu tư. Hãy tự nghiên cứu (DYOR) trước khi xuống tiền.\n"
            + "🐧 Smart Penguin Insights · @Trong0322\n\n" + " ".join(seo.get("hashtags", [])))
    seo["yt_description"] = desc[:4900]
    tags, n = [], 0
    for t in seo.get("yt_tags", []):
        if n + len(t) + 1 > 480:
            break
        tags.append(t)
        n += len(t) + 1
    seo["yt_tags"] = tags
    import insight_lab as L   # bỏ mọi dòng SEO nhắc đoạn ENA 95% (Trọng cấm)
    for k in ("yt_titles", "yt_takeaways", "yt_tags", "hashtags"):
        if isinstance(seo.get(k), list):
            seo[k] = [x for x in seo[k] if not L._banned(x)] or ([plan.get("title", "")] if k == "yt_titles" else [])
    for k in ("yt_intro", "pinned_comment", "keyword"):
        if isinstance(seo.get(k), str):
            seo[k] = L._scrub_text(seo[k])
    seo["shorts"] = [{kk: ("" if L._banned(vv) else vv) for kk, vv in sh.items()} for sh in seo.get("shorts") or [] if isinstance(sh, dict)]
    if L._banned(seo.get("yt_description", "")):
        seo["yt_description"] = "\n".join(l for l in seo["yt_description"].split("\n") if not L._banned(l) or "x.com/" in l)
    if own:
        seo = strip_source(seo, plan)
    return P.nodash(clean_tags(seo))


def clean_tags(seo: dict) -> dict:
    """Chuẩn hoá hashtag trong gói SEO: caption không chứa hashtag, danh sách không trùng, tối đa 5."""
    def uniq(xs, n):
        out, seen = [], set()
        for t in xs or []:
            t = str(t).strip()
            t = t if t.startswith("#") else "#" + t
            if t.lower() not in seen and len(t) > 1:
                seen.add(t.lower()); out.append(t)
        return out[:n]
    seo["hashtags"] = uniq(seo.get("hashtags"), 3)
    for sh in seo.get("shorts") or []:
        cap = sh.get("tiktok_caption") or ""
        sh["tiktok_hashtags"] = uniq(re.findall(r"#[\wÀ-ỹ]+", cap) + list(sh.get("tiktok_hashtags") or []), 5)
        sh["tiktok_caption"] = re.sub(r"\s*#[\wÀ-ỹ]+", "", cap).strip()
        yt = sh.get("yt_title") or ""
        sh["yt_title"] = (re.sub(r"\s*#[\wÀ-ỹ]+", "", yt).strip() + " #Shorts").strip()
    return seo


def strip_source(seo, plan: dict):
    """Xoá mọi nhắc tới tác giả/bài gốc (handle, link x.com) khỏi gói SEO: mô tả, caption, bình luận, tag."""
    keys = {k for p in plan.get("posts") or [] for k in (p.get("handle", ""), p.get("url", "")) if k}
    def bad(t: str) -> bool:
        return any(k.lower() in t.lower() for k in keys) or ("x.com/" in t and "Trong0322" not in t)
    def clean(x):
        if isinstance(x, dict):
            return {k: clean(v) for k, v in x.items()}
        if isinstance(x, list):
            return [clean(v) for v in x if not (isinstance(v, str) and bad(v))]
        if isinstance(x, str):
            return "\n".join(l for l in x.split("\n") if not bad(l) and "ý tưởng gốc" not in l.lower())
        return x
    return clean(seo)


# ---------------------------------------------------------------------------
# ảnh bìa
# ---------------------------------------------------------------------------
ICON_RULES = [("crack", r"bubble|bong bóng|vỡ|sập|crash|nổ"), ("down", r"giảm|lỗ|bán tháo|dump|rơi|mất"),
              ("up", r"tăng|pump|x\d|bùng nổ|đột phá"), ("hourglass", r"ngày|thời gian|chờ|sắp|khi nào|đếm ngược"),
              ("flame", r"nóng|hot|fomo|cháy"), ("scale", r"so sánh|cân|hay là|vs"), ("magnifier", r"bí mật|sự thật|soi|vì sao|tại sao|\?")]


def thumb_style(plan: dict, has_vs: bool, has_points: bool, has_stat: bool, has_before: bool = False) -> tuple[str, str]:
    """Trọng 26/11: ảnh bìa kiểu "viral sạch" (5 bố cục: stat, pill, vs, before, question).
    Chọn theo dữ liệu kịch bản, xoay vòng theo tiêu đề để 2 video liền nhau không giống nhau; kịch bản chỉ định được bằng thumb_style."""
    import hashlib
    text = " ".join(str(plan.get(k, "")) for k in ("thumb_text", "title", "theme")).lower()
    icon = plan.get("thumb_icon") or next((k for k, pat in ICON_RULES if re.search(pat, text)), "magnifier")
    if plan.get("thumb_style") in ("stat", "pill", "vs", "before", "question"):
        return plan["thumb_style"], icon
    if has_before:
        return "before", icon
    opts = (["vs", "question"] if has_vs else ["stat", "pill"] if has_stat and has_points
            else ["stat", "question"] if has_stat else ["question"])
    k = int(hashlib.md5(text.encode()).hexdigest(), 16) % len(opts)
    return opts[k], icon


def thumbnail(res: dict, out: Path) -> Path | None:
    plan = res["plan"]
    proj = next((s.get("project") for s in res["scenes"] if s.get("project") and s["project"].get("logo")), None)
    approved = bool(os.getenv("INSIGHT_SCRIPT", "").strip())   # kịch bản Trọng duyệt: dùng đúng chữ ảnh bìa đã duyệt
    stat = P.nodash(plan.get("thumb_stat", ""))[:12] if approved else R.real_number(V.en_money(plan.get("hook_stat", "")), plan.get("posts") or [])[:8]
    coins = (res.get("data") or {}).get("coins") or {}
    side = lambda x: {**x, "label": P.nodash(str(x.get("label", ""))), "value": P.nodash(V.en_money(str(x.get("value", "")))),
                      "logo": coins.get(str(x.get("logo", "")).upper(), {}).get("logo")} if isinstance(x, dict) and x.get("value") else None
    props = {"comp": "Thumb", "width": 1280, "height": 720,
             "text": P.nodash(V.en_money(plan.get("thumb_text") or plan.get("thumb") or plan.get("title", "")))[:48],
             "stat": stat, "accent": (proj or {}).get("color") or "#4F5BD5",
             "points": [P.nodash(x)[:28] for x in (plan.get("thumb_points") or [])][:3],
             "tag": P.nodash(str((plan.get("thumb_tag") or ""))), "kicker": P.nodash(str(plan.get("thumb_kicker") or ""))[:40],
             "vs": [v for v in (side(x) for x in (plan.get("thumb_vs") or [])[:2]) if v],
             "before": side(plan.get("thumb_before")), "after": side(plan.get("thumb_after")),
             "projectLogo": (proj or {}).get("logo"), "bg": None,
             "style": "", "icon": "none",
             "brand": (V.load_cfg().get("insight") or {}).get("brand", "Smart Penguin Insights")}
    if not (props["before"] and props["after"]):
        props["before"] = props["after"] = None
    props["style"], props["icon"] = thumb_style(plan, len(props["vs"]) >= 2, bool(props["points"]), bool(props["stat"]), bool(props["before"]))
    log(f"   Ảnh bìa: bố cục {props['style']}, hình dán {props['icon']}")
    try:
        R.run_remotion(props, out, frames="0")
        return out
    except Exception as ex:
        log(f"   ! ảnh bìa lỗi: {ex}")
        return None


# ---------------------------------------------------------------------------
# BOT REVIEW: AI xem khung hình + lời đọc → chấm điểm & gợi ý
# ---------------------------------------------------------------------------
REVIEW_PROMPT = """Bạn là biên tập viên YouTube/TikTok kỳ cựu mảng crypto (chuyên tối ưu giữ chân người xem).
Dưới đây là {n} khung hình trích đều từ video dài "{title}" ({minutes:.1f} phút, giọng {voice}, tốc độ ~{wpm} từ/phút)
và {ns} khung hình từ video ngắn 9:16. Lời đọc mở đầu: "{hook}".
Hãy review THẲNG THẮN, cụ thể, có thể làm được ngay ở lần dựng sau. Viết tiếng Việt dễ hiểu.
Trả JSON:
{{
  "score": điểm tổng 1-10 (số thập phân),
  "scores": {{"hook_3s": 1-10, "hinh_anh_ro_rang": 1-10, "mau_sac_brand": 1-10, "nhip_do": 1-10, "phu_de": 1-10,
              "du_lieu_lien_quan": 1-10, "thumbnail": 1-10, "short_9x16": 1-10}},
  "tot": ["2-3 điểm đang làm tốt"],
  "can_sua": ["3-6 việc cần sửa, mỗi việc nêu rõ ở đâu (giây/khung) và sửa thế nào"],
  "script_tips": ["2-3 mẹo cho LỜI ĐỌC lần sau (hook, độ dài, cách kể), sẽ được đưa thẳng vào hướng dẫn viết kịch bản"],
  "retention_risk": "đoạn nào dễ làm người xem bỏ đi và vì sao"
}}
SOÁT TRÌNH BÀY BẮT BUỘC (Trọng 23/11, lỗi nào cũng phải ghi vào can_sua, ghi rõ khung nào, và trừ điểm hinh_anh_ro_rang
xuống tối đa 6 nếu có dù chỉ 1 lỗi): chữ đè lên nhau; chữ tràn hoặc bị cắt mép; lỗi font (ô vuông, mất dấu tiếng Việt);
nhãn bị máy tự ngắt dòng giữa cụm (vd "lãi / 10%/năm"); 2 con số trong thẻ so sánh không thẳng hàng; nguồn số liệu viết liền
trong chú thích thay vì dòng nhỏ riêng; một từ mồ côi đứng một mình ở dòng cuối; chữ trên hình không khớp lời đọc lúc đó;
biểu đồ biến mất trước khi vẽ xong."""


def scene_changes(video: Path, thr: float = 0.06) -> int:
    """Số lần hình thay đổi rõ rệt (ffmpeg scene detection): thước đo nhịp độ khách quan."""
    try:
        r = subprocess.run(["ffmpeg", "-loglevel", "info", "-i", str(video), "-vf", f"scale=320:-2,select='gt(scene,{thr})',showinfo",
                            "-an", "-f", "null", "-"], capture_output=True, text=True, timeout=600)
        return r.stderr.count("pts_time:")
    except Exception:
        return 0


def frames_of(video: Path, n: int, w: int = 640) -> list[bytes]:
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                               capture_output=True, text=True).stdout or 1)
    out = []
    for k in range(n):
        t = 1.5 if k == 0 else dur * k / n
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                            "-vf", f"scale={w}:-2", "-f", "image2", "-c:v", "mjpeg", "-q:v", "5", "-"], capture_output=True)
        if r.stdout:
            out.append(r.stdout)
    return out


def claude_review_cli(prompt: str, imgs: list[tuple[str, bytes]]) -> dict:
    """Bot review bằng Claude qua gói Claude Pro (secret CLAUDE_CODE_OAUTH_TOKEN, chạy Claude Code không giao diện)."""
    import shutil
    import tempfile
    tok = re.sub(r"\s+", "", os.getenv("CLAUDE_CODE_OAUTH_TOKEN", ""))
    if not tok or not shutil.which("claude"):
        raise RuntimeError("chưa có CLAUDE_CODE_OAUTH_TOKEN hoặc chưa cài Claude Code")
    d = Path(tempfile.mkdtemp(prefix="review-"))
    names = []
    for label, b in imgs:
        (d / f"{label}.jpg").write_bytes(b)
        names.append(f"{label}.jpg")
    ask = (prompt + "\n\nCác khung hình nằm trong thư mục hiện tại: " + ", ".join(names)
           + ". Hãy dùng công cụ Read để XEM TỪNG ẢNH trước khi đánh giá. Cuối cùng chỉ in ra JSON hợp lệ, không thêm chữ nào khác.")
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
    model = (V.load_cfg().get("insight") or {}).get("review_model_cli", "sonnet")
    r = subprocess.run(["claude", "-p", ask, "--allowedTools", "Read", "--max-turns", "40", "--model", model,
                        "--output-format", "text"], cwd=d, env=env, capture_output=True, text=True, timeout=900)
    txt = r.stdout.strip()
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        raise RuntimeError(f"Claude không trả JSON: {(txt or r.stderr)[:300]}")
    return json.loads(m.group(0))


def claude_review(prompt: str, imgs: list[tuple[str, bytes]]) -> dict:
    """Bot review bằng Claude API (secret ANTHROPIC_API_KEY, tính phí theo lượt)."""
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("chưa có ANTHROPIC_API_KEY")
    content = []
    for label, b in imgs:
        content += [{"type": "text", "text": f"[{label}]"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                 "data": base64.b64encode(b).decode()}}]
    content.append({"type": "text", "text": prompt + "\nChỉ trả về JSON hợp lệ, không thêm chữ nào khác."})
    model = (V.load_cfg().get("insight") or {}).get("review_model", "claude-sonnet-5-5")
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=300, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model, "max_tokens": 2500, "messages": [{"role": "user", "content": content}]})
    if r.status_code != 200:
        raise RuntimeError(f"Claude HTTP {r.status_code}: {r.text[:300]}")
    txt = "".join(c.get("text", "") for c in r.json().get("content", []) if c.get("type") == "text")
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0) if m else txt)


def review(gem, cfg, res: dict, thumb: Path | None) -> dict:
    import insight_lab as L
    plan = res["plan"]
    words = sum(len(s["narration"].split()) for s in plan["sections"])
    wpm = int(words / max(1, res["duration"]) * 60 * 1.1)
    N = 18   # Trọng 22/11: review nhìn nhiều khung hơn, kèm giây + lời đang đọc, để chấm nhịp và dữ liệu cho đúng
    imgs = [(f"long_{i}", b) for i, b in enumerate(frames_of(res["long"], N))]
    dur = res["duration"]
    times = [1.5 if k == 0 else dur * k / N for k in range(N)]
    def said(t):
        for sc in res.get("scenes") or []:
            if sc["from"] <= t < sc["from"] + sc["dur"]:
                ws = [w["t"] for w in sc.get("words") or [] if abs(sc["from"] + w["s"] - t) < 2.5]
                return " ".join(ws)[:120]
        return ""
    timeline = "\n".join(f"- long_{k} ở giây {tt:.0f}: lời đọc \"{said(tt)}\"" for k, tt in enumerate(times))
    changes = scene_changes(res["long"])
    short_first = str(plan.get("format", "")).lower() == "short"   # Trọng 22/11: video ngắn chấm khác video dài
    for j, s in enumerate(res["shorts"][:2]):
        k = 10 if (short_first and j == 0) else 2
        imgs += [(f"short{j}_{i}", b) for i, b in enumerate(frames_of(s["path"], k, 540 if k > 2 else 360))]
    if thumb and thumb.exists():
        from PIL import Image
        import io
        im = Image.open(thumb).convert("RGB")
        im.thumbnail((640, 640))
        b = io.BytesIO()
        im.save(b, "JPEG", quality=80)
        imgs.append(("thumbnail", b.getvalue()))
    prompt = REVIEW_PROMPT.format(n=N, ns=len(imgs) - N, title=plan.get("title", ""), minutes=res["duration"] / 60,
                                  voice=res["voice"], wpm=wpm, hook=plan.get("hook", ""))
    prompt += (f"\n\nTHÔNG TIN THÊM (đo bằng máy): video đổi hình {changes} lần, tức khoảng {changes / max(1, dur / 60):.0f} lần mỗi phút "
               "(chuẩn kênh: từ 8 lần/phút là nhịp tốt). Khung hình chỉ là ảnh tĩnh nên hãy chấm nhịp độ dựa trên số lần đổi hình này "
               "và độ khác nhau giữa các khung, không chỉ dựa trên vài ảnh.\nLời đang đọc ở từng khung (để chấm dữ liệu có đúng ý lời đọc không):\n" + timeline)
    if plan.get("news"):   # Trọng 24/11: tin nóng chỉ giao short, bản 16:9 không dùng: đừng trừ điểm vì nó
        prompt += ("\n\nTIN NÓNG: chỉ short0 được giao cho người xem. BỎ QUA các khung long_* khi chấm và khi liệt kê can_sua.")
    if short_first:
        prompt += ("\n\nLƯU Ý QUAN TRỌNG: đây là video SHORT-FIRST. Sản phẩm chính là short0 (10 khung short0_*), video dài chỉ là bản phụ. "
                   "Chấm theo chuẩn video ngắn 9:16: hook 1 đến 2 giây, một ý chính, nhịp đổi hình 3 đến 6 giây, chữ đọc được trên điện thoại, "
                   "dưới 60 giây. KHÔNG trừ điểm vì video dài ngắn hơn 4 phút hay ít phần. Mục short_9x16 là mục nặng nhất, "
                   "các mục khác (hook, nhịp độ, phụ đề, dữ liệu) chấm chủ yếu trên short0.")
    for fn in (claude_review_cli, claude_review):   # ưu tiên Claude (gói Pro, rồi API), Gemini dự phòng
        try:
            rv = fn(prompt, imgs)
            rv["by"] = "Claude"
            return rv
        except Exception as ex:
            log(f"   ! review Claude ({fn.__name__}) chưa chạy được: {str(ex)[:200]}")
    log("   → dùng Gemini")
    try:
        return {**L.gem_vision(gem, cfg, prompt, imgs), "by": "Gemini"}
    except Exception as ex:
        log(f"   ! review lỗi: {ex}")
        return {}


def review_text(rv: dict) -> str:
    if not rv:
        return ""
    sc = rv.get("scores") or {}
    names = {"hook_3s": "Hook 3 giây đầu", "hinh_anh_ro_rang": "Hình rõ ràng", "mau_sac_brand": "Màu & brand",
             "nhip_do": "Nhịp độ", "phu_de": "Phụ đề", "du_lieu_lien_quan": "Dữ liệu đúng ý", "thumbnail": "Ảnh bìa",
             "short_9x16": "Video ngắn"}
    lines = [f"🧐 BOT REVIEW · điểm tổng {rv.get('score', '?')}/10", ""]
    lines += [f"• {names.get(k, k)}: {v}/10" for k, v in sc.items()]
    if rv.get("tot"):
        lines += ["", "👍 Đang tốt:"] + [f"• {x}" for x in rv["tot"]]
    if rv.get("can_sua"):
        lines += ["", "🔧 Nên sửa:"] + [f"{i + 1}. {x}" for i, x in enumerate(rv["can_sua"])]
    if rv.get("retention_risk"):
        lines += ["", "⚠️ Dễ mất người xem: " + rv["retention_risk"]]
    if rv.get("script_tips"):
        lines += ["", "✍️ Mẹo kịch bản:"] + [f"• {x}" for x in rv["script_tips"]]
    return P.nodash("\n".join(lines))


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
def _tg():
    t, c = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    return (f"https://api.telegram.org/bot{t}", c) if t and c else (None, None)


def tg_text(text: str):
    api, chat = _tg()
    if not api:
        return
    for i in range(0, len(text), 3900):
        requests.post(f"{api}/sendMessage", timeout=60, data={"chat_id": chat, "text": text[i:i + 3900],
                                                              "disable_web_page_preview": "true"})


def tg_video(path: Path, caption: str):
    api, chat = _tg()
    if not api:
        return
    if path.stat().st_size > 48_000_000:
        small = path.with_name(path.stem + "-preview.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-vf", "scale=-2:720", "-c:v", "libx264",
                        "-crf", "27", "-preset", "veryfast", "-c:a", "aac", "-b:a", "128k", str(small)], check=True)
        path, caption = small, caption + "\n(bản xem trước 720p · bản gốc 1080p ở GitHub Release)"
    with open(path, "rb") as f:
        r = requests.post(f"{api}/sendVideo", timeout=600, data={"chat_id": chat, "caption": caption[:1000],
                                                                 "supports_streaming": "true"},
                          files={"video": (path.name, f, "video/mp4")})
    if not r.ok:
        log(f"   ! Telegram sendVideo lỗi: {r.text[:200]}")


def _photo_jpg(path: Path) -> Path:
    """Trọng 24/11: ảnh bìa PNG ~1MB bị Telegram Desktop kẹt ở ô mờ không tải được.
    Gửi bản JPEG (nhẹ khoảng 5 đến 10 lần) cho Telegram; file PNG gốc vẫn giữ trong release để đăng."""
    try:
        if path.suffix.lower() == ".png" and path.stat().st_size > 300_000:
            from PIL import Image
            out = path.with_name(path.stem + "-tg.jpg")
            Image.open(path).convert("RGB").save(out, "JPEG", quality=90, optimize=True, progressive=True)
            return out
    except Exception as e:
        log(f"   ! đổi ảnh sang JPEG lỗi, gửi bản gốc: {e}")
    return path


def tg_photo(path: Path, caption: str):
    api, chat = _tg()
    if api and path and path.exists():
        path = _photo_jpg(path)
        for i in range(3):
            try:
                with open(path, "rb") as f:
                    r = requests.post(f"{api}/sendPhoto", timeout=120, data={"chat_id": chat, "caption": caption[:1000]}, files={"photo": f})
                if r.ok:
                    return
                log(f"   ! Telegram sendPhoto lỗi: {r.text[:200]}")
            except Exception as e:
                log(f"   ! Telegram sendPhoto lỗi mạng (lần {i+1}): {e}")
            time.sleep(5 * (i + 1))


# ---------------------------------------------------------------------------
def review_avg(gem, cfg, res: dict, thumb: Path | None, n: int = 2) -> dict:
    """Chấm n lần rồi lấy trung bình (Trọng 23/11: điểm 1 lần chấm lệch ±0,5 đến 1, nháp 6.8 → chính 6.6 là do nhiễu một phần).
    Góp ý lấy từ lần chấm khắt khe hơn (điểm thấp hơn) để không bỏ sót lỗi."""
    runs = [r for r in (review(gem, cfg, res, thumb) for _ in range(n)) if r and r.get("scores")]
    if not runs:
        return {}
    base = dict(min(runs, key=lambda r: float(r.get("score") or 0)))
    keys = {k for r in runs for k in r["scores"]}
    base["scores"] = {k: round(sum(float(r["scores"].get(k, 0)) for r in runs if k in r["scores"])
                               / max(1, sum(1 for r in runs if k in r["scores"])) * 2) / 2 for k in keys}
    base["score"] = round(sum(float(r.get("score") or 0) for r in runs) / len(runs), 2)
    base["runs"] = [r.get("score") for r in runs]
    return base


def review_draft(lab: Path, res: dict, out: Path, label: str = "Bản nháp") -> dict:
    """Chấm một bản dựng: chỉ chấm, KHÔNG tạo Release, KHÔNG gửi Telegram, KHÔNG đăng."""
    cfg = V.load_cfg()
    gem = P.Gemini(os.getenv("INSIGHT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", ""))
    thumb = thumbnail(res, out / f"thumbnail-{lab.name}-cham.png")
    log(f"⑧ Bot review {label.lower()} (chấm 2 lần lấy trung bình)")
    rv = review_avg(gem, cfg, res, thumb) or {}
    log(f"   {label}: {rv.get('score')} điểm (các lần chấm {rv.get('runs')}) {rv.get('scores')}")
    return rv


def publish(lab: Path, res: dict, out: Path, data_dir: Path | None = None, draft: dict | None = None, rv: dict | None = None,
            gate: list | None = None) -> dict:
    cfg = V.load_cfg()
    gem = P.Gemini(os.getenv("INSIGHT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", ""))
    tag = lab.name
    thumb = thumbnail(res, out / f"thumbnail-{tag}.png")
    log("⑥ Gói SEO")
    seo = seo_pack(gem, cfg, res)
    if os.getenv("INSIGHT_SCRIPT", "").strip() and res["plan"].get("title"):   # tiêu đề Trọng duyệt luôn đứng đầu
        seo["yt_titles"] = [res["plan"]["title"]] + [t for t in seo.get("yt_titles", []) if t != res["plan"]["title"]][:2]
    (out / f"seo-{tag}.json").write_text(json.dumps(seo, ensure_ascii=False, indent=1), encoding="utf-8")
    import short_covers as SC   # Trọng 21/11: mỗi short có ảnh bìa riêng
    lg = {k: v.get("logo") for k, v in ((res.get("data") or {}).get("coins") or {}).items()}
    covers = [SC.make(res["plan"], s["section"], s["title"], out / f"short{j + 1}-cover-{tag}.png", lg) for j, s in enumerate(res["shorts"])]
    for s, c in zip(res["shorts"], covers):
        s["cover"] = str(c) if c else None
    files = [res["long"]] + [s["path"] for s in res["shorts"]] + ([thumb] if thumb else []) + [c for c in covers if c] + [out / f"seo-{tag}.json"]
    if draft and draft.get("long") and Path(draft["long"]).exists():   # Trọng 22/11: bản nháp cũng là bản dựng thật, lưu kèm để tải về
        nh = out / f"smart-penguin-{tag}-nhap-haidang-16x9.mp4"
        shutil.copy(draft["long"], nh)
        files.append(nh)
        for j, sp in enumerate(draft.get("shorts") or []):
            if Path(sp).exists():
                q = out / f"smart-penguin-{tag}-nhap-haidang-short{j + 1}-9x16.mp4"
                shutil.copy(sp, q)
                files.append(q)
    url = ""
    repo = os.getenv("GITHUB_REPOSITORY")
    if repo and os.getenv("GH_TOKEN"):
        rt = f"insight-{tag}"
        subprocess.run(["gh", "release", "delete", rt, "-y", "--cleanup-tag", "-R", repo], capture_output=True)
        subprocess.run(["gh", "release", "create", rt, *map(str, files), "-R", repo, "--title",
                        (seo.get("yt_titles") or [res["plan"].get("title", "")])[0], "--notes", seo["yt_description"]], check=True)
        url = f"https://github.com/{repo}/releases/tag/{rt}"
    log("⑦ Gửi Telegram")
    plan = res["plan"]
    if plan.get("news"):   # Trọng 23/11: tin nóng chỉ có short (giọng Hải Đăng), gửi gọn để duyệt, không tự đăng
        return publish_news(gem, cfg, res, seo, covers, url, data_dir, tag, rv)
    tg_text(f"🐧 SMART PENGUIN INSIGHTS · video mới ({res['duration'] / 60:.1f} phút · giọng {res['voice'].split(':')[1]})\n"
            f"1 video YouTube 16:9 + {len(res['shorts'])} video ngắn 9:16 (TikTok/Shorts/Reels)\n" + (f"📦 File gốc: {url}" if url else ""))
    tg_photo(thumb, "🖼 Ảnh bìa YouTube")
    for j, c in enumerate(covers):
        if c:
            tg_photo(c, f"🖼 Ảnh bìa Short {j + 1}")
    tg_video(res["long"], "🎬 " + (seo.get("yt_titles") or [plan.get("title", "")])[0])
    for i, s in enumerate(res["shorts"]):
        sh = (seo.get("shorts") or [{}] * 9)[i] if i < len(seo.get("shorts") or []) else {}
        tg_video(s["path"], f"📱 Short {i + 1}: {sh.get('yt_title') or s['title']}")
    if preflight_text(res):
        tg_text(preflight_text(res))
    if draft and not draft.get("sent") and draft.get("long") and Path(draft["long"]).exists():   # Trọng 22/11: gửi cả bản nháp (24/11: đã gửi ngay sau lượt 1 thì thôi)
        drv = draft.get("review") or {}
        tg_video(Path(draft["long"]), f"🧪 Bản NHÁP (giọng {draft.get('voice', 'Hải Đăng')}, trước khi bot sửa): {drv.get('score', '?')} điểm")
        if draft.get("changes"):
            msg = "🛠 BOT XỬ LÝ TỪNG GÓP Ý CỦA BẢN NHÁP:\n\n" + "\n".join(draft["changes"])
            for k in range(0, len(msg), 3800):
                tg_text(msg[k:k + 3800])
    yt = ("📺 YOUTUBE: copy dán khi đăng\n\nTIÊU ĐỀ (chọn 1):\n" + "\n".join(f"{i + 1}. {t}" for i, t in enumerate(seo.get("yt_titles", [])))
          + "\n\nMÔ TẢ:\n" + seo["yt_description"] + "\n\nTAGS:\n" + ", ".join(seo.get("yt_tags", []))
          + ("\n\nBÌNH LUẬN GHIM:\n" + seo["pinned_comment"] if seo.get("pinned_comment") else ""))
    tg_text(yt)
    if seo.get("shorts"):
        tk = ["🎵 TIKTOK / SHORTS: caption từng video ngắn"]
        for i, sh in enumerate(seo["shorts"][: len(res["shorts"])]):
            tk += ["", f"Short {i + 1}", f"Shorts title: {sh.get('yt_title', '')}",
                   f"TikTok: {with_tags(sh.get('tiktok_caption', ''), sh.get('tiktok_hashtags', []))}"]
        tg_text("\n".join(tk))
    try:   # đăng tự động (chỉ chạy khi SOCIAL_AUTOPOST=1 và có key), xem docs/social-setup.md
        import social_upload as SU
        posted = SU.run(res, seo, thumb)
        if posted:
            tg_text("📤 ĐĂNG TỰ ĐỘNG\n" + "\n".join(posted))
    except Exception as ex:
        log(f"   ! đăng tự động lỗi: {ex}")
    if not rv:
        log("⑧ Bot review")
        rv = review_avg(gem, cfg, res, thumb)
    if gate:   # các lượt chấm của cửa chặn chất lượng
        tg_text("🚦 CỬA CHẶN CHẤT LƯỢNG (bản chính không được thua bản nháp)\n" + "\n".join(gate))
    if rv:
        tg_text(review_text(rv))
        if draft and (draft.get("review") or {}).get("scores"):
            a, b = draft["review"]["scores"], rv.get("scores") or {}
            tg_text("📊 SO SÁNH nháp → bản chính\n" + f"Tổng: {draft['review'].get('score')} → {rv.get('score')}\n"
                    + "\n".join(f"{k}: {a.get(k)} → {b.get(k)}" for k in b))
        if data_dir:  # lưu lại để lần sau viết kịch bản rút kinh nghiệm
            p = data_dir / "insight" / "reviews.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            arr = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
            arr.append({"tag": tag, "at": datetime.now(P.VN_TZ).isoformat(timespec="minutes"), **rv})
            p.write_text(json.dumps(arr[-30:], ensure_ascii=False, indent=1), encoding="utf-8")
            try:   # cập nhật file bài học cho video sau
                import insight_lessons as LS
                LS.build(data_dir)
            except Exception as ex:
                log(f"   ! cập nhật bài học lỗi: {ex}")
    return {"release": url, "seo": seo, "review": rv, "thumb": str(thumb) if thumb else None}


def publish_news(gem, cfg, res, seo, covers, url, data_dir, tag, rv0: dict | None = None) -> dict:
    """Tin nóng (news_flash.py): chỉ gửi short 9:16 + caption + bot review, KHÔNG đăng tự động."""
    plan = res["plan"]
    tg_text(f"⚡ TIN NÓNG · short đã dựng xong (giọng {res['voice'].split(':')[-1]})\n{plan.get('title', '')}\n"
            + (f"📦 File gốc: {url}" if url else "") + "\nXem rồi đăng tay nếu ổn nhé.")
    for j, s in enumerate(res["shorts"]):
        if j < len(covers) and covers[j]:
            tg_photo(covers[j], f"🖼 Ảnh bìa short {j + 1}")
        sh = (seo.get("shorts") or [{}])[j] if j < len(seo.get("shorts") or []) else {}
        tg_video(s["path"], f"📱 {sh.get('yt_title') or s['title']}")
    if seo.get("shorts"):
        sh = seo["shorts"][0]
        tg_text("🎵 CAPTION copy dán khi đăng\n\n"
                f"Shorts title: {sh.get('yt_title', '')}\n\n"
                f"TikTok/Reels: {with_tags(sh.get('tiktok_caption', ''), sh.get('tiktok_hashtags', []))}")
    if preflight_text(res):
        tg_text(preflight_text(res))
    log("⑧ Bot review")
    rv = rv0 or review(gem, cfg, res, None)   # news_flash.build đã review (và tự sửa) rồi thì dùng luôn
    if len(res.get("review_rounds") or []) > 1:
        tg_text("🔁 Bot tự sửa theo review rồi dựng lại: điểm " + " → ".join(str(x) for x in res["review_rounds"]))
    if rv:
        tg_text(review_text(rv))
        if data_dir:   # lưu riêng, không trộn vào bài học của video insight dài
            p = data_dir / "insight" / "news-reviews.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            arr = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
            arr.append({"tag": tag, "at": datetime.now(P.VN_TZ).isoformat(timespec="minutes"), **rv})
            p.write_text(json.dumps(arr[-30:], ensure_ascii=False, indent=1), encoding="utf-8")
    return {"release": url, "seo": seo, "review": rv, "thumb": None}

def preflight_text(res: dict) -> str:
    """Báo kết quả soát hình trước khi dựng (preflight.py) cho Trọng."""
    rows = []
    for j, s in enumerate(res.get("shorts") or []):
        pre = s.get("preflight") or {}
        if pre.get("skipped") or pre.get("ok") is None and not pre.get("error"):
            continue
        sc = (f" · điểm dự kiến {pre.get('score_before')} → {pre.get('score')}" if pre.get("score_before") is not None else "")
        if pre.get("ok"):
            rows.append(f"Short {j + 1}: ổn sau {pre.get('rounds', 1)} vòng{sc}")
        else:
            rows.append(f"Short {j + 1}: còn {len(pre.get('issues') or [])} lỗi sau {pre.get('rounds', 0)} vòng{sc}"
                        + "".join(f"\n  • {x.get('problem', '')}" for x in (pre.get("issues") or [])[:5])
                        + (f"\n  (soát lỗi: {pre['error']})" if pre.get("error") else ""))
    return ("🔎 Bot review xem trước (trước khi dựng)\n" + "\n".join(rows)) if rows else ""
