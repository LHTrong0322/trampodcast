"""Trọng 27/11: câu đầu short cấm mở bằng tên tác giả, đoạn đầu short luôn là highlight."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import video_lint as L  # noqa: E402


def test_bat_cau_mo_bang_ten_tac_gia():
    assert L.opens_with_author("Kyle gọi crypto là một thị trường chanh")
    assert L.opens_with_author("Theo @zeroxkyle, altcoin sắp về 0")
    assert L.opens_with_author("zeroxkyle vừa chỉ ra 3 tiêu chí", {"zeroxkyle"})


def test_khong_bat_nham_cau_highlight():
    assert not L.opens_with_author("95% altcoin sẽ về 0 trong chu kỳ này")
    assert not L.opens_with_author("Nvidia vừa đưa Jensen Huang trở lại ghế CEO")
    assert not L.opens_with_author("Bitcoin về $55K: đáy thật hay bẫy?", {"kyle"})


def test_lint_short_khong_co_hook_thi_xet_dau_loi_doc():
    plan = {"title": "t", "hook": "", "posts": [{"author": "Kyle", "handle": "zeroxkyle"}],
            "sections": [{"narration": "Kyle gọi crypto là thị trường chanh. 4 dấu hiệu coin rác..."}], "shorts": [0]}
    assert any("tên tác giả" in x for x in L.lint(plan))
    plan["short_hooks"] = {"0": "4 dấu hiệu coin rác bạn cần tránh?"}
    assert any("câu đọc đầu tiên" in x for x in L.lint(plan))   # tiêu đề ổn nhưng câu nghe đầu vẫn là tên tác giả
    plan["short_spans"] = [{"from": "4 dấu hiệu coin rác", "to": ""}]
    assert not any("tên tác giả" in x for x in L.lint(plan))
