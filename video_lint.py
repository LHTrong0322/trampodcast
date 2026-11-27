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


# Trọng 23/11: "lỗi font, lỗi dựng nhiều, chữ xấu, không thẳng hàng, nguồn viết liền". Luật trình bày soát TRƯỚC khi dựng,
# để bot sửa kịch bản (insight_improve) tự sửa luôn, không đợi Trọng phát hiện.
LIMITS = {"vs_label": 26, "vs_value": 11, "bignum_label": 60, "statement": 56, "flow_step": 24, "dots_label": 48}


def layout_issues(beats: list) -> list[str]:
    bad = []
    for b in beats:
        t, at = b.get("type"), b.get("at", "")
        lab = str(b.get("label") or "")
        if re.search(r"\bnguồn\s*:|\bsource\s*:", lab, re.I) and t not in ("bignum", "dots"):
            bad.append(f"Hình '{at}': nguồn viết liền trong chú thích '{lab[:40]}...'. Tách ra trường \"source\" (hiện chữ nhỏ dòng riêng).")
        if t == "versus":
            # Trọng 24/11: "SEC: Đang điều tra VS California: Đang điều tra" là VS vô nghĩa; so sánh phải là 2 con số
            vals = [str((b.get(sd) or {}).get("value", "")) for sd in ("left", "right")]
            if not all(re.search(r"\d", v) for v in vals):
                bad.append(f"Hình so sánh '{at}': giá trị '{vals[0]}' / '{vals[1]}' không phải con số, VS vô nghĩa. Dùng thẻ chữ hoặc 2 số thật.")
            ls = [len(str((b.get(sd) or {}).get("label", ""))) for sd in ("left", "right")]
            if max(ls) > 16 and min(ls) <= 16:
                bad.append(f"Hình so sánh '{at}': nhãn 2 bên lệch độ dài ({ls[0]} và {ls[1]} ký tự) nên lệch dòng, viết cả 2 nhãn ≤ 16 ký tự.")
            for side in ("left", "right"):
                x = b.get(side) or {}
                if len(str(x.get("label", ""))) > LIMITS["vs_label"]:
                    bad.append(f"Hình so sánh '{at}': nhãn {side} '{x.get('label')}' dài {len(str(x.get('label')))} ký tự (tối đa {LIMITS['vs_label']}), viết gọn lại.")
                if len(str(x.get("value", ""))) > LIMITS["vs_value"]:
                    bad.append(f"Hình so sánh '{at}': số {side} '{x.get('value')}' quá dài (tối đa {LIMITS['vs_value']} ký tự), số to sẽ bị co nhỏ.")
        if t == "bignum" and len(splitless(lab)) > LIMITS["bignum_label"]:
            bad.append(f"Thẻ số '{at}': chú thích dài {len(lab)} ký tự (tối đa {LIMITS['bignum_label']}), rút gọn, nguồn để trường \"source\".")
        if t == "statement" and len(str(b.get("text", ""))) > LIMITS["statement"]:
            bad.append(f"Thẻ chữ '{at}': {len(str(b.get('text')))} ký tự (tối đa {LIMITS['statement']}), câu dài xuống dòng xấu.")
        if t == "flow":
            for st in b.get("steps") or []:
                if len(str(st)) > LIMITS["flow_step"]:
                    bad.append(f"Hình các bước '{at}': bước '{st}' dài quá {LIMITS['flow_step']} ký tự.")
        if t == "photo" and re.search(r"\b(jensen|huang|trump|musk|powell|saylor|vitalik|biden|gensler|bessent)\b", str(b.get("query", "")), re.I):
            bad.append(f"Ảnh '{at}': từ khoá '{b.get('query')}' có tên người thật, video không dùng ảnh người thật lấy từ mạng. Đổi sang cảnh/đồ vật chung.")
        if t == "statement" and str(b.get("text", "")).rstrip().endswith("?"):
            pass
        if t == "dots" and len(splitless(lab)) > LIMITS["dots_label"]:
            bad.append(f"Hình chấm '{at}': chú thích dài quá {LIMITS['dots_label']} ký tự.")
    return bad


