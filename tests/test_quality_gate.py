"""Cửa chặn chất lượng: bản chính không được thua bản nháp (Trọng 23/11)."""
import insight


def test_worse_total_lower():
    assert insight.worse({"score": 6.8, "scores": {}}, {"score": 6.6, "scores": {}}) == ["tổng 6.8 → 6.6"]


def test_worse_metric_drop_one_point():
    a = {"score": 6.8, "scores": {"du_lieu_lien_quan": 7.5, "phu_de": 6.5}}
    b = {"score": 6.9, "scores": {"du_lieu_lien_quan": 6, "phu_de": 7}}
    assert insight.worse(a, b) == ["du_lieu_lien_quan 7.5 → 6"]


def test_not_worse_small_noise():
    a = {"score": 6.8, "scores": {"nhip_do": 7.5}}
    b = {"score": 6.8, "scores": {"nhip_do": 7}}
    assert insight.worse(a, b) == []


def test_review_avg_averages(monkeypatch):
    import insight_publish as PB
    seq = iter([{"score": 7.0, "scores": {"a": 7, "b": 6}, "can_sua": ["x"]},
                {"score": 6.0, "scores": {"a": 6, "b": 6}, "can_sua": ["y"]}])
    monkeypatch.setattr(PB, "review", lambda *a, **k: next(seq))
    rv = PB.review_avg(None, None, {}, None, n=2)
    assert rv["score"] == 6.5 and rv["scores"]["a"] == 6.5 and rv["can_sua"] == ["y"] and rv["runs"] == [7.0, 6.0]


def test_below_target():
    assert insight.below({"score": 7.2, "scores": {"a": 7, "b": 6.5, "c": 8}}) == ["b 6.5"]
    # Trọng 28/11: điểm tổng, máy đo bố cục và vai người xem cũng chặn
    assert insight.below({"score": 6.5, "scores": {}}) == ["tổng 6.5"]
    assert "máy đo" in insight.below({"score": 8, "scores": {}, "layout_serious": 2})[0]
    assert "không đáng xem" in insight.below({"score": 8, "scores": {}, "nguoi_xem": {"dang_xem": False}})[0]
