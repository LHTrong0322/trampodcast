"""Nhân bản giọng Mai Thảo và Mai Linh (đã đồng ý) bằng VieNeu (miễn phí, chạy trên máy GitHub).

Lấy tin nhắn giọng nói / file âm thanh mới nhất gửi cho bot Telegram,
dùng TOÀN BỘ bản thu làm giọng mẫu, đọc thử đoạn kịch bản mẫu (giống voice_ab.py) rồi gửi lại Telegram.
Không đổi offset của bot, nên không ảnh hưởng hộp thư lấy link của insight.
File giọng gốc không lưu vào repo.
"""
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import requests

import voice_ab as AB

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OWNER = str(os.getenv("TELEGRAM_CHAT_ID", "")).strip()
API = f"https://api.telegram.org/bot{TOKEN}"
OUT = Path("samples")
OUT.mkdir(exist_ok=True)


def latest_voices(n: int = 2):
    """n file giọng mới nhất, xếp theo thứ tự gửi (cũ trước, mới sau)."""
    res = requests.get(f"{API}/getUpdates", params={"timeout": 0}, timeout=60).json()
    found = []
    for up in res.get("result", []):
        m = up.get("message") or {}
        if str((m.get("chat") or {}).get("id")) != OWNER:
            continue
        doc = m.get("document") or {}
        f = (m.get("voice") or m.get("audio") or m.get("video_note") or m.get("video")
             or (doc if str(doc.get("mime_type", "")).startswith(("audio", "video")) else None))
        if f:
            found.append((m.get("date", 0), f["file_id"]))
    found.sort()
    return [fid for _, fid in found[-n:]]


def latest_voice():
    res = requests.get(f"{API}/getUpdates", params={"timeout": 0}, timeout=60).json()
    best = None
    for up in res.get("result", []):
        m = up.get("message") or {}
        if str((m.get("chat") or {}).get("id")) != OWNER:
            continue
        doc = m.get("document") or {}
        f = (m.get("voice") or m.get("audio") or m.get("video_note") or m.get("video")
             or (doc if str(doc.get("mime_type", "")).startswith(("audio", "video")) else None))
        if f:
            best = (m.get("date", 0), f["file_id"])
    return best[1] if best else None


def download(file_id: str) -> Path:
    path = requests.get(f"{API}/getFile", params={"file_id": file_id}, timeout=60).json()["result"]["file_path"]
    raw = OUT / ("ref_raw" + Path(path).suffix)
    ref = OUT / "ref.wav"
    raw.write_bytes(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{path}", timeout=120).content)
    ref = OUT / "ref.wav"
    # lấy TOÀN BỘ bản thu: bỏ các khoảng lặng dài, chuẩn âm lượng, mono 24kHz
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-ac", "1", "-ar", "24000",
                    "-af", "silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=-1:stop_duration=0.6:"
                    "stop_threshold=-45dB,highpass=f=70,loudnorm=I=-18", str(ref)], check=True)
    raw.unlink()
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(ref)], capture_output=True, text=True).stdout.strip() or 0)
    print(f"Giọng mẫu: {dur:.1f} giây")
    return ref


VOICE_NAMES = ["Mai Thảo", "Mai Linh"]  # theo thứ tự gửi: giọng gửi trước, giọng gửi sau
VOICE_NAME = ""
DEMO = ("Chào buổi sáng cả nhà, đây là Trạm Podcast Crypto."
        "Tin nóng nhất sáng nay: Bitcoin tiếp tục lao dốc, có lúc chạm năm mươi lăm nghìn một trăm linh sáu đô trên sàn Coinbase, "
        "mức thấp nhất kể từ tháng chín năm hai nghìn không trăm hai mươi bốn."
        "Chỉ trong hai mươi bốn giờ, gần ba trăm bốn mươi bốn nghìn trader bị thanh lý, tổng giá trị khoảng hai phẩy ba tám tỷ đô, "
        "và hơn chín mươi hai phần trăm trong số đó là lệnh long."
        "Theo Arthur Hayes, crypto đang bị bán ra đầu tiên để bù margin call cho các khoản lỗ từ cổ phiếu công nghệ, "
        "khi thị trường chuyển sang trạng thái risk-off."
        "Điều cần để ý: thanh lý dây chuyền có thể tiếp tục gây áp lực giảm giá ngắn hạn, "
        "nên cả nhà hạn chế dùng đòn bẩy cao trong giai đoạn này nhé.")

WIN = 8.0  # VieNeu chỉ nhận tối đa 8 giây mỗi lần tham chiếu


