"""Biểu đồ nhiều năm cắt theo ngày thật (lỗi 23/11: ghi '30 năm' mà dữ liệu 42 năm)."""
import time
import insight_lab as L


class R:
    def __init__(self, ts, cl):
        self._j = {"chart": {"result": [{"timestamp": ts, "indicators": {"quote": [{"close": cl}]}}]}}

    def json(self):
        return self._j


def test_years_cut_by_date(monkeypatch):
    now = time.time()
    ts = [now - (42 - k / 4) * 365 * 86400 for k in range(42 * 4)]   # giá quý 42 năm
    cl = [100 + k for k in range(len(ts))]
    monkeypatch.setattr(L.requests, "get", lambda *a, **k: R(ts, cl))
    out = L._stock_series("SPX", 30 * 365)
    assert 115 <= len(out) <= 122   # khoảng 30 năm giá quý
