"""Ludo bản 2: ngắt nghỉ tự nhiên hơn, đọc từ tiếng Anh chuẩn hơn (miễn phí, Gemini Flash).

So với bản B:
- Đọc cả đoạn trong MỘT lần gọi (giọng liền mạch, không bị "reset" giữa các đoạn).
- Mỗi câu một dòng, câu dài tách ở chỗ lấy hơi tự nhiên → máy nghỉ đúng chỗ.
- Lời đạo diễn viết theo khung Google khuyên dùng: hồ sơ giọng, bối cảnh, nhịp, cách đọc tiếng Anh.
- Bảng phát âm cho từng từ tiếng Anh (FDV đọc từng chữ cái, unlock, revenue...).
F: bản trên. G: bản trên + thẻ nghỉ [short pause] / [medium pause] ở chỗ cần nhấn.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

import podcast as P
import voice_samples as VS
import voice_ab as AB
import voice_master as VM
import subprocess

TERMS = {
    "low float": "low float (English: 'low flow-t')",
    "FDV": "FDV (spell the letters in English: 'eff-dee-vee')",
    "unlock": "unlock (English: 'un-LOCK')",
    "revenue": "revenue (English: 'REV-uh-noo')",
    "narrative": "narrative (English: 'NAIR-uh-tiv')",
    "insider": "insider (English: 'in-SIGH-der')",
    "retail": "retail (English: 'REE-tail')",
}

# Lời dặn NGẮN (bản dài bị máy đọc to luôn cả lời dặn). Cùng độ dài với bản B đã chạy tốt.
STYLE = {
    "hn": ("Ludo, host of a premium Vietnamese finance channel. Deep, warm, composed, authoritative, like a VTV "
           "finance presenter. Standard Hanoi accent, crisp and polished, no regional coloring. Measured pace, "
           "about 160 words per minute, steady intonation, firm sentence endings. English crypto terms pronounced "
           "naturally in English."),
    "sg": ("Ludo, host of a premium Vietnamese business podcast. Deep, warm, composed and confident. Educated urban "
           "Saigon accent, polished and modern, no countryside coloring. Measured pace, about 160 words per minute, "
           "steady intonation. English crypto terms pronounced naturally in English."),
    "kol": ("Ludo, a successful young Vietnamese crypto KOL talking to his community. Confident, charismatic, "
            "energetic but controlled, a hint of a smile. Polished urban Saigon accent, never rural, never salesy. "
            "About 170 words per minute. English crypto terms pronounced naturally in English."),
}


def lines(t: str) -> str:
    """Mỗi câu một dòng; câu dài thì xuống dòng sau dấu phẩy ở chỗ lấy hơi."""
    out = []
    for s in re.split(r"(?<=[.!?:])\s+", t.strip()):
        if len(s.split()) > 22 and ", " in s:
            parts = s.split(", ")
            cur = parts[0]
            for p in parts[1:]:
                if len(cur.split()) >= 9:
                    out.append(cur + ",")
                    cur = p
                else:
                    cur += ", " + p
            out.append(cur)
        else:
            out.append(s)
    return "\n".join(out)


def tagged(t: str) -> str:
    t = re.sub(r":\s*", ": [short pause] ", t, count=1)
    t = t.replace("Có bốn nguyên nhân.", "Có bốn nguyên nhân. [medium pause]")
    return t.replace(", còn retail", ", [short pause] còn retail")


def main():
    out = Path("samples"); out.mkdir(exist_ok=True)
    gem = P.Gemini(os.getenv("INSIGHT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", ""))
    text = AB.speakable(AB.HOOK + " " + AB.BODY)
    VS.WORDS[0] = len(text.split())
    used = [v for k, v in TERMS.items() if k.lower() in text.lower()]
    terms = "\n".join("- " + v for v in used)
    plain = lines(text)
    variants = [
        ("J", "Ludo", "hn", "Ludo giọng chuẩn Hà Nội, dẫn chương trình tài chính"),
        ("K", "Ludo", "sg", "Ludo giọng Sài Gòn thành thị, podcast kinh doanh"),
        ("N", "Ludo", "kol", "Ludo vibe KOL crypto, tự tin, cuốn"),
        ("L", "Charon", "hn", "Charon (giọng trầm, rõ) chuẩn Hà Nội"),
        ("O", "Puck", "kol", "Puck (giọng trẻ, sáng) vibe KOL crypto"),
    ]
    for code, voice, acc, label in variants:
        print(code, label)
        try:
            pcm = gem.tts(["gemini-3.8-flash-tts"], voice, STYLE[acc], plain)
            sec = len(pcm) / (P.SAMPLE_RATE * 2)
            if sec > len(plain.split()) / 150 * 60 * 1.35:   # dài bất thường = máy đọc cả lời dặn, bỏ
                raise RuntimeError(f"audio dài bất thường {sec:.0f}s, có thể đọc nhầm lời dặn")
            raw = out / f"{code}-raw.mp3"
            VS.to_mp3(pcm, raw)
            p = out / f"{code}-{voice.lower()}.mp3"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-af", VM.CHAIN.format(tempo=1.0),
                            "-ar", "48000", "-b:a", "160k", str(p)], check=True)
            raw.unlink()
            VS.send(p, f"{code}. {label} (đã làm đẹp giọng)")
        except Exception as ex:
            print(f"   ! {code} lỗi: {str(ex)[:300]}")
        time.sleep(12)
    print('Thứ tự key đã dùng: xem dòng ↪ ở trên (nếu có)')


def raw_tts(gem, prompt: str) -> bytes:
    """Gọi Gemini với nguyên lời đạo diễn (không bọc thêm khung của podcast.tts)."""
    import base64
    data = gem._post("gemini-3.8-flash-tts", {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Ludo"}}}},
    }, timeout=300)
    pcm = b""
    for part in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            pcm += P.decode_audio(base64.b64decode(part["inlineData"]["data"]), part["inlineData"].get("mimeType", ""))
    return pcm


if __name__ == "__main__":
    main()
