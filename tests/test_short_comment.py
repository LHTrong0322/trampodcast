"""Trọng 23/11: short YouTube phải luôn có bình luận."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import social_schedule as S  # noqa: E402


def _w(p: Path, d: dict):
    p.write_text(json.dumps(d), encoding="utf-8")


def test_short_khong_ghi_binh_luan_thi_tu_tao_kem_link_video_dai(tmp_path):
    _w(tmp_path / "a.json", {"tag": "T1", "youtube": {"item": "long", "publish_at": "2026-11-21T12:25:00Z"}})
    _w(tmp_path / "a.state.json", {"yt_id": "LONG123"})
    plan = {"tag": "T1", "youtube": {"item": "short2", "publish_at": "2026-11-23T13:40:00Z"}}
    c = S.short_comment(plan, tmp_path)
    assert "https://youtu.be/LONG123" in c["comment"]
    assert c["comment_at"] == "2026-11-23T13:45:00Z"


def test_short_chua_co_video_dai_van_co_binh_luan(tmp_path):
    plan = {"tag": "T2", "youtube": {"item": "short1", "publish_at": "2026-11-23T13:40:00Z"}}
    assert "Smart Penguin Insights" in S.short_comment(plan, tmp_path)["comment"]


def test_khong_ghi_de_binh_luan_co_san_va_bo_qua_video_dai(tmp_path):
    assert S.short_comment({"tag": "T", "youtube": {"item": "short1", "publish_at": "2026-11-23T13:40:00Z", "comment": "x"}}, tmp_path) is None
    assert S.short_comment({"tag": "T", "youtube": {"item": "long", "publish_at": "2026-11-23T13:40:00Z"}}, tmp_path) is None
