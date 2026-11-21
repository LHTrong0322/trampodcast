"""Làm đẹp giọng sau khi đọc (miễn phí, không tốn lượt Gemini): nhanh hơn nhưng giữ cao độ,
lọc ù, bớt rè chữ s, thêm độ sáng, nén cho giọng dày và đều như thu ở studio.

Lấy mẫu B (Ludo có chỉ dẫn) từ lần chạy voice-ab gần nhất, xuất 2 bản:
H: nhanh hơn 8 phần trăm + làm đẹp giọng
I: nhanh hơn 12 phần trăm + làm đẹp giọng
"""
import io
import os
import subprocess
import zipfile
from pathlib import Path

import requests

import voice_samples as VS

REPO = os.getenv("GITHUB_REPOSITORY", "LHTrong0322/trampodcast")
H = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN', '')}", "Accept": "application/vnd.github+json"}

# chuỗi xử lý giọng: lọc ù dưới 80Hz, bớt đục 250Hz, sáng giọng 3.5kHz, bớt xì chữ s, nén nhẹ, chuẩn âm lượng YouTube
CHAIN = ("highpass=f=80,equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3500:t=q:w=1.0:g=2.5,"
         "equalizer=f=9000:t=h:w=2000:g=1.5,deesser=i=0.35,"
         "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,"
         "atempo={tempo},loudnorm=I=-14:TP=-1.0:LRA=7")


def fetch_b() -> Path:
    runs = requests.get(f"https://api.github.com/repos/{REPO}/actions/workflows/voice-ab.yml/runs",
                        params={"status": "success", "per_page": 1}, headers=H, timeout=60).json()["workflow_runs"]
    arts = requests.get(runs[0]["artifacts_url"], headers=H, timeout=60).json()["artifacts"]
    z = requests.get(arts[0]["archive_download_url"], headers=H, timeout=120)
    out = Path("samples"); out.mkdir(exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(z.content)) as zf:
        zf.extract("B-ludo.mp3", out)
    return out / "B-ludo.mp3"


def main():
    src = fetch_b()
    VS.WORDS[0] = 117
    for code, tempo, label in (("H", 1.08, "Ludo B, nhanh hơn 8 phần trăm + làm đẹp giọng"),
                               ("I", 1.12, "Ludo B, nhanh hơn 12 phần trăm + làm đẹp giọng")):
        dst = Path("samples") / f"{code}-ludo.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af", CHAIN.format(tempo=tempo),
                        "-ar", "48000", "-b:a", "160k", str(dst)], check=True)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    str(dst)], capture_output=True, text=True).stdout)
        print(code, f"{dur:.0f}s · {117 / dur * 60:.0f} từ/phút")
        VS.send(dst, f"{code}. {label}")


if __name__ == "__main__":
    main()