def splitless(lab: str) -> str:
    """Chú thích đã bỏ phần nguồn (khuôn hình tự tách 'Nguồn: ...' xuống dòng nhỏ)."""
    return re.split(r"[.,;]?\s*(?:Nguồn|Source)\s*:", lab, flags=re.I)[0].strip()


# Trọng 27/11: câu đầu short CẤM mở bằng tên tác giả; đoạn đầu short luôn là HIGHLIGHT (con số sốc, nghịch lý,
# kết luận bất ngờ) để tạo tò mò giữ chân người xem. Bằng chứng: short "coin rác" mở "Kyle gọi crypto là..." chỉ 4,5% ở lại xem.
_SAY = r"(?:gọi|nói|cho rằng|chia sẻ|viết|nhận định|bảo|tin rằng|khẳng định|vừa đăng|phân tích|chỉ ra|đưa ra)"
_AUTHOR_OPEN = re.compile(rf"^\W*(?:[Tt]heo\s+)?@?[A-ZĐ][\wÀ-ỹ.]*(?:\s+[A-ZĐ][\wÀ-ỹ.]*)?\s+{_SAY}\b|^\W*(?:[Tt]heo\s+)?@\w+", re.U)


def _authors(plan: dict) -> set[str]:
    names = set()
    posts = list(plan.get("posts") or []) + [plan.get("source_post") or {}]
    for p in posts:
        if isinstance(p, dict):
            names |= {str(p.get(k) or "") for k in ("author", "handle")}
    names |= {str(x) for x in (plan.get("authors") or [])} | {str(plan.get("source_label") or "")}
    return {n.lstrip("@").lower() for n in names if len(n.lstrip("@")) >= 3}


def opens_with_author(text: str, authors: set[str] | None = None) -> bool:
    """Câu mở có bắt đầu bằng tên tác giả / @handle không (xét 5 từ đầu)."""
    t = (text or "").strip()
    if not t:
        return False
    if _AUTHOR_OPEN.search(t):
        return True
    head = " ".join(re.findall(r"[\w@.]+", t.lower())[:5]).replace("@", "")
    return any(re.search(rf"(?<![\w]){re.escape(a)}(?![\w])", head) for a in (authors or set()))


