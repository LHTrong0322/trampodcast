"""Review 27/11: giọng đọc "75 nghìn" bị chép thành "75.000" hoặc "bảy mươi lăm" nên thẻ hình lệch 1 câu."""
import insight_render as R


def _w(text):
    return [{"t": t, "s": i * 0.4} for i, t in enumerate(text.split())]


def test_khop_khi_so_bi_chep_khac():
    for text in ("tháng 6 . Bitcoin từ bảy mươi lăm nghìn đô hôm 9", "tháng 6 . Bitcoin từ 75.000 đô hôm 9"):
        b = R.beats_for([{"at": "Bitcoin từ 75 nghìn", "type": "bignum", "value": "$75K"}], _w(text), 20, {})
        assert b[0]["s"] == 1.2


def test_khop_dung_nguyen_van_van_nhu_cu():
    b = R.beats_for([{"at": "giá vốn", "type": "bignum", "value": "$53K"}], _w("chỉ còn cao hơn giá vốn trung bình"), 20, {})
    assert b[0]["s"] == 1.2
