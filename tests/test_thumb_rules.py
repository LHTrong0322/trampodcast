"""Trọng 26/11: ảnh bìa kiểu viral sạch (5 bố cục) và luật soát chữ ảnh bìa."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import insight_publish as IP  # noqa: E402
import video_lint as L  # noqa: E402


def test_chon_bo_cuc_theo_du_lieu():
    assert IP.thumb_style({"thumb_text": "a"}, False, False, True, has_before=True)[0] == "before"
    assert IP.thumb_style({"thumb_text": "b"}, True, False, False)[0] in ("vs", "question")
    assert IP.thumb_style({"thumb_text": "c"}, False, True, True)[0] in ("stat", "pill")
    assert IP.thumb_style({"thumb_text": "d"}, False, False, False)[0] == "question"


def test_kich_ban_chi_dinh_bo_cuc_thi_dung_dung_bo_cuc_do():
    assert IP.thumb_style({"thumb_style": "pill"}, False, False, True)[0] == "pill"
    assert IP.thumb_style({"thumb_style": "hero"}, False, False, True)[0] in ("stat", "question")   # bố cục cũ đã bỏ


def _lint_thumb(**kw):
    return [x for x in L.lint({"title": "t", "hook": "", "sections": [], **kw}) if "bìa" in x or "thumb" in x]


def test_lint_bat_chu_in_hoa_va_thieu_con_so():
    bad = _lint_thumb(thumb_text="AI BUBBLE ĐÃ VỠ?")
    assert any("IN HOA" in x for x in bad)
    assert any("nhân vật chính" in x for x in bad)


def test_lint_mau_dung_khong_bao_loi():
    assert _lint_thumb(thumb_text="Cú rũ hay sụp đổ?", thumb_stat="-$6T", thumb_tag="CÙNG ĐỎ") == []
