"""Trọng 27/11: chart + backtest lý thuyết Dow (dow_lab). Dữ liệu giả có xu hướng rõ để kiểm tra logic."""
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


def test_backtest_tranh_duoc_downtrend():
    px = UP + DOWN[1:]
    r = DL.backtest(px)
    s = r["stats"]
    assert s["dd"] > s["bhdd"]          # sụt giảm ít hơn mua rồi giữ (số âm, gần 0 hơn)
    assert r["signals"][0]["side"] == "buy" and any(x["side"] == "sell" for x in r["signals"])
    assert len(r["equity"]) == len(r["bh"]) == len(px)


def test_dien_o_so_dow_vao_loi_doc():
    import insight_lab as IL
    data = {"dow": {"2018:4": {"stats": {"ret": 1234.4, "bh": 512.0, "dd": -38.6, "bhdd": -77.2, "trades": 9, "inmkt": 55.1}}}}
    plan = {"hook": "Cầm khi Dow tăng: lãi {DOW:2018:ret}%, sụt tối đa {DOW:2018:dd}%, {DOW:2018:trades} lần mua.",
            "sections": [{"narration": "Mua rồi giữ: {DOW:2018/4:bh}%, sụt {DOW:2018:bhdd}%.", "beats": []}]}
    out = IL.live_numbers(plan, data)
    assert out["hook"] == "Cầm khi Dow tăng: lãi 1230%, sụt tối đa 39%, 9 lần mua."
    assert out["sections"][0]["narration"] == "Mua rồi giữ: 512%, sụt 77%."


def test_thieu_du_lieu_dow_thi_dung():
    import pytest
    import insight_lab as IL
    with pytest.raises(RuntimeError):
        IL.live_numbers({"hook": "{DOW:2018:ret}%", "sections": []}, {})
