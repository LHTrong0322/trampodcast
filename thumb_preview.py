"""Vẽ thử ảnh bìa YouTube với nhiều phông để Trọng chọn (không dựng video, không tốn lượt Gemini).
python thumb_preview.py scripts/<ten>-approved.json anton,barlow,archivo,montserrat,bvp
"""
import json
import sys
from pathlib import Path

import requests

import insight_publish as IP
import insight_render as R
import video as V
import podcast as P


def main(script: str, fonts: str):
    plan = json.loads(Path(script).read_text(encoding="utf-8"))
    lab = Path("lab_thumb"); (lab / "logos").mkdir(parents=True, exist_ok=True)
    logos = {}
    for x in plan.get("thumb_vs") or []:
        t = str(x.get("logo", "")).upper()
        info = V.coin_info(t) if t else None
        if info and info.get("large"):
            (lab / "logos" / f"{t}.png").write_bytes(requests.get(info["large"], timeout=30).content)
            logos[t] = f"logos/{t}.png"
    R.prep_public(lab)
    out = Path("thumbs"); out.mkdir(exist_ok=True)
    for f in [x.strip() for x in fonts.split(",") if x.strip()]:
        props = {"comp": "Thumb", "width": 1280, "height": 720, "text": plan.get("thumb_text") or plan.get("title", ""),
                 "stat": plan.get("thumb_stat", ""), "accent": "#4F5BD5", "points": plan.get("thumb_points") or [],
                 "warn": False, "projectLogo": None, "bg": None, "brand": "Smart Penguin Insights", "font": f,
                 "tag": P.nodash(str((plan.get("thumb_tag") or ""))), "vs": [{**x, "logo": logos.get(str(x.get("logo", "")).upper())} for x in (plan.get("thumb_vs") or [])]}
        p = out / f"thumb-{f}.png"
        R.run_remotion(props, p, frames="0")
        IP.tg_photo(p, f"🖼 Ảnh bìa thử phông: {f}")
        print("đã vẽ", p)
    import os, subprocess
    repo = os.getenv("GITHUB_REPOSITORY")
    if repo:   # để kiểm tra từ xa (artifact bị chặn): đưa lên Release "thumb-preview"
        subprocess.run(["gh", "release", "create", "thumb-preview", "-R", repo, "--title", "Ảnh bìa thử", "--notes", "Ảnh bìa vẽ thử"], capture_output=True)
        subprocess.run(["gh", "release", "upload", "thumb-preview", *map(str, out.glob("*.png")), "--clobber", "-R", repo], check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "anton,barlow,archivo,montserrat,bvp")
