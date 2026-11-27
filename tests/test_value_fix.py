"""Trọng 27/11: câu/thẻ KHÔNG ĐÁNG phải được viết lại ngay, nhưng không được bịa số hay làm hỏng thẻ hình."""
import json

import value_fix as VF

OLD = {"hook": "ETF bị rút gần 5 tỷ đô.", "description": "Quý 3 hút vào $6.34B.",
       "sections": [{"narration": "ETF bị rút gần 5 tỷ đô trong tháng 11. Cổ phiếu AI bị bán tháo. Bạn nghĩ sao?",
                     "beats": [{"at": "ETF bị rút", "type": "bignum", "value": "-$4.94B"}], "bullets": []}]}
NAR = ("ETF bị rút gần 5 tỷ đô trong tháng 11. Quý 3 các quỹ hút vào 6,34 tỷ đô, giờ đã bị xoá sạch. " * 4
       + "Bạn nghĩ sao? Bình luận cho mình nhé.")


def test_loc_loi_khong_dang():
    rv = {"can_sua": ["KHÔNG ĐÁNG: thẻ 2 lặp phụ đề", "chữ hơi nhỏ"]}
    pre = {"issues": [{"problem": "KHÔNG ĐÁNG: câu đệm"}, {"problem": "font"}]}
    assert VF.problems_from(rv, pre) == ["KHÔNG ĐÁNG: thẻ 2 lặp phụ đề", "KHÔNG ĐÁNG: câu đệm"]


def test_so_moi_chua_kiem_chung_van_dung():
    """Trọng 27/11 14:10: số chưa kiểm chứng được vẫn dùng, chỉ chặn số đã kiểm chứng ra sai."""
    new = {"narration": NAR + " Giá có thể về 42 nghìn.", "beats": [{"at": "ETF bị rút", "type": "bignum"}]}
    assert VF.validate(OLD, new) == ""
    assert "sai" in VF.validate(OLD, new, wrong=[{"value": "42 nghìn"}])


def test_chan_the_khong_bam_loi_doc():
    new = {"narration": NAR, "beats": [{"at": "câu không tồn tại", "type": "bignum"}]}
    assert "cụm không có" in VF.validate(OLD, new)


def test_chan_gach_dai():
    new = {"narration": NAR.replace(". Quý", " \u2014 Quý", 1), "beats": [{"at": "ETF bị rút", "type": "bignum"}]}
    assert VF.validate(OLD, new)


def test_viet_lai_hop_le():
    fake = lambda prompt: {"narration": NAR, "beats": [{"at": "Quý 3 các quỹ", "type": "versus"}],
                           "changes": [{"cu": "Cổ phiếu AI bị bán tháo.", "moi": "Quý 3 ...", "ly_do": "lặp"}]}
    new, ch, why = VF.rewrite(json.loads(json.dumps(OLD)), ["KHÔNG ĐÁNG: câu 2"], run=fake)
    assert why == "" and new["sections"][0]["narration"] == NAR and ch[0]["cu"]


def test_claude_loi_thi_giu_ban_cu():
    def boom(prompt):
        raise RuntimeError("hết lượt")
    new, ch, why = VF.rewrite(OLD, ["x"], run=boom)
    assert new is None and "lỗi" in why


FACT = {"value": "$53K", "claim": "giá vốn trung bình toàn thị trường", "url": "https://cointelegraph.com/x",
        "source": "Cointelegraph", "quote": "realized price near $53,000"}


def _writer(prompt):
    return {"narration": NAR + " Giá vốn trung bình khoảng 53 nghìn đô.", "beats": [{"at": "Quý 3 các quỹ", "type": "versus"}],
            "changes": [{"cu": "a", "moi": "b", "ly_do": "c"}], "new_facts": [FACT]}


def test_so_moi_co_nguon_da_kiem_chung_thi_duoc_dung():
    ok = lambda prompt: {"results": [{"i": 0, "ok": True}]}
    new, ch, why = VF.rewrite(json.loads(json.dumps(OLD)), ["x"], run=_writer, check=ok)
    assert why == "" and new["sources"][0]["url"].startswith("https") and any("kiểm chứng" in c["ly_do"] for c in ch)


def test_so_moi_kiem_chung_ra_sai_thi_giu_ban_cu():
    bad = lambda prompt: {"results": [{"i": 0, "verdict": "sai", "why": "giá vốn thật là $45K"}]}
    new, ch, why = VF.rewrite(json.loads(json.dumps(OLD)), ["x"], run=_writer, check=bad)
    assert new is None and "kiểm chứng ra sai" in why


def test_so_moi_chua_kiem_chung_duoc_van_dung():
    """Trọng 27/11 14:10: tra không ra nguồn (hoặc không có link) không phải là sai, vẫn dùng và ghi chú."""
    unk = lambda prompt: {"results": [{"i": 0, "verdict": "chua_ro", "why": "không tìm thấy bài"}]}
    new, ch, why = VF.rewrite(json.loads(json.dumps(OLD)), ["x"], run=_writer, check=unk)
    assert why == "" and new is not None and any("chưa kiểm chứng" in c["ly_do"] for c in ch)
    nolink = lambda prompt: {**_writer(prompt), "new_facts": [{**FACT, "url": ""}]}
    new, ch, why = VF.rewrite(json.loads(json.dumps(OLD)), ["x"], run=nolink, check=lambda p: {"results": []})
    assert why == "" and new is not None


def test_kieu_tra_cu_ok_false_khong_coi_la_sai():
    old_style = lambda prompt: {"results": [{"i": 0, "ok": False, "why": "bài không có số này"}]}
    good, wrong = VF.verify([FACT], run=old_style)
    assert good == [] and wrong == []


def test_chan_the_sai_khung():
    """Trọng 27/11: bot viết lại để thẻ versus có left/right là chữ, dựng lỗi 'str' object has no attribute 'get'."""
    bad = {"narration": NAR, "beats": [{"at": "ETF bị rút", "type": "versus", "left": "Quý 3", "right": "Tháng 11"}]}
    assert "sai khung" in VF.validate(OLD, bad)
    bad2 = {"narration": NAR, "beats": [{"at": "ETF bị rút", "type": "logos", "items": ["BTC"]}]}
    assert "sai khung" in VF.validate(OLD, bad2)
    ok = {"narration": NAR, "beats": [{"at": "ETF bị rút", "type": "versus", "left": {"label": "Quý 3"}, "right": {"label": "Tháng 11"}}]}
    assert VF.validate(OLD, ok) == ""
