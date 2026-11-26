"""Trọng 23/11: short YouTube phải luôn có bình luận."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import social_schedule as S  # noqa: E402


def _w(p: Path, d: dict):
    p.write_text(json.dumps(d), encoding="utf-8")


def test_short_tu_tao_binh_luan_keo_ve_telegram_khong_link(tmp_path):
    """Trọng 26/11: bình luận YouTube có link bị ẩn, nên không gắn link nào, gắn link Telegram."""
    _w(tmp_path / "a.json", {"tag": "T1", "youtube": {"item": "long", "publish_at": "2026-11-21T12:25:00Z"}})
    _w(tmp_path / "a.state.json", {"yt_id": "LONG123"})
    plan = {"tag": "T1", "youtube": {"item": "short2", "publish_at": "2026-11-23T13:40:00Z"}}
    c = S.short_comment(plan, tmp_path)
    assert "youtu" not in c["comment"]
    assert "https://t.me/SmartPanda0322" in c["comment"]
    assert c["comment_at"] == "2026-11-23T13:45:00Z"


def test_lam_sach_binh_luan_cu_co_link_youtube():
    from social_upload import yt_comment_text
    t = yt_comment_text("Coin bạn hold qua mấy điều? Comment nhé 👇\n▶ Xem bản đầy đủ: https://youtu.be/MBh0-ZsFOuE")
    assert "youtu" not in t
    assert t.startswith("Coin bạn hold") and "https://t.me/SmartPanda0322" in t
    assert "{LONG_URL}" not in yt_comment_text("▶ Bản đầy đủ trên YouTube: {LONG_URL}")
    assert yt_comment_text("x").count("t.me/SmartPanda0322") == 1
    assert yt_comment_text(yt_comment_text("x")).count("t.me/SmartPanda0322") == 1


def test_khong_ghi_de_binh_luan_co_san_video_dai_cung_co_binh_luan(tmp_path):
    assert S.short_comment({"tag": "T", "youtube": {"item": "short1", "publish_at": "2026-11-23T13:40:00Z", "comment": "x"}}, tmp_path) is None
    assert "t.me/SmartPanda0322" in S.short_comment({"tag": "T", "youtube": {"item": "long", "publish_at": "2026-11-23T13:40:00Z"}}, tmp_path)["comment"]


def test_short_lay_link_video_dai_cung_ma(tmp_path):
    _w(tmp_path / "v.json", {"tag": "T9", "youtube": {"item": "long"}})
    _w(tmp_path / "v.state.json", {"yt_id": "AAA"})
    _w(tmp_path / "v-s1.json", {"tag": "T9", "youtube": {"item": "short1"}})
    _w(tmp_path / "v-s1.state.json", {"yt_id": "BBB"})
    assert S.long_url("T9", tmp_path) == "https://youtu.be/AAA"
    assert S.long_url("KHAC", tmp_path) is None


def test_facebook_va_tiktok_cung_keo_ve_telegram():
    """Trọng 26/11: mọi video FB, YouTube, TikTok đều có bình luận call to action về Telegram."""
    import social_upload as SU
    fb = SU.fb_link_comment("https://youtu.be/ABC")
    assert "youtu" not in fb and "https://t.me/SmartPanda0322" in fb
    assert SU.cta_comment("Câu hỏi? 👇\n💬 Telegram: https://t.me/SmartPanda0322").count("t.me/SmartPanda0322") == 1


def test_cta_chi_dung_1_cau():
    """Trọng 27/11: chỉ dùng đúng 1 câu call to action."""
    import social_upload as SU
    cs = {SU.pick_cta(f"tag{i}") for i in range(40)}
    assert cs == {"🐧 Cả nhà join group Telegram để nhận nhiều insights sớm hơn nhé 👉 https://t.me/SmartPanda0322"}
    assert not any(ch in c for c in SU.TELEGRAM_CTAS for ch in "\u2014\u2013")   # không gạch dài
