"""Trọng 28/11: máy dựng gọi công cụ tạo ảnh của Google (Gemini) cho thẻ photo có "gen"."""
import base64
import io
import json

from PIL import Image

import insight_lab as L


class FakeGem:
    key = "k"

    def __init__(self, ok=True):
        self.ok, self.calls = ok, []

    def _post(self, model, body, timeout=0):
        self.calls.append(model)
        if not self.ok:
            raise RuntimeError("429")
        b = io.BytesIO()
        Image.new("RGB", (64, 36), "navy").save(b, "PNG")
        return {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": base64.b64encode(b.getvalue()).decode()}}]}}]}


def test_the_photo_gen_tao_anh(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "_IMG_MODELS", ["img-model"])
    plan = {"sections": [{"beats": [{"type": "photo", "at": "x", "label": "Bãi biển", "gen": "a beach"}]}]}
    L.photo_beats(tmp_path, plan, FakeGem(), {"insight": {"ai_images": True}})
    b = plan["sections"][0]["beats"][0]
    assert b["src"].startswith("img/gen_") and (tmp_path / b["src"]).exists()
    assert "AI" in plan["image_credits"][b["src"][4:]]


def test_tao_anh_loi_thi_ve_the_chu(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "_IMG_MODELS", ["img-model"])
    plan = {"sections": [{"beats": [{"type": "photo", "at": "x", "label": "Bãi biển", "gen": "a beach"}]}]}
    monkeypatch.setattr(L.V, "search_google", lambda q, o: None)
    monkeypatch.setattr(L.V, "search_wikimedia", lambda q, o: None)
    L.photo_beats(tmp_path, plan, FakeGem(ok=False), {"insight": {"ai_images": True}})
    b = plan["sections"][0]["beats"][0]
    assert b["type"] == "statement" and b["text"] == "Bãi biển"


def test_mac_dinh_khong_tao_anh_ai_va_khong_dung_anh_kho(tmp_path, monkeypatch):
    """Trọng 28/11: không cần ảnh AI, bỏ ảnh kho; chỉ tìm Google (giấy phép mở) rồi Wikimedia."""
    called = []
    monkeypatch.setattr(L.V, "search_google", lambda q, o: called.append(("g", q)))
    monkeypatch.setattr(L.V, "search_wikimedia", lambda q, o: called.append(("w", q)))
    monkeypatch.setattr(L.V, "search_pixabay", lambda q, o: (_ for _ in ()).throw(AssertionError("ảnh kho")))
    gem = FakeGem()
    plan = {"sections": [{"beats": [{"type": "photo", "at": "x", "label": "1929", "gen": "x", "query": "1929 crash"}]}]}
    L.photo_beats(tmp_path, plan, gem, {})
    assert gem.calls == [] and ("g", "1929 crash") in called
