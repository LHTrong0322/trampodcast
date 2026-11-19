"""Gửi các file video/ảnh của 1 GitHub Release vào Telegram (để xem trước).
python tg_send_release.py <tag>   — chú thích lấy từ captions.json trong release (nếu có)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

tag = sys.argv[1]
src = sys.argv[2] if len(sys.argv) > 2 else ""
repo = os.environ["GITHUB_REPOSITORY"]
if src:  # thư mục file dựng sẵn (từ nhánh lab-renders) → tạo Release rồi gửi
    d = Path(src)
    caps0 = json.loads((d / "captions.json").read_text(encoding="utf-8")) if (d / "captions.json").exists() else {}
    files = [str(p) for p in sorted(d.iterdir()) if p.is_file()]
    subprocess.run(["gh", "release", "delete", tag, "-y", "--cleanup-tag", "-R", repo], capture_output=True)
    subprocess.run(["gh", "release", "create", tag, *files, "-R", repo, "--title", caps0.get("_title", tag),
                    "--notes", caps0.get("_notes", "")], check=True)
else:
    d = Path("rel")
    d.mkdir(exist_ok=True)
    subprocess.run(["gh", "release", "download", tag, "-R", repo, "-D", str(d), "--clobber"], check=True)
caps = json.loads((d / "captions.json").read_text(encoding="utf-8")) if (d / "captions.json").exists() else {}
token, chat = os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]
api = f"https://api.telegram.org/bot{token}"
order = caps.get("_order") or sorted(p.name for p in d.iterdir())
for name in order:
    p = d / name
    if not p.exists() or p.suffix not in (".mp4", ".png", ".jpg"):
        continue
    cap = caps.get(name, name)[:1000]
    if p.suffix == ".mp4":
        if p.stat().st_size > 48e6:
            small = p.with_name(p.stem + "-720p.mp4")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(p), "-vf", "scale=-2:720", "-c:v", "libx264",
                            "-crf", "28", "-preset", "veryfast", "-c:a", "aac", "-b:a", "96k", str(small)], check=True)
            p = small
            cap += "\n(bản xem trước 720p · bản gốc 1080p ở GitHub Release)"
        with open(p, "rb") as f:
            r = requests.post(f"{api}/sendVideo", data={"chat_id": chat, "caption": cap, "supports_streaming": "true"},
                              files={"video": (p.name, f, "video/mp4")}, timeout=600)
    else:
        with open(p, "rb") as f:
            r = requests.post(f"{api}/sendPhoto", data={"chat_id": chat, "caption": cap}, files={"photo": f}, timeout=120)
    print(name, r.status_code, r.text[:200] if not r.ok else "")
if caps.get("_message"):
    requests.post(f"{api}/sendMessage", data={"chat_id": chat, "text": caps["_message"][:3900]}, timeout=60)
