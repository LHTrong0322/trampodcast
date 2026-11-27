"""Trọng 27/11 (audit kênh): Shorts chỉ khoảng 21% engaged view, video dài mất 50% người xem trong khoảng 20 giây đầu.
Luật hook: chữ trên hình giây 0 ngắn và có điểm gây tò mò, không mở bằng lời chào, video dài có lời hứa trong hook."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import video_lint as L  # noqa: E402


def _long(**kw):
    plan = {"title": "t", "hook": "Bitcoin quanh $55K. Hết video bạn sẽ biết vùng đáy nằm ở đâu.",
            "hook_screen": "BTC $55K: đáy hay bẫy?", "sections": [{"narration": "Phần một nói về giá."}], "shorts": []}
    plan.update(kw)
    return plan


def test_bat_loi_chao_o_dau():
    assert L.opens_with_greeting("Chào mừng mọi người đã quay trở lại với Smart Penguin Insights")
    assert L.opens_with_greeting("Xin chào các bạn, hôm nay")
    assert L.opens_with_greeting("Hôm nay chúng ta cùng tìm hiểu về Bitcoin")
    assert L.opens_with_greeting("Trong video này mình sẽ nói về HYPE")
    assert not L.opens_with_greeting("HYPE tăng 150% còn AAVE giảm 35%")
    assert not L.opens_with_greeting("Chỉ số này đang chỉ Bitcoin về $43K")


def test_hook_screen_ngan_va_co_diem_nhan():
    assert not L.hook_screen_issues(_long())
    assert any("8 từ" in x for x in L.hook_screen_issues(_long(hook_screen="Đây là một câu chữ trên hình rất dài dòng không ai đọc kịp")))
    assert any("con số" in x for x in L.hook_screen_issues(_long(hook_screen="đáy đã tới rồi")))
    assert not L.hook_screen_issues(_long(hook_screen="Nvidia bật mạnh"))      # tên lớn là đủ
    assert any("Thiếu hook_screen" in x for x in L.hook_screen_issues(_long(hook_screen="")))


def test_video_dai_phai_co_loi_hua():
    assert not any("lời hứa" in x for x in L.lint(_long()))
    assert any("lời hứa" in x for x in L.lint(_long(hook="Bitcoin đang quanh $55K và thị trường rất sợ hãi.")))
    assert not any("lời hứa" in x for x in L.lint(_long(format="short", hook="Bitcoin đang quanh $55K.")))


def test_lint_bat_loi_chao_o_hook_va_short():
    assert any("lời chào" in x for x in L.lint(_long(hook="Chào mừng mọi người, hết video bạn sẽ biết đáy ở đâu.")))
    plan = _long(sections=[{"narration": "Xin chào các bạn. HYPE tăng 150% còn AAVE giảm 35%."}], shorts=[0])
    assert any("Short 1" in x and "lời chào" in x for x in L.lint(plan))
    plan["short_spans"] = [{"from": "HYPE tăng 150%", "to": ""}]
    assert not any("Short 1" in x and "lời chào" in x for x in L.lint(plan))
