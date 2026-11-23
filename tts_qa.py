"""Kiểm tra giọng đọc trước khi dựng/gửi: nghe lại bằng máy (Whisper) rồi so với kịch bản.

Bắt 3 lỗi: đọc LẶP (một cụm từ bị đọc nhiều lần hơn kịch bản), đọc THIẾU (bỏ câu),
đọc THỪA (đọc cả lời dặn hoặc chữ lạ). Trọng chốt 21/11: không được gửi video bị lặp nữa.

Dùng trong code:   ok, reason = tts_qa.check("00.wav", "kịch bản đoạn này")
Dùng tay:          python tts_qa.py video.mp4 scripts/zeroxkyle-approved.json
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from collections import Counter

_MODEL = None


def _model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel("small", device="cpu", compute_type="int8")
    return _MODEL


def words(t: str) -> list[str]:
    import vi_num   # bản nghe lại hay ghi số bằng chữ số: đổi sang chữ để so với lời đọc (23/11)
    t = vi_num.say_numbers(t.replace('%', ' phần trăm')).lower()
    t = re.sub(r"\[[^\]]*\]", " ", t)
    # "một nghìn lẻ sáu mươi" (lời đọc) và "một nghìn không trăm sáu mươi" (Whisper) là cùng một số
    t = re.sub(r"\b(nghìn|ngàn) lẻ (\w+ mươi)", r"\1 không trăm \2", t)
    return re.findall(r"[0-9a-zà-ỹđ]+", t)


def transcribe(path: str) -> list[tuple[float, float, str]]:
    import subprocess
    import numpy as np
    # tự giải mã bằng ffmpeg (thư viện av trên máy GitHub hay lệch phiên bản)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    segs, _ = _model().transcribe(audio, language="vi", vad_filter=True, beam_size=1)
    return [(s.start, s.end, s.text.strip()) for s in segs]


def repeats(heard: list[str], script: list[str], n: int = 4) -> list[str]:
    """Cụm n từ xuất hiện trong bản nghe nhiều hơn trong kịch bản (dấu hiệu đọc lặp)."""
    def grams(w):
        return Counter(" ".join(w[i:i + n]) for i in range(len(w) - n + 1))
    h, s = grams(heard), grams(script)
    # log 23/11 (video 100y, phần chu kỳ 4 năm): Whisper ghi "chu kỳ" thành "chuukki", "một nghìn lẻ" thành "một nghìn không trăm",
    # nên cụm lặp HỢP LỆ trong kịch bản bị tính là đọc lặp, 4/4 lần. Chỉ tính cụm mà mọi chữ đều có trong kịch bản;
    # đọc lặp thật vẫn bị bắt qua các cụm viết đúng và qua kiểm tra độ dài (đọc thừa).
    vocab = set(script)
    return [g for g, c in h.items() if c > s.get(g, 0) and c >= 2 and all(w in vocab for w in g.split())]


def check(path: str, text: str) -> tuple[bool, str]:
    heard_t = " ".join(t for _, _, t in transcribe(path))
    heard, script = words(heard_t), words(text)
    if not script:
        return True, "trống"
    rep = repeats(heard, script)
    ratio = len(heard) / len(script)
    sim = difflib.SequenceMatcher(None, heard, script, autojunk=False).ratio()
    if len(rep) >= 2:
        return False, f"đọc lặp: {', '.join(rep[:3])}"
    if ratio > 1.25:
        return False, f"đọc thừa {ratio:.0%} so với kịch bản"
    if ratio < 0.75:
        return False, f"đọc thiếu, chỉ {ratio:.0%} kịch bản"
    if sim < 0.55:
        return False, f"khác kịch bản nhiều (giống {sim:.0%})"
    return True, f"ổn (giống {sim:.0%}, độ dài {ratio:.0%})"


def double_cut(path: str) -> float | None:
    """Gemini đôi khi đọc CẢ đoạn 2 lần liền (đo 23/11: hook 8s thành 16s, nửa sau giống hệt nửa đầu).
    Tìm chỗ bản nghe bắt đầu lại từ đầu, trả về giây nên cắt (giữa 2 lần đọc). Không thấy thì None."""
    segs = transcribe(path)
    if len(segs) < 2:
        return None
    head = words(segs[0][2])[:5]
    if len(head) < 3:
        return None
    for k in range(1, len(segs)):
        if segs[k][0] > 1.5 and words(segs[k][2])[:len(head)] == head:
            return round((segs[k - 1][1] + segs[k][0]) / 2, 2)
    return None


def check_video(path: str, script_json: str | None = None) -> list[str]:
    """Nghe cả video, liệt kê chỗ lặp kèm thời điểm."""
    segs = transcribe(path)
    script = []
    if script_json:
        d = json.load(open(script_json))
        parts = [d.get("hook", ""), d.get("intro", "")] + [s.get("narration", "") if isinstance(s, dict) else s
                                                          for s in d.get("sections", [])] + [d.get("outro", "")]
        script = words(" ".join(p for p in parts if isinstance(p, str)))
    allw, owner = [], []
    for i, (_, _, t) in enumerate(segs):
        w = words(t)
        allw += w
        owner += [i] * len(w)
    probs = []
    for g in repeats(allw, script, 5):
        gw = g.split()
        hits = [owner[k] for k in range(len(allw) - 4) if allw[k:k + 5] == gw]
        probs.append(f"'{g}' ở " + ", ".join(f"{segs[h][0]:.0f}s" for h in dict.fromkeys(hits)))
    for s, e, t in segs:
        print(f"{s:6.1f}-{e:6.1f} {t}")
    return probs


if __name__ == "__main__":
    probs = check_video(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("\nCHỖ LẶP:" if probs else "\nKhông thấy chỗ lặp.")
    for p in probs:
        print(" -", p)
