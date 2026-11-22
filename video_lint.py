"""Kiểm tra khung video TRƯỚC khi dựng (Trọng 22/11: đẩy mọi tiêu chí bot review lên ít nhất 7/10).

Bắt các lỗi mà bot review vòng 2 hay trừ điểm, dựa trên kịch bản JSON:
- Nhịp độ: khoảng trống giữa hai lần đổi hình quá dài, thẻ câu hỏi đứng trơ, cả video không có biểu đồ, câu "đắt" không được làm nổi.
- Dữ liệu đúng ý: lời đọc nói "bốn thứ" mà hình không có đủ 4 ý, hứa N câu hỏi mà phần tóm tắt khác N.
- Ảnh bìa và video ngắn: chữ ảnh bìa quá dài, thiếu nhãn phụ, tiêu đề short không có số hoặc câu hỏi.

Dùng:  python video_lint.py scripts/<ten>-approved.json
"""
from __future__ import annotations

import json
import re
import sys

WPS = 3.3          # giọng Ludo KOL đọc khoảng 200 từ/phút
GAP_MAX = 26       # khoảng 8 giây không đổi hình là người xem bắt đầu lướt
NUM = {"hai": 2, "ba": 3, "bốn": 4, "tư": 4, "năm": 5, "sáu": 6}


def _words(t: str) -> list[str]:
    return re.findall(r"[\w%$]+", (t or "").lower())


def _find(words: list[str], phrase: str) -> int:
    p = _words(phrase)
    if not p:
        return -1
    for i in range(len(words) - len(p) + 1):
        if words[i:i + len(p)] == p:
            return i
    return -1


def _anchors(words: list[str], beats: list[dict]) -> list[tuple[int, dict]]:
    out = []
    for b in beats or []:
        i = _find(words, b.get("at", ""))
        if i >= 0:
            out.append((i, b))
        for s in b.get("step_at") or []:
            j = _find(words, s)
            if j >= 0:
                out.append((j, {"type": "step"}))
    return sorted(out, key=lambda x: x[0])


def lint(plan: dict) -> list[str]:
    bad: list[str] = []
    secs = plan.get("sections") or []
    all_beats = list(plan.get("hook_beats") or [])
    for k, s in enumerate(secs, 1):
        w = _words(s.get("narration", ""))
        beats = s.get("beats") or []
        all_beats += beats
        for b in beats:
            if b.get("at") and _find(w, b["at"]) < 0:
                bad.append(f"Phần {k}: hình '{b.get('type')}' gắn với cụm '{b['at']}' nhưng lời đọc không có cụm này, hình sẽ hiện sai lúc.")
        an = _anchors(w, beats)
        if not an:
            bad.append(f"Phần {k}: không có hình nào đổi theo lời đọc ({len(w)} từ, khoảng {len(w) / WPS:.0f} giây đứng yên).")
            continue
        marks = [0] + [i for i, _ in an] + [len(w)]
        if an[0][0] > 12:
            bad.append(f"Phần {k}: {an[0][0] / WPS:.0f} giây đầu chưa có hình, cho hình đầu tiên hiện ngay câu đầu.")
        for a, b in zip(marks[1:], marks[2:]):
            if (b - a) / WPS > 8.4:
                seg = " ".join(w[a:a + 6])
                bad.append(f"Phần {k}: từ '{seg}...' có {(b - a) / WPS:.0f} giây không đổi hình (tối đa 8 giây), thêm 1 hình số liệu hoặc ví dụ.")
        for b in beats:
            if b.get("type") == "question":
                bad.append(f"Phần {k}: thẻ câu hỏi '{b.get('text', '')}' không có dữ liệu (review 22/11 trừ điểm), thay bằng số liệu, biểu đồ hoặc logo kèm số.")
        for n, (i, b) in enumerate(an):
            if b.get("type") == "question":
                nxt = an[n + 1][0] if n + 1 < len(an) else len(w)
                if nxt - i > 18:
                    bad.append(f"Phần {k}: thẻ câu hỏi đứng một mình {(nxt - i) / WPS:.0f} giây, cho số liệu hoặc ví dụ hiện sớm hơn.")
        for m in re.finditer(r"\b(hai|ba|bốn|tư|năm|sáu|[2-6])\s+(thứ|điều|ý|bước|yếu tố|tiêu chí|lý do|dấu hiệu)\b", s.get("narration", "").lower()):
            n = NUM.get(m.group(1)) or int(m.group(1))
            sizes = [len(b.get("steps") or b.get("items") or b.get("coins") or []) for b in beats]
            if n not in sizes and len(s.get("bullets") or []) != n:
                bad.append(f"Phần {k}: lời đọc nói '{m.group(0)}' nhưng không có hình nào hiện đủ {n} ý.")
    if not any(b.get("type") in ("chart", "race", "wma") for b in all_beats):
        bad.append("Cả video chưa có biểu đồ giá nào. Thêm ít nhất 1 hình 'race' hoặc 'chart' (giá thật của coin đang nói tới).")
    types = [b.get("type") for b in all_beats]
    if types and max(types.count(t) for t in set(types)) > max(4, len(types) * 0.4):
        bad.append("Một kiểu hình lặp quá nhiều, đổi bớt sang kiểu khác (versus, chart, dots, flow, logos).")
    hook = plan.get("hook", "")
    m = re.search(r"\b(hai|ba|bốn|năm|sáu|[2-6])\s+câu hỏi", hook.lower())
    if m:
        n = NUM.get(m.group(1)) or int(m.group(1))
        if plan.get("outro_points") and len(plan["outro_points"]) != n:
            bad.append(f"Hook hứa {n} câu hỏi nhưng phần tóm tắt có {len(plan['outro_points'])} ý.")
        q = re.search(r"câu (số )?(\d)", hook.lower())
        if q and int(q.group(2)) <= len(secs) and not secs[int(q.group(2)) - 1].get("emphasis"):
            bad.append(f"Hook nhắc riêng câu số {q.group(2)} nhưng phần đó chưa được làm nổi (thêm \"emphasis\": \"CÂU NGƯỜI TA BỎ QUA\").")
    if len(_words(hook)) > 42:
        bad.append(f"Hook dài {len(_words(hook))} từ (khoảng {len(_words(hook)) / WPS:.0f} giây), nên dưới 40 từ.")
    tt = plan.get("thumb_text", "")
    if len(tt) > 24:
        bad.append(f"Chữ ảnh bìa '{tt}' dài {len(tt)} ký tự, nên tối đa 24 để đọc được khi thu nhỏ.")
    if plan.get("thumb_vs") and not plan.get("thumb_tag"):
        bad.append("Ảnh bìa có bảng so sánh nhưng thiếu nhãn phụ thumb_tag (vd '4 CÂU HỎI TRƯỚC KHI MUA').")
    for key, h in (plan.get("short_hooks") or {}).items():
        if not re.search(r"\d|\?", h):
            bad.append(f"Tiêu đề short phần {int(key) + 1} '{h}' không có con số hay câu hỏi, khó gây tò mò.")
        if len(h) > 60:
            bad.append(f"Tiêu đề short phần {int(key) + 1} dài {len(h)} ký tự, nên dưới 60.")
    return bad


if __name__ == "__main__":
    issues = lint(json.loads(open(sys.argv[1], encoding="utf-8").read()))
    print("\n".join(f"- {x}" for x in issues) if issues else "Khung ổn, không thấy lỗi.")
