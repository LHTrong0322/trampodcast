"""Kiểm tra từng key Gemini còn lượt đọc giọng (TTS) và lượt viết chữ không. Mỗi key thử 1 câu rất ngắn. Không in khoá ra log."""
import os

import requests

NAMES = ["INSIGHT_GEMINI_API_KEY", "GEMINI_API_KEY", "GEMINI_API_KEY2"] + [f"GEMINI_API_KEY{i}" for i in range(3, 10)]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"


def probe(key: str, model: str, tts: bool) -> str:
    body = {"contents": [{"parts": [{"text": "Xin chào." if tts else "Trả lời đúng 1 chữ: ok"}]}]}
    if tts:
        body["generationConfig"] = {"responseModalities": ["AUDIO"],
                                    "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Ludo"}}}}
    r = requests.post(URL.format(m=model), params={"key": key}, json=body, timeout=120)
    if r.status_code == 200:
        return "CÒN LƯỢT"
    msg = r.json().get("error", {}).get("message", "")[:120] if r.headers.get("content-type", "").startswith("application/json") else r.text[:120]
    if r.status_code == 429:
        return "HẾT LƯỢT (429)" + (" trong ngày" if "PerDay" in r.text or "per day" in r.text.lower() else ", có thể chỉ giới hạn mỗi phút")
    return f"LỖI {r.status_code}: {msg}"


seen = set()
for n in NAMES:
    k = os.getenv(n, "").strip()
    if not k:
        continue
    dup = k in seen
    seen.add(k)
    if dup:
        print(f"{n}: trùng với một key khác")
        continue
    print(f"{n}: giọng đọc (gemini-3.8-flash-tts) = {probe(k, 'gemini-3.8-flash-tts', True)} | "
          f"viết chữ (gemini-2.5-flash) = {probe(k, 'gemini-2.5-flash', False)}")
