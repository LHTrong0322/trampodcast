"""Trọng 28/11: chữ trên hình sai chính tả phải được sửa trước khi dựng."""
import spell_fix as SF

PROPS = {"shortTitle": "Lý thuyêt Dow", "data": {"x": "Lý thuyêt"},
         "scenes": [{"type": "section", "heading": "Lý thuyêt Dow và xu hướng", "images": ["img/Lý thuyêt.png"],
                     "beats": [{"type": "statement", "at": "Lý thuyêt Dow", "text": "Lý thuyêt Dow"}],
                     "words": [{"t": "Lý", "s": 0}, {"t": "thuyêt", "s": 0.3}, {"t": "Dow.", "s": 0.6}]}]}


def test_sua_chu_tren_the_va_phu_de():
    SF._CACHE.clear()
    run = lambda pr: {"sua": [{"sai": "thuyêt", "dung": "thuyết"}]}
    p, lines = SF.check(PROPS, run=run, log=lambda *a: None)
    sc = p["scenes"][0]
    assert p["shortTitle"] == "Lý thuyết Dow" and sc["heading"].startswith("Lý thuyết")
    assert sc["beats"][0]["text"] == "Lý thuyết Dow" and sc["words"][1]["t"] == "thuyết"
    assert sc["beats"][0]["at"] == "Lý thuyêt Dow"          # "at" là cụm để bám giọng đọc: không đụng
    assert sc["images"] == ["img/Lý thuyêt.png"] and p["data"]["x"] == "Lý thuyêt"
    assert lines == ["thuyêt → thuyết"]


def test_claude_loi_thi_giu_nguyen():
    SF._CACHE.clear()
    def boom(pr):
        raise RuntimeError("hết lượt")
    p, lines = SF.check(PROPS, run=boom, log=lambda *a: None)
    assert p is PROPS and lines == []


def test_khong_nhan_gach_dai():
    SF._CACHE.clear()
    p, lines = SF.check(PROPS, run=lambda pr: {"sua": [{"sai": "Dow", "dung": "Dow — x"}]}, log=lambda *a: None)
    assert lines == []
