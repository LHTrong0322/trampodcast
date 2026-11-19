"""Đọc thử 1 đoạn tin bằng nhiều giọng rồi gửi từng bản vào Telegram để chọn.

python voice_samples.py --vieneu "Hải Đăng,Minh Đức" --gemini "Charon,Orus"
"""
import argparse
import os
import subprocess
import tempfile
import time
from pathlib import Path

import requests

import podcast as P

TEXT = ("Chào mọi người, đây là bản tin crypto tuần này. "
        "Thị trường vừa trải qua một tuần đỏ lửa khi hơn sáu tỷ đô bị thanh lý chỉ trong bảy ngày. "
        "Bitcoin giảm mười ba phần trăm, trong khi CZ lên tiếng phủ nhận tin đồn Binance xả coin. "
        "Ở mảng vĩ mô, Fed phát tín hiệu có thể tăng lãi suất thêm nửa phần trăm vào tháng mười hai, "
        "tạo áp lực lên cả Bitcoin lẫn cổ phiếu công nghệ. "
        "Đây không phải lời khuyên đầu tư, mọi người nhớ tự nghiên cứu kỹ nhé.")

GEMINI_STYLE = "Đọc bằng giọng nam miền Bắc, giọng Hà Nội, trầm ấm, rõ ràng, nhịp vừa phải như người dẫn bản tin"


def stats(pcm: bytes, words: int) -> str:
    """Tốc độ đọc (từ/phút) và cao độ giọng trung bình (Hz) — để so sánh khách quan."""
    import numpy as np
    sr = P.SAMPLE_RATE
    x = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768
    dur = len(x) / sr
    f0 = []
    n = int(sr * 0.04)
    for i in range(0, len(x) - n, n):
        fr = x[i:i + n] - x[i:i + n].mean()
        if np.sqrt((fr ** 2).mean()) < 0.03:
            continue
        ac = np.correlate(fr, fr, "full")[n - 1:]
        lo, hi = sr // 300, sr // 70
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.4 * ac[0]:
            f0.append(sr / k)
    pitch = float(np.median(f0)) if f0 else 0
    return f"{dur:.0f}s · {words / dur * 60:.0f} từ/phút · cao độ ~{pitch:.0f}Hz"


def to_mp3(pcm: bytes, path: Path):
    pcm = P.clean_chunk(pcm)
    print("  ", stats(pcm, len(TEXT.split())))
    with tempfile.NamedTemporaryFile(suffix=".pcm", delete=False) as f:
        f.write(pcm)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(P.SAMPLE_RATE), "-ac", "1",
                    "-i", f.name, "-af", "loudnorm=I=-16:TP=-1.5", "-b:a", "96k", str(path)], check=True)


def send(path: Path, caption: str):
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print("  (không có Telegram secret, bỏ qua gửi)")
        return
    with open(path, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendAudio", timeout=120,
                          data={"chat_id": chat, "caption": caption, "title": caption},
                          files={"audio": (path.name, f, "audio/mpeg")})
    print("  Telegram:", r.status_code)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vieneu", default="")
    ap.add_argument("--gemini", default="")
    ap.add_argument("--text", default="")
    a = ap.parse_args()
    text = a.text.strip() or TEXT
    out = Path("samples"); out.mkdir(exist_ok=True)
    import yaml
    cfg = yaml.safe_load((P.ROOT / "sources.yaml").read_text(encoding="utf-8"))
    n = 0
    for v in [x.strip() for x in a.vieneu.split(",") if x.strip()]:
        n += 1
        print(f"VieNeu · {v}")
        try:
            p = out / f"{n:02d}-vieneu.mp3"
            to_mp3(P.vieneu_tts(text, v), p)
            send(p, f"{n}. VieNeu · {v} (miễn phí)")
        except Exception as ex:
            print("  lỗi:", ex)
    gvoices = [x.strip() for x in a.gemini.split(",") if x.strip()]
    if gvoices:
        gem = P.Gemini(os.getenv("GEMINI_API_KEY", ""))
        models = (cfg or {}).get("models", {}).get("tts") or ["gemini-3.8-flash-tts"]
        for i, v in enumerate(gvoices):
            n += 1
            print(f"Gemini · {v}")
            try:
                p = out / f"{n:02d}-gemini.mp3"
                to_mp3(gem.tts(models, v, GEMINI_STYLE, text), p)
                send(p, f"{n}. Gemini · {v} (giọng Hà Nội)")
            except Exception as ex:
                print("  lỗi:", ex)
            if i + 1 < len(gvoices):
                time.sleep(25)


if __name__ == "__main__":
    main()
