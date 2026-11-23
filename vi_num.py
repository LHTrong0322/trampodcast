"""Đọc số thành chữ tiếng Việt cho giọng máy (Trọng 23/11: phụ đề hiện số "9" thay vì "chín",
nên kịch bản viết số bằng chữ số, chỉ lúc đưa cho giọng đọc mới đổi sang chữ).

S&P 500 đọc là "ét en pi năm trăm" (Trọng 23/11: không đọc số 500 kiểu tiếng Anh)."""
from __future__ import annotations

import re

DIG = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]


def _two(n: int) -> str:
    """0..99, không có số 0 đứng đầu."""
    t, u = divmod(n, 10)
    if t == 0:
        return DIG[u]
    if t == 1:
        return "mười" + ("" if u == 0 else " lăm" if u == 5 else " " + DIG[u])
    out = DIG[t] + " mươi"
    if u == 1:
        return out + " mốt"
    if u == 4:
        return out + " tư"
    if u == 5:
        return out + " lăm"
    return out + ("" if u == 0 else " " + DIG[u])


def _three(n: int, full: bool) -> str:
    """0..999. full = nhóm không đứng đầu (2025 = hai nghìn KHÔNG TRĂM hai mươi lăm)."""
    h, r = divmod(n, 100)
    if h == 0 and not full:
        return _two(r)
    out = DIG[h] + " trăm"
    if r == 0:
        return out
    if r < 10:
        return out + " lẻ " + DIG[r]
    return out + " " + _two(r)


def read_int(n: int) -> str:
    if n == 0:
        return "không"
    units = ["", " nghìn", " triệu", " tỷ"]
    groups = []
    while n:
        n, g = divmod(n, 1000)
        groups.append(g)
    words = []
    for i in range(len(groups) - 1, -1, -1):
        g = groups[i]
        if g == 0:
            continue
        lead = i == len(groups) - 1
        words.append(_three(g, not lead) + units[i] if i < 4 else _three(g, not lead))
    return " ".join(words)


def read_number(s: str) -> str:
    """'94' → chín mươi tư; '0.03' / '0,03' → không phẩy không ba; '6,910' → sáu nghìn chín trăm mười."""
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", s):   # dấu ngăn hàng nghìn
        return read_int(int(re.sub(r"[.,]", "", s)))
    m = re.fullmatch(r"(\d+)[.,](\d+)", s)
    if m:
        frac = m.group(2)
        tail = " ".join(DIG[int(c)] for c in frac) if frac.startswith("0") or len(frac) > 2 else read_int(int(frac))
        return f"{read_int(int(m.group(1)))} phẩy {tail}"
    return read_int(int(s))


def say_numbers(t: str) -> str:
    """Đổi chữ số trong câu thành chữ (không đụng tên có số dính chữ như VN30)."""
    t = re.sub(r"S&P\s*500", "ét en pi năm trăm", t)
    t = re.sub(r"S&P\b", "ét en pi", t)
    t = re.sub(r"(?<![\w.,])(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)(?![\w])", lambda m: read_number(m.group(1)), t)
    return t


if __name__ == "__main__":
    for x, want in [("94", "chín mươi tư"), ("79", "bảy mươi chín"), ("21", "hai mươi mốt"), ("15", "mười lăm"),
                    ("10", "mười"), ("105", "một trăm lẻ năm"), ("1957", "một nghìn chín trăm năm mươi bảy"),
                    ("2025", "hai nghìn không trăm hai mươi lăm"), ("164", "một trăm sáu mươi tư"),
                    ("0.03", "không phẩy không ba"), ("6,910", "sáu nghìn chín trăm mười"), ("1.5", "một phẩy năm"),
                    ("100", "một trăm"), ("30", "ba mươi"), ("1000000", "một triệu")]:
        got = read_number(x)
        assert got == want, (x, got, want)
    print(say_numbers("S&P 500 tăng 10 phần trăm từ 1957, VN30 giữ nguyên, phí 0.03 phần trăm, 3 triệu đô."))
    print("ok")
