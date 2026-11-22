"""Thử đọc 1 câu bằng giọng Gemini Ludo@kol rồi in bản nghe lại (Whisper) kèm thời điểm, để xem có đọc lặp thật không.
Dùng: python tts_probe.py  (đọc các câu trong biến PROBE_TEXTS, ngăn cách bởi dòng '||')"""
import os
from pathlib import Path

import yaml

import podcast as P
import video as V
import voice_ab as VA
import voice_ludo2 as VL
import tts_qa

cfg = yaml.safe_load(Path("sources.yaml").read_text(encoding="utf-8"))
cfg["podcast"]["tts_provider"] = "gemini"
cfg["podcast"]["voice"] = "Ludo"
cfg["podcast"]["voice_style"] = VL.STYLE["kol"]
gem = P.Gemini(os.getenv("INSIGHT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", ""))
Path("probe").mkdir(exist_ok=True)
for i, t in enumerate(x.strip() for x in os.environ["PROBE_TEXTS"].split("||") if x.strip()):
    txt = VA.speakable(t)
    pcm = V.tts_once(gem, cfg, txt)
    out = Path("probe") / f"probe{i}.wav"
    V.pcm_to_wav(pcm, out)
    print(f"===== BẢN {i}: {txt}")
    print(f"   dài {len(pcm) / (P.SAMPLE_RATE * 2):.1f}s")
    for s, e, w in tts_qa.transcribe(str(out)):
        print(f"   [{s:5.1f} - {e:5.1f}] {w}")
    print("   kiểm tra:", tts_qa.check(str(out), t))
