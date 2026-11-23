"""Đọc số tiếng Việt cho giọng máy (Trọng 23/11: phụ đề chữ số, giọng đọc chữ; S&P 500 đọc 'ét en pi năm trăm')."""
import vi_num as N


def test_numbers():
    for x, want in [("94", "chín mươi tư"), ("21", "hai mươi mốt"), ("15", "mười lăm"), ("105", "một trăm lẻ năm"),
                    ("1957", "một nghìn chín trăm năm mươi bảy"), ("2025", "hai nghìn không trăm hai mươi lăm"),
                    ("0.03", "không phẩy không ba"), ("6,910", "sáu nghìn chín trăm mười"), ("1.6", "một phẩy sáu")]:
        assert N.read_number(x) == want


def test_sentence_keeps_codes():
    t = N.say_numbers("S&P 500 tăng 10 phần trăm, VN30 vẫn giữ")
    assert t.startswith("ét en pi năm trăm tăng mười phần trăm") and "VN30" in t
