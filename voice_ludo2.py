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

TERMS = {
    "low float": "low float (English: 'low flow-t')",
    "FDV": "FDV (spell the letters in English: 'eff-dee-vee')",
    "unlock": "unlock (English: 'un-LOCK')",
    "revenue": "revenue (English: 'REV-uh-noo')",
    "narrative": "narrative (English: 'NAIR-uh-tiv')",
    "insider": "insider (English: 'in-SIGH-der')",
    "retail": "retail (English: 'REE-tail')",
}

PROMPT = """# AUDIO PROFILE: Ludo
Host of "Smart Penguin Insights", a Vietnamese crypto explainer channel on YouTube.
A sharp, calm analyst explaining to a smart friend over coffee. Warm, confident, never a news anchor, never robotic.

# THE SCENE
Recording a YouTube video in a quiet studio. He has read this script many times, so he speaks it naturally,
like he is thinking it through, not reading.

# DIRECTOR'S NOTES
Language: native Southern-neutral Vietnamese with correct tones.
Pacing: relaxed and unhurried, about 160 words per minute. Never rush.
Breathing: take a natural breath at every line break. Pause briefly at commas,
a little longer at full stops and after a colon. Slow down slightly on the key idea of each sentence.
Emphasis: lean on numbers, on list markers ("Thứ nhất", "Thứ hai") and on the contrast words ("còn", "nhưng").
English terms: these words are English and must sound like a fluent bilingual speaker saying them in English,
with English stress, NOT Vietnamese tones, then flow straight back into Vietnamese:
{terms}
Opening line: a little more energy to hook the listener, then settle into the calm analytical tone.
Read ONLY the transcript, word for word. Never read these notes or any headings or tags in brackets aloud.

# TRANSCRIPT
{text}"""


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
    for code, label, body in (
        ("F", "Ludo bản 2: ngắt nghỉ tự nhiên + phát âm tiếng Anh", lines(text)),
        ("G", "Ludo bản 2 + thẻ nghỉ ở chỗ nhấn", tagged(lines(text))),
    ):
        print(code, label)
        print(body)
        try:
            prompt = PROMPT.format(terms=terms, text=body)
            pcm = raw_tts(gem, prompt)
            p = out / f"{code}-ludo.mp3"
            VS.to_mp3(pcm, p)
            VS.send(p, f"{code}. {label}")
        except Exception as ex:
            print(f"   ! {code} lỗi: {str(ex)[:300]}")
        time.sleep(15)


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
