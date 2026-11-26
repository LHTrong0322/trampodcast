"""Trọng 27/11: còn câu/thẻ không đáng xem (dang_xem < 8) thì kịch bản không được chốt dù điểm tổng cao."""
import script_review as SR


def _fake(score, dang_xem):
    return lambda prompt: {"score": score, "scores": {"hook_1s": 9, "dang_xem": dang_xem}}


def test_dang_xem_thap_thi_khong_qua(monkeypatch):
    monkeypatch.setattr(SR, "run_claude", _fake(8.8, 6))
    assert SR.review('{"format": "short"}')["pass"] is False


def test_dang_xem_dat_thi_qua(monkeypatch):
    monkeypatch.setattr(SR, "run_claude", _fake(8.5, 8.5))
    assert SR.review('{"format": "short"}')["pass"] is True


def test_luat_gia_tri_co_trong_moi_buoc():
    import insight_lab as L, insight_publish as PB, preflight as PF
    for t in (SR.RUBRIC, SR.RUBRIC_SHORT, L.NEWS_PROMPT, PB.REVIEW_PROMPT, PF.PROMPT):
        assert "LUẬT GIÁ TRỊ" in t
