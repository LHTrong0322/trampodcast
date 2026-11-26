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


# Trọng 26/11 (ghi nhớ bằng code): nhắc dự án thì ảnh bìa phải có logo dự án; chủ đề khớp hình dán thì phải có hình dán.
COINS = {"HYPE": {"logo": "logos/HYPE.png", "name": "Hyperliquid", "color": "#50D2C1"},
         "AAVE": {"logo": "logos/AAVE.png", "name": "Aave", "color": "#B6509E"}}


def test_anh_bia_nhac_du_an_thi_co_logo():
    assert IP.subject_logo({"thumb_text": "Vì sao HYPE x2.5?"}, COINS)["logo"] == "logos/HYPE.png"
    assert IP.subject_logo({"title": "Aave còn đáng giữ không?"}, COINS)["logo"] == "logos/AAVE.png"
    assert IP.subject_logo({"thumb_logo": "AAVE", "thumb_text": "x"}, COINS)["logo"] == "logos/AAVE.png"


def test_khong_nhac_du_an_hoac_chi_dinh_penguin_thi_khong_gan_logo():
    assert IP.subject_logo({"thumb_text": "Cú rũ hay sụp đổ?"}, COINS) is None
    assert IP.subject_logo({"thumb_text": "Vì sao HYPE x2.5?", "thumb_subject": "penguin"}, COINS) is None


def test_chu_de_khop_thi_co_hinh_dan():
    assert IP.topic_icon({"thumb_text": "Bong bóng AI vỡ?"}) == "crack"
    assert IP.topic_icon({"thumb_text": "HYPE tăng mạnh"}) == "up"
    assert IP.topic_icon({"thumb_text": "Mua index fund"}) == "none"


def test_short_nhac_du_an_thi_co_logo():
    import short_covers as SC
    plan = {"sections": [{"heading": "h", "key_stat": "+150%", "key_label": ""}]}
    p = SC.props_for(plan, 0, "Vì sao HYPE tăng 150%?", {"HYPE": "logos/HYPE.png"})
    assert p["projectLogo"] == "logos/HYPE.png" and p["icon"] == "up"
    p2 = SC.props_for(plan, 0, "Lưới đỡ vừa biến mất", {"HYPE": "logos/HYPE.png"})
    assert p2["projectLogo"] is None
