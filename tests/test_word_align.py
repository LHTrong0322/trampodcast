"""Trọng 28/11: thẻ hình và phụ đề phải bám giây THẬT của giọng đọc."""
import word_align as WA


def test_khop_theo_giong_that():
    script = "Charles Dow lập Wall Street Journal năm 1889".split()
    heard = [(0.0, 0.4, "Charles"), (0.4, 0.7, "Dow"), (0.7, 1.0, "lập"), (3.0, 3.3, "Wall"), (3.3, 3.6, "Street"),
             (3.6, 4.0, "Journal"), (4.0, 4.2, "năm"), (4.2, 5.5, "một nghìn tám trăm tám mươi chín")]
    w = WA.align(script, heard, 6.0)
    assert [x["t"] for x in w] == script
    assert w[3]["s"] == 3.0          # "Wall" đúng giây giọng đọc (cách ước cũ sẽ đặt khoảng 1.5s)
    assert abs(w[7]["s"] - 4.2) < 0.01   # số đọc thành chữ vẫn khớp


def test_chu_khong_nghe_ra_thi_noi_suy():
    script = "BTC tăng XYZQ mạnh".split()
    heard = [(0.0, 0.5, "BTC"), (0.5, 1.0, "tăng"), (2.0, 2.5, "mạnh")]
    w = WA.align(script, heard, 3.0)
    assert 1.0 <= w[2]["s"] < 2.0 and w[3]["s"] == 2.0


def test_nghe_lech_qua_nhieu_thi_tra_none():
    assert WA.align("một hai ba bốn năm".split(), [(0, 1, "xin chào các bạn")], 2.0) is None
