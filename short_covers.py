"""Ảnh bìa cho video ngắn 9:16 (Trọng 21/11: "short cũng phải có ảnh bìa").

Trong quy trình dựng: insight_publish gọi make(...) cho mỗi short, ảnh lên Release + Telegram.
Dùng tay cho video đã dựng:  python short_covers.py <tag> <scripts/...-approved.json> [fb_reel_id1,fb_reel_id2]
  → vẽ ảnh bìa từng short, gắn vào Release, gửi Telegram, và nếu có id Reel Facebook thì đặt làm ảnh bìa Reel.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import podcast as P
import video as V

ROOT = Path(__file__).resolve().parent


def _icon(title: str) -> str:
    import re
    import insight_publish as IP
    t = title.lower()
    if re.search(r"rác|tránh|bẫy|cảnh báo|sai lầm", t):
        return "down"
    return next((k for k, pat in IP.ICON_RULES if re.search(pat, t)), "magnifier")


def props_for(plan: dict, sec_idx: int, title: str, logos: dict | None = None) -> dict:
    s = plan["sections"][sec_idx]
    up = title.upper()
    # bảng so sánh của ảnh bìa YouTube: chỉ dùng khi tiêu đề short nhắc đủ các coin trong đó
    vs = [{**x, "logo": (logos or {}).get(str(x.get("logo", "")).upper())} for x in (plan.get("thumb_vs") or [])
          if str(x.get("label", "")).upper() in up]
    if len(vs) < 2:
        vs = []
    return {"comp": "ShortThumb", "width": 1080, "height": 1920,
            "text": P.nodash(V.en_money(title))[:60],
            "stat": "" if vs else P.nodash(V.en_money(s.get("key_stat", "")))[:10],
            "vs": vs,
            "icon": _icon(title),
            "label": P.nodash(V.en_money(s.get("key_label", "")))[:40],
            # chỉ hiện ý liệt kê khi kịch bản ghi riêng cho ảnh bìa (bullet của phần thường không khớp tiêu đề short)
            "points": [P.nodash(V.en_money(b))[:34] for b in ((plan.get("short_cover_points") or {}).get(str(sec_idx)) or [])][:3],
            "accent": "#4F5BD5", "projectLogo": None,
            "brand": (V.load_cfg().get("insight") or {}).get("brand", "Smart Penguin Insights")}


def make(plan: dict, sec_idx: int, title: str, out: Path, logos: dict | None = None) -> Path | None:
    import insight_render as R
    try:
        R.run_remotion(props_for(plan, sec_idx, title, logos), out, frames="0")
        return out
    except Exception as ex:
        P.log(f"   ! ảnh bìa short lỗi: {ex}")
        return None


def fb_set_thumb(video_id: str, img: Path) -> str:
    import requests
    import social_upload as SU
    with open(img, "rb") as fh:
        r = requests.post(f"https://graph.facebook.com/{SU.FB_VER}/{video_id}/thumbnails",
                          params={"access_token": os.environ["FB_PAGE_TOKEN"].strip(), "is_preferred": "true"},
                          files={"source": (img.name, fh, "image/png")}, timeout=120)
    return f"{r.status_code} {r.text[:200]}"


def main(tag: str, script: str, fb_ids: str = ""):
    plan = json.loads(Path(script).read_text(encoding="utf-8"))
    hooks = {int(k): v for k, v in (plan.get("short_hooks") or {}).items()}
    out = Path("covers"); out.mkdir(exist_ok=True)
    import insight_render as R
    lab = Path("lab_empty"); (lab / "logos").mkdir(parents=True, exist_ok=True)
    logos = {}
    for x in plan.get("thumb_vs") or []:   # logo coin cho bảng so sánh
        t = str(x.get("logo", "")).upper()
        try:
            info = V.coin_info(t) if t else None
            if info and info.get("large"):
                import requests
                (lab / "logos" / f"{t}.png").write_bytes(requests.get(info["large"], timeout=30).content)
                logos[t] = f"logos/{t}.png"
        except Exception as ex:
            print("logo lỗi", t, ex)
    R.prep_public(lab)   # phông chữ + logo kênh cho Remotion
    files = []
    for j, i in enumerate(plan.get("shorts", [])[:2]):
        title = hooks.get(i) or plan["sections"][i]["heading"]
        f = out / f"short{j + 1}-cover-{tag}.png"
        import insight_render as R
        R.run_remotion(props_for(plan, i, title, logos), f, frames="0")
        files.append(f)
        print("ảnh bìa", f, "|", title)
    repo = os.getenv("GITHUB_REPOSITORY")
    if repo:
        subprocess.run(["gh", "release", "upload", f"insight-{tag}", *map(str, files), "--clobber", "-R", repo], check=True)
        print("đã gắn vào Release insight-" + tag)
    import insight_publish as IP
    for j, f in enumerate(files):
        IP.tg_photo(f, f"🖼 Ảnh bìa Short {j + 1} (Reels/Shorts/TikTok)")
    for j, vid in enumerate([x.strip() for x in fb_ids.split(",") if x.strip()]):
        if j < len(files):
            print(f"Facebook ảnh bìa Reel {vid}:", fb_set_thumb(vid, files[j]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
