"""Lỗi 26/11: prompt viết kịch bản có dấu ngoặc nhọn chưa thoát ({"label", "value"}) làm PROMPT.format hỏng, mọi lượt dựng video chết ngay bước viết kịch bản."""
import insight_lab as L


def test_prompt_format_khong_loi():
    out = L.PROMPT.format(posts="x", minutes=1, max_sections=1)
    assert '{"label", "value"}' in out
