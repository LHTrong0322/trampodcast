"""So sánh giọng A/B cho video Smart Penguin Insights (cùng 1 đoạn kịch bản đã duyệt, cùng giọng Ludo).

  A: như hiện tại (model gemini-3.8-flash-tts, không chỉ dẫn phong cách)
  B: cùng model + chỉ dẫn phong cách từng phần + chữ đã chuẩn hoá để máy đọc (cách 1 + 2, miễn phí)
  C: model Pro (gemini-2.5-pro-preview-tts) + chỉ dẫn phong cách (để biết bản Pro có hay hơn không)
Gửi 3 file mp3 vào Telegram và lưu thư mục samples/ (artifact GitHub).
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

import podcast as P
import voice_samples as VS

HOOK = ("Kyle nói chu kỳ này chỉ có một thước đo đáng tin: doanh thu thật và đang tăng. Còn lại, kể cả những màn "
        "hợp tác với tên tuổi lớn, phần nhiều chỉ là cái cớ để bơm giá.")
BODY = ("Kyle gọi crypto là một thị trường chanh, tức là thị trường mà người mua không phân biệt được hàng tốt hay hàng "
        "xấu, nên mặc định coi tất cả là xấu. Có bốn nguyên nhân. Thứ nhất, token có low float nhưng FDV rất cao, rồi "
        "unlock dần trong nhiều năm, tạo ra một bức tường người bán. Thứ hai, dự án không có revenue, không có người "
        "dùng thật, chỉ sống nhờ narrative. Insider biết lịch unlock và số liệu thật, còn retail thì không.")

# Cách 1: chỉ dẫn phong cách cho từng loại đoạn (Gemini TTS đọc phần này như lời đạo diễn, không đọc to)
PROFILE = ("Ludo, host of 'Smart Penguin Insights', a Vietnamese crypto explainer channel. Confident, smart, "
           "trustworthy analyst talking to a friend; natural conversational Vietnamese, never robotic or news-anchor stiff. "
           "English crypto terms (low float, FDV, unlock, revenue, narrative, insider, retail, buyback, tokenomics) are "
           "pronounced naturally in English, smoothly inside the Vietnamese sentence.")
STYLE = {
    "hook": "Energetic and punchy, slightly faster pace, grab attention in the first second. Strong emphasis on the key "
            "claim ('doanh thu thật'), a short dramatic pause before the final clause.",
    "intro": "Warm, welcoming, a smile in the voice, medium pace.",
    "section": "Clear, confident analytical tone at a steady medium pace. Slow down a little and stress numbers, "
               "list markers ('Thứ nhất', 'Thứ hai') and English terms. Brief natural pauses at commas and between sentences.",
    "outro": "Reflective and sincere, slightly slower, gentle emphasis on the final call to action.",
}

UNIT = {"K": "nghìn", "M": "triệu", "B": "tỷ", "T": "nghìn tỷ"}


def speakable(t: str) -> str:
    """Cách 2: chuẩn hoá chữ cho máy đọc (không đổi nội dung): tiền, phần trăm, ký hiệu."""
    t = re.sub(r"\$(\d+(?:[.,]\d+)?)\s*([KMBT])\b", lambda m: f"{m.group(1).replace('.', ',')} {UNIT[m.group(2)]} đô", t)
    t = re.sub(r"\$(\d[\d.,]*)", r"\1 đô", t)
    t = re.sub(r"(\d+(?:[.,]\d+)?)\s*%", r"\1 phần trăm", t)
    t = t.replace("&", " and ").replace("→", ", ").replace("/", " trên ")
    t = re.sub(r"\$?\b[A-Z][A-Z0-9]{2,}\b", _name, t)
    return re.sub(r"\s{2,}", " ", t).strip()


# Trọng chốt 21/11: TÊN DỰ ÁN đọc liền một từ (AAVE đọc "Aave", không đánh vần A A V E).
# Chỉ các viết tắt dưới đây mới đánh vần từng chữ cái.
SPELL = {"FDV", "DCA", "TVL", "VC", "ETF", "ATH", "ATL", "APY", "APR", "TGE", "DEX", "CEX", "KOL", "PMF", "BTC", "ETH",
         "DAO", "NFT", "USD", "USDT", "USDC", "SEC", "DWF", "YTD", "CEO", "AI", "API", "OTC", "MEV", "RWA", "LST", "LRT",
         "AMM", "CPI", "FED", "FOMC", "GDP", "IPO", "ICO", "IDO", "KYC", "OI", "PNL", "ROI", "SOL", "BNB", "XRP", "DYOR"}


def _name(m) -> str:
    w = m.group(0).lstrip("$")
    return w if w in SPELL else w.capitalize()


def styled(kind: str) -> str:
    return PROFILE + "\n\nDelivery: " + STYLE[kind]


def main():
    out = Path("samples"); out.mkdir(exist_ok=True)
    gem = P.Gemini(os.getenv("INSIGHT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", ""))
    VS.WORDS[0] = len((HOOK + " " + BODY).split())
    variants = [
        ("A", "Hiện tại: Ludo, model Flash, không chỉ dẫn", ["gemini-3.8-flash-tts"], False),
        ("B", "Mới miễn phí: Ludo Flash + chỉ dẫn phong cách + chữ chuẩn hoá", ["gemini-3.8-flash-tts"], True),
        ("C", "Bản Pro: Ludo Pro + chỉ dẫn phong cách", ["gemini-2.5-pro-preview-tts"], True),
    ]
    for code, label, models, improved in variants:
        print(f"{code} · {label}")
        try:
            pcm = b""
            for kind, text in (("hook", HOOK), ("section", BODY)):
                txt = speakable(text) if improved else text
                pcm += gem.tts(models, "Ludo", styled(kind) if improved else "", txt)
                pcm += b"\x00\x00" * int(P.SAMPLE_RATE * 0.35)   # nghỉ ngắn giữa 2 đoạn như video thật
                time.sleep(8)
            p = out / f"{code}-ludo.mp3"
            VS.to_mp3(pcm, p)
            VS.send(p, f"{code}. {label}")
        except Exception as ex:
            print(f"   ! {code} lỗi: {str(ex)[:300]}")
        time.sleep(15)


if __name__ == "__main__":
    main()
