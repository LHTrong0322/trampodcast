"""Bản dựng có kèm bản nháp giọng dự phòng: đăng luôn phải lấy bản chính."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import social_post as SP  # noqa: E402


def test_bo_qua_ban_nhap(tmp_path, monkeypatch):
    names = ["x-nhap-haidang-16x9.mp4", "x-16x9.mp4", "x-nhap-haidang-short1-9x16.mp4", "x-short1-9x16.mp4",
             "x-short2-9x16.mp4", "thumbnail-x.png", "seo-x.json"]

    def fake_run(*a, **k):
        for n in names:
            (tmp_path / n).write_text("{}")
    monkeypatch.setenv("GITHUB_REPOSITORY", "a/b")
    monkeypatch.setattr(SP.subprocess, "run", fake_run)
    rel = SP.fetch_release("x", tmp_path)
    assert rel["long"].name == "x-16x9.mp4"
    assert rel["short1"].name == "x-short1-9x16.mp4"
