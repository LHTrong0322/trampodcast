"""Luật trình bày (Trọng 23/11): nhãn so sánh dài, nguồn viết liền, thẻ chữ dài phải bị bắt trước khi dựng."""
import video_lint as VL


def test_versus_label_too_long():
    b = [{"type": "versus", "at": "x", "left": {"label": "Mỗi năm bỏ", "value": "$10K"},
          "right": {"label": "Sau 30 năm, lãi trung bình 10% mỗi năm", "value": "$1.6M"}}]
    assert any("nhãn right" in x for x in VL.layout_issues(b))


def test_bignum_source_split_not_counted():
    b = [{"type": "bignum", "at": "x", "value": "79%",
          "label": "quỹ chuyên gia Mỹ thua S&P 500 năm 2025. Nguồn: SPIVA 2025 (S&P Dow Jones Indices)"}]
    assert VL.layout_issues(b) == []


def test_source_inline_in_statement():
    b = [{"type": "flow", "at": "x", "label": "Các bước. Nguồn: HOSE", "steps": ["A", "B"]}]
    assert any("nguồn viết liền" in x for x in VL.layout_issues(b))


def test_clean_beats_pass():
    b = [{"type": "versus", "at": "x", "left": {"label": "VN30 năm 2012", "value": "447 điểm"},
          "right": {"label": "VN30 11/2026", "value": "1,855 điểm"}},
         {"type": "statement", "at": "y", "text": "ETF: mua bán như một cổ phiếu"}]
    assert VL.layout_issues(b) == []