def short_open_issues(plan: dict) -> list[str]:
    """Câu đầu tiên người xem nghe trong mỗi short: short_hooks nếu có, không thì cụm bắt đầu short_spans / đầu lời đọc phần."""
    bad, au = [], _authors(plan)
    secs = plan.get("sections") or []
    hooks = plan.get("short_hooks") or {}
    spans = plan.get("short_spans") or []
    for n, i in enumerate(plan.get("shorts") or []):
        if not isinstance(i, int) or not 0 <= i < len(secs):
            continue
        h = str(hooks.get(str(i)) or hooks.get(i) or "")
        sp = spans[n] if n < len(spans) and isinstance(spans[n], dict) else {}
        narr = str(secs[i].get("narration") or "")
        # dựng từ kịch bản duyệt: short_hooks chỉ là tiêu đề trên hình, câu NGHE đầu tiên là đầu short_spans (hoặc đầu lời đọc phần)
        spoken = narr[narr.find(sp["from"]):] if sp.get("from") and sp["from"] in narr else narr
        for what, first in (("tiêu đề/câu mở", h), ("câu đọc đầu tiên", spoken)):
            if opens_with_author(first, au):
                bad.append(f"Short {n + 1}: {what} mở bằng tên tác giả ('{first[:50]}'). Đoạn đầu short phải là highlight gây tò mò "
                           f"(con số sốc, nghịch lý, kết luận bất ngờ), tên tác giả để sau; chỉnh short_spans 'from' hoặc lời đọc.")
    return bad


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
        gap_max = 5.5 if plan.get("format") == "short" else 8.4   # Trọng 24/11: short đổi hình 3 đến 5 giây như video đã duyệt
        # Trọng 27/11: "dựng chart nhiều hơn": biểu đồ có lời đọc giải thích được giữ lâu hơn (tối đa 22 giây, short 12 giây)
        chart_max = 12 if plan.get("format") == "short" else 22
        kind = {i: x.get("type") for i, x in an}
        for a, b in zip(marks[1:], marks[2:]):
            lim = chart_max if kind.get(a) in ("dow", "wma", "chart", "trend", "race") else gap_max
            if (b - a) / WPS > lim:
                seg = " ".join(w[a:a + 6])
                bad.append(f"Phần {k}: từ '{seg}...' có {(b - a) / WPS:.0f} giây không đổi hình (tối đa {lim:.0f} giây), thêm 1 hình số liệu, ảnh hoặc ví dụ.")
        for b in beats[:-1]:   # Trọng 24/11: câu hỏi mời comment ở thẻ CUỐI thì được (review muốn thẻ ?, không dùng thẻ trích dẫn)
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
    if not any(b.get("type") in ("chart", "race", "wma", "trend", "dow") for b in all_beats):
        bad.append("Cả video chưa có biểu đồ giá nào. Thêm ít nhất 1 hình 'race' hoặc 'chart' (giá thật của coin đang nói tới).")
    bad += layout_issues(all_beats)
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
        bad.append("Ảnh bìa có bảng so sánh nhưng thiếu nhãn phụ thumb_tag (vd 'vẫn lỗ?').")
    # Trọng 26/11: ảnh bìa kiểu viral sạch (remotion/src/Thumb.tsx)
    letters = re.sub(r"[^A-Za-zÀ-ỹ]", "", tt)
    if len(letters) >= 8 and letters == letters.upper():
        bad.append(f"Chữ ảnh bìa '{tt}' đang IN HOA cả câu, kiểu mới viết thường có dấu như câu nói (vd 'Cú rũ hay sụp đổ?').")
    if not (plan.get("thumb_stat") or plan.get("thumb_vs") or plan.get("thumb_before")):
        bad.append("Ảnh bìa thiếu con số làm nhân vật chính: điền thumb_stat (vd '-$6T', '79%') hoặc thumb_vs / thumb_before + thumb_after.")
    if bool(plan.get("thumb_before")) != bool(plan.get("thumb_after")):
        bad.append("Ảnh bìa trước/sau phải điền đủ cả thumb_before và thumb_after.")
    for key, lim in (("thumb_tag", 24), ("thumb_kicker", 30)):
        if len(str(plan.get(key) or "")) > lim:
            bad.append(f"{key} '{plan[key]}' dài {len(str(plan[key]))} ký tự, tối đa {lim}.")
    for key, h in (plan.get("short_hooks") or {}).items():
        if not re.search(r"\d|\?", h):
            bad.append(f"Tiêu đề short phần {int(key) + 1} '{h}' không có con số hay câu hỏi, khó gây tò mò.")
        # Trọng 24/11 (short NVDA): tiêu đề 61 ký tự tràn 3 dòng, bị thẻ đè. Video đã duyệt (video 3, 4) đều ≤ 46 ký tự.
        if len(h) > 46:
            bad.append(f"Tiêu đề short phần {int(key) + 1} dài {len(h)} ký tự, tối đa 46 (2 dòng), video đã duyệt đều 25 đến 46.")
    bad += short_open_issues(plan)
    st = plan.get("short_title") or ""
    if st and len(st) > 46:
        bad.append(f"short_title dài {len(st)} ký tự, tối đa 46 (2 dòng).")
    return bad


if __name__ == "__main__":
    issues = lint(json.loads(open(sys.argv[1], encoding="utf-8").read()))
    print("\n".join(f"- {x}" for x in issues) if issues else "Khung ổn, không thấy lỗi.")
