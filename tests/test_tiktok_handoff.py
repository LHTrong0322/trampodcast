"""Trọng 23/11: short lên lịch thì gửi sẵn video + caption TikTok qua Telegram."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import insight_publish as PB  # noqa: E402
import social_schedule as S  # noqa: E402


def test_caption_lay_tu_reel_va_bo_link():
    plan = {"facebook": {"item": "short1", "caption": "Câu hỏi? https://t.me/x #crypto"}}
    assert "https://" not in S.tiktok_caption(plan)
    assert S.tiktok_caption({"tiktok": {"caption": "riêng"}, "facebook": plan["facebook"]}) == "riêng"
    assert S.tiktok_caption({"facebook": {"item": "long", "caption": "x"}}) is None


def test_tat_gui_telegram_mac_dinh(tmp_path):
    plan = {"facebook": {"item": "short4", "publish_unix": 1795606200, "caption": "x"}}
    assert S.tiktok_handoff(plan, {"short4": tmp_path / "a.mp4"}, {}) is None


def test_gui_mot_lan_dung_gio_vn(monkeypatch, tmp_path):
    monkeypatch.setattr(S, "TIKTOK_TELEGRAM", True)
    sent = []
    monkeypatch.setattr(PB, "tg_video", lambda p, c: sent.append(c))
    monkeypatch.setattr(PB, "tg_text", lambda t: sent.append(t))
    plan = {"facebook": {"item": "short4", "publish_unix": 1795606200, "caption": "Nvidia P/E 9x"}}  # 25/11 11:30Z
    st = {}
    line = S.tiktok_handoff(plan, {"short4": tmp_path / "a.mp4"}, st)
    assert "T4 25/11 18:30" in line and st["tiktok_sent"]
    assert sent[1] == "Nvidia P/E 9x"
    assert "https://t.me/SmartPanda0322" in sent[2]   # 26/11: kèm bình luận kéo về Telegram
    assert S.tiktok_handoff(plan, {"short4": tmp_path / "a.mp4"}, st) is None   # không gửi lại


def test_video_dai_khong_gui():
    plan = {"youtube": {"item": "long", "publish_at": "2026-11-24T11:00:00Z"}, "facebook": {"item": "long", "caption": "x"}}
    assert S.tiktok_handoff(plan, {"long": "a.mp4"}, {}) is None
