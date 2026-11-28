"""Khớp mốc thời gian từng chữ theo giọng đọc THẬT (Trọng 28/11: "hình và text không khớp nhau rất rất là nhiều").

Trước đây mốc chữ được ƯỚC theo độ dài chữ trong câu, câu dài lệch tới 1 đến 2 giây, nên thẻ hình và phụ đề
hiện trễ hoặc sớm hơn lời đọc. Giờ máy nghe lại giọng (Whisper, có mốc từng chữ) rồi so với kịch bản:
chữ nào nghe ra thì lấy đúng giây đó, chữ không nghe ra thì nội suy giữa 2 chữ nghe được hai bên.
Nghe khớp dưới 50% (giọng lạ, Whisper lỗi) thì trả None để dùng cách ước cũ.
"""
from __future__ import annotations

import difflib


def _tokens(w: str) -> list[str]:
    import tts_qa
    return tts_qa.words(w)


def heard_words(pcm: bytes, sr: int) -> list[tuple[float, float, str]]:
    """Whisper nghe pcm 16-bit mono, trả [(giây đầu, giây cuối, chữ)]."""
    import numpy as np
    import tts_qa
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    if sr != 16000:   # đổi tần số mẫu đơn giản (nội suy tuyến tính) cho Whisper
        n = int(len(a) * 16000 / sr)
        a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
    segs, _ = tts_qa._model().transcribe(a, language="vi", vad_filter=False, beam_size=1, word_timestamps=True)
    return [(w.start, w.end, w.word) for s in segs for w in (s.words or [])]


def align(script_words: list[str], heard: list[tuple[float, float, str]], speech: float) -> list[dict] | None:
    """script_words: chữ của kịch bản (đúng như hiện trên phụ đề). heard: chữ Whisper nghe được kèm giây."""
    if not script_words:
        return []
    st, owner = [], []
    for i, w in enumerate(script_words):
        for t in _tokens(w) or [w.lower()]:
            st.append(t)
            owner.append(i)
    ht, htime = [], []
    for a, b, w in heard:
        toks = _tokens(w)
        for k, t in enumerate(toks):   # chữ Whisper bung ra nhiều tiếng (vd số): chia đều thời gian
            ht.append(t)
            htime.append((a + (b - a) * k / len(toks), a + (b - a) * (k + 1) / len(toks)))
    if not st or not ht:
        return None
    sm = difflib.SequenceMatcher(None, st, ht, autojunk=False)
    start: dict[int, float] = {}
    end: dict[int, float] = {}
    hit = 0
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            i, (a, b) = owner[blk.a + k], htime[blk.b + k]
            start[i] = min(start.get(i, a), a)
            end[i] = max(end.get(i, b), b)
            hit += 1
    if hit / len(st) < 0.5:
        return None
    n = len(script_words)
    s = [start.get(i) for i in range(n)]
    known = [i for i in range(n) if s[i] is not None]
    for i in range(n):   # nội suy chữ không nghe ra, chia đều giữa 2 chữ nghe được gần nhất
        if s[i] is not None:
            continue
        lo = max([k for k in known if k < i], default=None)
        hi = min([k for k in known if k > i], default=None)
        t0 = end[lo] if lo is not None else 0.0
        t1 = s[hi] if hi is not None else speech
        first = (lo + 1) if lo is not None else 0
        last = (hi - 1) if hi is not None else n - 1
        s[i] = t0 + (t1 - t0) * (i - first + 0.5) / (last - first + 1)
    for i in range(1, n):   # luôn tăng dần
        s[i] = max(s[i], s[i - 1] + 0.01)
    out = []
    for i, w in enumerate(script_words):
        e = end.get(i) if i in end else (s[i + 1] if i + 1 < n else speech)
        out.append({"t": w, "s": round(s[i], 3), "e": round(max(e, s[i] + 0.05), 3)})
    return out
