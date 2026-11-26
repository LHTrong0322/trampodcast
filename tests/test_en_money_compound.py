"""Review 26/11: phụ đề ghi "4B $940M" thay vì "$4.94B"."""
import video as V


def test_so_kep():
    assert V.en_money("rút ròng 4 tỷ 940 triệu đô la trong tháng 11") == "rút ròng $4.94B trong tháng 11"
    assert V.en_money("kỷ lục cũ là 4 tỷ 510 triệu, hồi tháng 6") == "kỷ lục cũ là 4.51B, hồi tháng 6"
    assert V.en_money("2 tỷ 50 triệu đô") == "$2.05B"
    assert V.en_money("1 triệu 200 nghìn đô la") == "$1.2M"


def test_khong_doi_so_don():
    assert V.en_money("59 nghìn đô la") == "$59K"
    assert V.en_money("4,94 tỷ đô la") == "$4.94B"
