"""Vẽ lại ảnh bìa kiểu "viral sạch" cho video ĐÃ DỰNG (không dựng lại video):
ảnh bìa YouTube 16:9 -> scripts/posts/thumbs/<tag>.png, ảnh bìa mọi short 9:16 -> assets/posts/<tag>/shortN-cover.jpg.
python rethumb.py <tag> <scripts/...-approved.json>     (Trọng 27/11: video chưa có ảnh bìa mới thì cook lại)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from PIL import Image

import insight_publish as IP
import insight_render as R
import insight_lab as L
import short_covers as SC
import video as V


def main(tag: str, script: str):
    plan = json.loads(Path(script).read_text(encoding="utf-8"))
    lab = Path("lab_rethumb"); (lab / "logos").mkdir(parents=True, exist_ok=True)
    tickers = {str(plan.get("thumb_logo") or "").lstrip("$").upper()} | {str(x.get("logo", "")).upper() for x in plan.get("thumb_vs") or []}
    coins, logos = {}, {}
    for t in sorted(x for x in tickers if x):
        info = V.coin_info(t)
        if info and info.get("large"):
            p = lab / "logos" / f"{t}.png"
            p.write_bytes(requests.get(info["large"], timeout=30).content)
            logos[t] = f"logos/{t}.png"
            coins[t] = {"name": info.get("name", t), "logo": logos[t], "color": L.BRAND_OVERRIDE.get(t) or L.brand_color(p)}
    R.prep_public(lab)
    os.environ["INSIGHT_SCRIPT"] = script   # dùng đúng chữ ảnh bìa trong kịch bản đã duyệt
    out = Path("scripts/posts/thumbs") / f"{tag}.png"
    IP.thumbnail({"plan": plan, "data": {"coins": coins}, "scenes": []}, out)
    print("ảnh bìa dài", out)
    hooks = {int(k): v for k, v in (plan.get("short_hooks") or {}).items()}
    d = Path("assets/posts") / tag; d.mkdir(parents=True, exist_ok=True)
    files = [out]
    for j, i in enumerate(plan.get("shorts", [])):
        title = hooks.get(i) or plan["sections"][i]["heading"]
        png = Path("covers") / f"short{j + 1}.png"
        R.run_remotion(SC.props_for(plan, i, title, logos), png, frames="0")
        jpg = d / f"short{j + 1}-cover.jpg"
        Image.open(png).convert("RGB").save(jpg, quality=88)
        files.append(png)
        print("ảnh bìa short", j + 1, jpg, "|", title)
    for j, f in enumerate(files):
        IP.tg_photo(f, "🖼 Ảnh bìa mới: " + ("video dài" if j == 0 else f"Short {j}") + f" ({tag})")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
