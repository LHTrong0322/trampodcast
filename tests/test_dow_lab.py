"""Trọng 27/11: chart lý thuyết Dow (28/11 bỏ backtest) (dow_lab). Dữ liệu giả có xu hướng rõ để kiểm tra logic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dow_lab as DL  # noqa: E402


def zigzag(legs):
    """Nối các chặng tuyến tính: [(từ, tới, số nến)]."""
    px = []
    for a, b, n in legs:
        px += [a + (b - a) * i / n for i in range(n)]
    return px + [legs[-1][1]]


UP = zigzag([(100, 130, 8), (130, 115, 8), (115, 150, 8), (150, 135, 8), (135, 180, 8), (180, 160, 8), (160, 200, 8)])
DOWN = zigzag([(200, 170, 8), (170, 185, 8), (185, 140, 8), (140, 160, 8), (160, 110, 8), (110, 125, 8), (125, 80, 8)])


def test_nhan_dinh_day_tang():
    labs = [s["label"] for s in DL.label_swings(DL.pivots(UP))]
    assert labs and all(x in ("HH", "HL") for x in labs)


def test_nhan_dinh_day_giam():
    labs = [s["label"] for s in DL.label_swings(DL.pivots(DOWN))]
    assert labs and all(x in ("LH", "LL") for x in labs)


def test_trang_thai_khong_nhin_truoc_tuong_lai():
    st = DL.states(UP)
    assert st[-1] == 1 and DL.states(DOWN)[-1] == -1
    # cắt dữ liệu tới nến t thì trạng thái tại t không đổi
    for t in (30, 40, 50):
        assert DL.states(UP[:t + 1])[t] == st[t]
