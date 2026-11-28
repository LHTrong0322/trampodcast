"""Trọng 27/11: chart lý thuyết Dow (Trọng 28/11: bỏ backtest) trên giá BTC tuần thật (beat type "dow").

Cùng thuật toán dow() của bot radar (LHTrong0322/radar-scanner, index.html): đỉnh/đáy swing là nến cao/thấp nhất
trong k nến mỗi bên (mặc định k = 4). So 2 đỉnh và 2 đáy gần nhất:
  HH + HL (đỉnh sau cao hơn, đáy sau cao hơn)  = xu hướng tăng (state 1), trừ khi giá đã thủng đáy HL gần nhất
  LH + LL                                      = xu hướng giảm (state -1), trừ khi giá đã vượt đỉnh LH gần nhất
  còn lại                                      = lẫn lộn (state 0)
Không nhìn trước tương lai: đỉnh/đáy ở nến i chỉ được biết sau khi đã có k nến bên phải.
Backtest: cầm BTC khi state = 1, đứng ngoài (tiền mặt) khi khác 1, vào/ra ở giá đóng cửa tuần. Không tính phí.
"""
from __future__ import annotations


def pivots(px: list[float], k: int = 4) -> list[dict]:
    """Đỉnh/đáy swing trên giá đóng cửa: [{i, tp: 'H'|'L', v}] theo thứ tự thời gian."""
    out = []
    for i in range(k, len(px) - k):
        win = px[i - k:i] + px[i + 1:i + k + 1]
        if px[i] > max(win):
            out.append({"i": i, "tp": "H", "v": px[i]})
        elif px[i] < min(win):
            out.append({"i": i, "tp": "L", "v": px[i]})
    return out


def label_swings(piv: list[dict]) -> list[dict]:
    """Gắn nhãn HH/LH cho đỉnh, HL/LL cho đáy (so với đỉnh/đáy trước đó cùng loại)."""
    last = {"H": None, "L": None}
    out = []
    for p in piv:
        prev = last[p["tp"]]
        if prev is not None:
            up = p["v"] > prev
            lab = ("HH" if up else "LH") if p["tp"] == "H" else ("HL" if up else "LL")
            out.append({**p, "label": lab})
        last[p["tp"]] = p["v"]
    return out


def states(px: list[float], k: int = 4) -> list[int]:
    """Trạng thái Dow tại từng nến, chỉ dùng đỉnh/đáy đã được xác nhận tới nến đó."""
    piv = pivots(px, k)
    st, H, L, j = [], [], [], 0
    for t in range(len(px)):
        while j < len(piv) and piv[j]["i"] + k <= t:
            (H if piv[j]["tp"] == "H" else L).append(piv[j]["v"])
            j += 1
        if len(H) < 2 or len(L) < 2:
            st.append(0)
            continue
        hh, hl = H[-1] > H[-2], L[-1] > L[-2]
        if hh and hl:
            st.append(0 if px[t] < L[-1] else 1)
        elif not hh and not hl:
            st.append(0 if px[t] > H[-1] else -1)
        else:
            st.append(0)
    return st
