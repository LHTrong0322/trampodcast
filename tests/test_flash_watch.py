"""Lượt canh Telegram (news-flash-gate.yml loop=1) chỉ chạy khi còn kịch bản cần xử lý trong 24 giờ."""
import json
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import news_flash as NF  # noqa: E402


def _state(tmp_path, drafts):
    p = tmp_path / "state.json"
    p.write_text(json.dumps({"drafts": drafts}), encoding="utf-8")
    return p


def test_waiting_recent_is_watched(tmp_path):
    made = (NF.now_vn() - timedelta(hours=3)).isoformat()
    assert NF.watching(_state(tmp_path, {"a": {"status": "waiting", "created": made}})) == "yes"


def test_approved_not_built_is_watched(tmp_path):
    made = NF.now_vn().isoformat()
    assert NF.watching(_state(tmp_path, {"a": {"status": "approved", "created": made}})) == "yes"


def test_old_or_done_is_not_watched(tmp_path):
    old = (NF.now_vn() - timedelta(hours=30)).isoformat()
    new = NF.now_vn().isoformat()
    drafts = {"a": {"status": "waiting", "created": old}, "b": {"status": "built", "created": new},
              "c": {"status": "waiting", "created": "hỏng"}}
    assert NF.watching(_state(tmp_path, drafts)) == "no"


def test_missing_state_is_not_watched(tmp_path):
    assert NF.watching(tmp_path / "khong-co.json") == "no"