def enroll_full(tts, ref: Path) -> dict:
    """Dùng hết bản thu: cắt thành các đoạn 8 giây, lấy đặc trưng giọng của MỌI đoạn rồi gộp trung bình
    (chất giọng), chọn đoạn gần giọng trung bình nhất làm mẫu nhịp đọc."""
    import soundfile as sf
    wav, sr = sf.read(str(ref), dtype="float32")
    n = int(WIN * sr)
    parts = []
    for i in range(0, max(1, len(wav) - int(3 * sr)), n):
        seg = wav[i:i + n]
        if len(seg) < 3 * sr or float(np.sqrt(np.mean(seg ** 2))) < 0.01:
            continue
        peak = float(np.max(np.abs(seg)))
        spec = np.abs(np.fft.rfft(seg[: 4 * sr]))
        freqs = np.fft.rfftfreq(len(seg[: 4 * sr]), 1 / sr)
        bright = float((spec * freqs).sum() / (spec.sum() + 1e-8))  # độ sáng giọng
        rms = float(np.sqrt(np.mean(seg ** 2)))
        if peak > 0.99:  # bị rè/vỡ tiếng
            continue
        f = OUT / f"seg{len(parts)}.wav"
        sf.write(str(f), seg, sr)
        emb, codes = tts.encode_reference(str(f), denoise=True)
        f.unlink()
        parts.append((np.asarray(emb, dtype=np.float32), codes, rms, bright))
    if not parts:
        raise RuntimeError("Bản thu quá ngắn hoặc quá nhỏ tiếng")
    # bỏ 1/4 số đoạn nhỏ tiếng nhất (thường nói lí nhí, không rõ chữ)
    if len(parts) >= 4:
        cut = sorted(p[2] for p in parts)[len(parts) // 4]
        parts = [p for p in parts if p[2] >= cut]
    embs = np.stack([p[0].reshape(-1) for p in parts])
    unit = embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-8)
    mean = unit.mean(0)
    sim = unit @ mean
    # đoạn mẫu nhịp đọc: trong nửa giống giọng chung nhất, lấy đoạn tươi sáng và rõ tiếng nhất
    close = [i for i in np.argsort(-sim)[: max(1, (len(parts) + 1) // 2)]]
    best = int(close[0])  # đoạn giống giọng chung nhất: đọc đều, rõ, ít cười hay ngập ngừng
    norm0 = float(np.linalg.norm(embs[best]))
    mean = (mean / (np.linalg.norm(mean) + 1e-8) * norm0).reshape(parts[0][0].shape).astype(parts[0][0].dtype)
    print(f"   dùng {len(parts)} đoạn 8 giây rõ tiếng nhất, mẫu nhịp đọc là đoạn đều giọng nhất")
    return {"speaker_emb": mean, "codes": parts[best][1]}


def to_mp3(wav: np.ndarray, sr: int, path: Path, pitch: float = 1.0, tempo: float = 1.0):
    pcm = (np.clip(wav, -1, 1) * 32767).astype(np.int16).tobytes()
    # rõ chữ: đọc chậm nhẹ, nâng dải 2 đến 5 kHz (vùng phụ âm), giữ formant khi nâng tông để không bị giọng chuột
    # cắt thời gian chết: mọi khoảng lặng dài hơn 0,2 giây rút còn 0,12 giây
    gaps = "silenceremove=start_periods=1:start_threshold=-42dB:stop_periods=-1:stop_duration=0.2:stop_threshold=-42dB:stop_silence=0.12"
    clear = gaps + ",highpass=f=80,equalizer=f=3500:t=q:w=1.2:g=3,equalizer=f=250:t=q:w=1:g=-2"
    fx = [f"rubberband=pitch={pitch}:tempo={tempo}:formant=preserved:pitchq=quality,{clear},loudnorm=I=-16:TP=-1.5",
          f"atempo={tempo},{clear},loudnorm=I=-16:TP=-1.5"]
    for af in fx:
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-",
                            "-af", af, "-b:a", "128k", str(path)], input=pcm)
        if r.returncode == 0:
            break
        print("   (không có rubberband, chỉ chỉnh tốc độ)")
    print(f"   {len(wav) / sr:.0f}s")


def main():
    global VOICE_NAME
    fids = latest_voices(len(VOICE_NAMES))
    if len(fids) < len(VOICE_NAMES):
        requests.post(f"{API}/sendMessage", timeout=30, data={"chat_id": OWNER, "text":
                      f"Mình chỉ thấy {len(fids)} file giọng trong 24 giờ qua, cần {len(VOICE_NAMES)}. Bạn gửi lại giúp mình nhé."})
        sys.exit("Thiếu giọng mẫu")
    from vieneu import Vieneu
    tts = Vieneu()
    text = AB.speakable(DEMO)
    for code, (name, fid) in zip("XY", zip(VOICE_NAMES, fids)):
        VOICE_NAME = name
        print(code, name)
        try:
            ref = download(fid)
            voice = enroll_full(tts, ref)
            ref.unlink(missing_ok=True)
            wav = tts.infer(text, voice=voice, max_chars=256, silence_p=0.04, temperature=0.4, top_k=10,
                            repetition_penalty=1.3)
            mp3 = OUT / f"{code}_{name.replace(' ', '_')}.mp3"
            to_mp3(np.asarray(wav, dtype=np.float32), tts.sample_rate, mp3, tempo=1.08)
            AB.VS.send(mp3, f"{code} · Giọng {name} đọc thử tin podcast sáng nay (VieNeu, miễn phí)")
        except Exception as ex:
            print(f"   ! {code} lỗi: {ex}")


if __name__ == "__main__":
    main()
