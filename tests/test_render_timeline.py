"""Trọng 27/11: short bài học viết sẵn có intro trống làm dựng lỗi KeyError 'intro'."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import insight_render as R  # noqa: E402


def test_intro_trong_khong_lam_hong_dung():
    pcm = {"hook": b"\0\0" * 2400, "s0": b"\0\0" * 4800, "outro": b"\0\0" * 2400}
    text = {"hook": "Đầu tư dài hạn có cần xem chart không?", "s0": "Chart cho biết giá đang ở đâu.", "outro": "Không phải lời khuyên đầu tư."}
    pre = {k: [{"t": "x", "s": 0, "e": 0.1}] for k in pcm}
    _, scenes, total = R.build_timeline({"sections": [{}]}, pcm, text, pre=pre)
    assert [sc["key"] for sc in scenes] == ["hook", "s0", "outro"]
    assert total > 0


def test_doan_co_loi_ma_thieu_giong_van_bao_loi():
    import pytest
    pcm = {"hook": b"\0\0" * 2400, "outro": b"\0\0" * 2400}
    text = {"hook": "a", "intro": "Có lời mà mất giọng", "s0": "b", "outro": "c"}
    with pytest.raises(KeyError):
        R.build_timeline({"sections": [{}]}, pcm, text, pre={k: [] for k in pcm})
