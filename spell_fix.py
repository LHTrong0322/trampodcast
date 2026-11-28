"""Soát chính tả chữ trên hình TRƯỚC khi dựng (Trọng 28/11: "rất nhiều đoạn sai chính tả").

Gom mọi chữ sẽ hiện trên hình (tiêu đề, thẻ, nhãn, phụ đề) từ props của Remotion, nhờ Claude chỉ ra lỗi chính tả tiếng Việt
(sai dấu, gõ nhầm, thiếu chữ, viết hoa sai tên riêng), rồi tự sửa thẳng vào props. Chỉ sửa chính tả, không đổi ý, không đổi văn.
Lỗi gọi Claude thì bỏ qua, không làm hỏng lượt dựng.
"""
from __future__ import annotations

import re

PROMPT = """Bạn là biên tập viên soát chính tả tiếng Việt cho video YouTube kênh crypto Smart Penguin Insights.
Dưới đây là TOÀN BỘ chữ sẽ hiện trên màn hình (mỗi dòng 1 cụm). Tìm lỗi CHÍNH TẢ: sai dấu, gõ nhầm, thừa thiếu chữ cái,
dính chữ, viết hoa sai tên riêng (Bitcoin, Charles Dow, Wall Street Journal...), dấu câu lạc chỗ.
KHÔNG sửa văn phong, KHÔNG dịch thuật ngữ tiếng Anh (buyback, unlock, revenue, trend, uptrend...), KHÔNG đổi số liệu,
KHÔNG thêm dấu gạch ngang dài. Không chắc là lỗi thì bỏ qua.
{texts}
Trả DUY NHẤT JSON: {{"sua": [{{"sai": "đoạn sai, copy NGUYÊN VĂN, ngắn nhất đủ để không nhầm chỗ", "dung": "đoạn đúng"}}]}}"""

SKIP = {"images", "img", "logo", "avatar", "src", "audio", "source", "type", "at", "tone", "mode", "color", "comp", "s", "e"}
_CACHE: dict[str, str] = {}


def _walk(x, fn, key=""):
    if isinstance(x, dict):
        return {k: (v if k in SKIP else _walk(v, fn, k)) for k, v in x.items()}
    if isinstance(x, list):
        return [_walk(v, fn, key) for v in x]
    if isinstance(x, str) and re.search(r"[A-Za-zÀ-ỹ]", x):
        return fn(x)
    return x


def screen_texts(props: dict) -> list[str]:
    """Mọi cụm chữ sẽ hiện trên hình. Phụ đề gom thành câu cho Claude đọc có ngữ cảnh."""
    seen, out = set(), []

    def add(t):
        t = " ".join(t.split())
        if len(t) > 1 and t not in seen:
            seen.add(t)
            out.append(t)
        return t
    body = {k: v for k, v in props.items() if k not in ("data", "words")}
    for sc in body.get("scenes") or []:
        ws = " ".join(w.get("t", "") for w in sc.get("words") or [])
        for sent in re.split(r"(?<=[.!?])\s+", ws):
            add(sent)
    _walk({k: v for k, v in body.items() if k != "scenes"}, add)
    _walk([{k: v for k, v in sc.items() if k != "words"} for sc in body.get("scenes") or []], add)
    return out


def apply(props: dict, fixes: dict[str, str]) -> tuple[dict, set]:
    """Sửa thẳng vào props (cả chữ thẻ và từng chữ phụ đề). Trả (props, các lỗi đã thật sự sửa)."""
    if not fixes:
        return props, set()
    n: set = set()

    def fix(t):
        nonlocal n
        for a, b in fixes.items():
            if a in t:
                t = t.replace(a, b)
                n.add(a)
        return t
    out = {**props}
    for k, v in props.items():
        if k in ("scenes",):
            continue
        if k not in ("data",) and k not in SKIP:
            out[k] = _walk(v, fix, k)
    scenes = []
    for sc in props.get("scenes") or []:
        sc2 = _walk({k: v for k, v in sc.items() if k != "words"}, fix)
        words = [dict(w) for w in sc.get("words") or []]
        for a, b in fixes.items():   # phụ đề: sửa theo từng cụm chữ liền nhau
            aw, bw = a.split(), b.split()
            if not aw or len(aw) != len(bw):
                continue
            for i in range(len(words) - len(aw) + 1):
                if [w["t"] for w in words[i:i + len(aw)]] == aw:
                    for j, t in enumerate(bw):
                        words[i + j]["t"] = t
                    n.add(a)
        sc2["words"] = words
        scenes.append(sc2)
    out["scenes"] = scenes
    return out, n


def check(props: dict, run=None, log=print) -> tuple[dict, list[str]]:
    """Soát và sửa. Trả (props đã sửa, danh sách 'sai → đúng' để báo Trọng)."""
    texts = [t for t in screen_texts(props) if t not in _CACHE]
    if texts:
        try:
            if run is None:
                import script_review as SR
                run = lambda pr: SR.run_claude(pr, turns=3, timeout=600)
            res = run(PROMPT.format(texts="\n".join(f"- {t}" for t in texts[:400])))
            for f in res.get("sua") or []:
                a, b = str(f.get("sai") or ""), str(f.get("dung") or "")
                if a and b and a != b and "—" not in b and "–" not in b and len(a) <= 80:
                    _CACHE[a] = b
            for t in texts:
                _CACHE.setdefault(t, t)
        except Exception as ex:
            log(f"   ! soát chính tả lỗi, bỏ qua: {str(ex)[:150]}")
            return props, []
    fixes = {a: b for a, b in _CACHE.items() if a != b}
    props, done = apply(props, fixes)
    lines = [f"{a} → {fixes[a]}" for a in done]
    log(f"   🔤 Soát chính tả chữ trên hình: {len(texts)} cụm mới, sửa {len(lines)} lỗi" + (f": {'; '.join(lines[:6])}" if lines else ""))
    return props, lines
