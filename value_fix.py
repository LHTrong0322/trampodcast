"""Trọng 27/11: phát hiện câu hoặc thẻ KHÔNG ĐÁNG xem thì viết lại NGAY, kể cả lời đọc.

Dùng ở 2 chỗ (news_flash.build):
  A. Trước khi đọc giọng: chấm "đáng xem" cả kịch bản viết tay/đã duyệt; dưới 8 thì viết lại câu không đáng (rẻ, chưa tốn giọng).
  B. Sau review (xem trước hoặc sau dựng): lỗi KHÔNG ĐÁNG nằm ở lời đọc thì viết lại câu, đọc giọng lại, dựng lại.

Ràng buộc an toàn: chỉ sửa câu bị chỉ ra; không dấu gạch ngang dài; thẻ hình phải bám đúng cụm trong lời đọc mới.
Trọng 28/11: BỎ bước kiểm chứng nguồn (bot thứ hai). Claude được tự do sáng tạo, thêm số liệu, ví dụ, góc kể mới,
không phải đi tra nguồn cho từng số, không bị chặn vì "chưa kiểm chứng". Sai ràng buộc kỹ thuật thì giữ bản cũ.
"""
from __future__ import annotations

import json
import re

import podcast as P

PROMPT = """Bạn là biên tập viên kịch bản video ngắn 9:16 tiếng Việt kênh Smart Penguin Insights (crypto).
{rule}

Bot review vừa chỉ ra các chỗ KHÔNG ĐÁNG hoặc cần sửa:
{problems}

LỜI ĐỌC HIỆN TẠI:
"{narration}"

THẺ HÌNH HIỆN TẠI (at = cụm từ trong lời đọc nơi thẻ xuất hiện):
{beats}

SỐ LIỆU ĐÃ CÓ (dùng thoải mái):
{facts}

TỰ DO SÁNG TẠO (Trọng 28/11): không rập khuôn sách giáo khoa. Được và NÊN thêm số liệu, ví dụ thật, so sánh lịch sử,
câu chuyện, góc nhìn bất ngờ nếu nó làm câu hay hơn. Không cần đi tra nguồn cho từng số, không xoá số chỉ vì "chưa thấy nguồn".
Chỉ đừng nói điều bạn biết là sai. Có link nguồn sẵn trong đầu thì ghi vào "new_facts" để đưa vào mô tả video, không có thì thôi.

Viết lại ĐÚNG các câu bị chỉ ra (câu khác giữ nguyên từng chữ) để mỗi câu mang 1 điều mới, có 1 con số hoặc 1 so sánh,
và thẻ hình VẼ chính con số đó (bignum, versus, chart, logo), không chép câu chữ. Câu không có gì để vẽ thì bỏ câu.
Giữ: câu mở có con số, câu kết hỏi bình luận, tổng 95 đến 150 từ, từ ngữ crypto giữ tiếng Anh, không dấu gạch ngang dài,
nói "retail", "insider", "unlock", "revenue". Mỗi "at" của thẻ phải là cụm có NGUYÊN VĂN trong lời đọc mới.
Trả DUY NHẤT JSON:
{{"narration": "toàn bộ lời đọc mới", "beats": [thẻ hình đầy đủ, cùng định dạng như trên],
  "changes": [{{"cu": "câu cũ", "moi": "câu mới hoặc (bỏ)", "ly_do": "vì sao"}}],
  "new_facts": [{{"value": "con số đúng như trong lời đọc hoặc thẻ (vd $53K, 15%)", "claim": "ý của số đó",
                 "url": "link bài nguồn", "source": "tên nguồn", "quote": "trích nguyên văn có con số"}}]}}"""



def problems_from(rv: dict | None, pre: dict | None = None) -> list[str]:
    """Các lỗi KHÔNG ĐÁNG từ review sau dựng (can_sua) và review xem trước (issues)."""
    out = [x for x in (rv or {}).get("can_sua", []) if "KHÔNG ĐÁNG" in str(x).upper()]
    for it in (pre or {}).get("issues", []) or []:
        t = it.get("problem", "") if isinstance(it, dict) else str(it)
        if "KHÔNG ĐÁNG" in t.upper():
            out.append(t)
    return out


def validate(old: dict, new: dict) -> str:
    """Trả "" nếu bản mới dùng được, không thì lý do bỏ (chỉ ràng buộc kỹ thuật; Trọng 28/11 bỏ kiểm chứng nguồn)."""
    nar = str(new.get("narration") or "").strip()
    if not nar or not isinstance(new.get("beats"), list) or not new["beats"]:
        return "thiếu lời đọc hoặc thẻ"
    if "\u2014" in nar or "\u2013" in nar:
        return "có dấu gạch ngang dài"
    n = len(nar.split())
    if not 80 <= n <= 185:
        return f"độ dài {n} từ ngoài khoảng cho phép"
    # Trọng 27/11: bot viết lại từng để thẻ "versus" có left/right là chữ thay vì khung {label, value...}, làm dựng lỗi.
    for b in new["beats"]:
        if not isinstance(b, dict):
            return "thẻ sai khung"
        for f in ("left", "right"):
            if b.get(f) is not None and not isinstance(b[f], dict):
                return f"thẻ {b.get('type')} sai khung ở {f}"
        for f in ("items", "cols"):
            if b.get(f) is not None and not (isinstance(b[f], list) and all(isinstance(x, dict) for x in b[f])):
                return f"thẻ {b.get('type')} sai khung ở {f}"
    low = re.sub(r"[^\w\s]", "", nar.lower())
    for b in new["beats"]:
        at = re.sub(r"[^\w\s]", "", str(b.get("at", "")).lower()).strip()
        if not at or at not in low:
            return f"thẻ bám cụm không có trong lời đọc: {b.get('at')}"
    return ""


def rewrite(plan: dict, problems: list[str], run=None) -> tuple[dict | None, list[dict], str]:
    """Viết lại câu/thẻ không đáng. Trả (plan mới hoặc None, danh sách đổi, lý do nếu bỏ).
    Trọng 28/11: không còn bước kiểm chứng nguồn, chỉ chặn lỗi kỹ thuật (độ dài, khung thẻ, cụm "at")."""
    import script_review as SR
    run = run or (lambda pr: SR.run_claude(pr, tools="WebSearch,WebFetch", turns=30, timeout=1200))
    sec = plan["sections"][0]
    src = [f"{f.get('value', '')}: {f.get('claim', '')} ({f.get('source', '')}, {f.get('url', '')})" for f in plan.get("sources") or []]
    facts = "\n".join(x for x in [plan.get("description", ""), "; ".join(sec.get("bullets", []) or []), *src] if x)
    pr = PROMPT.format(rule=SR.VALUE_RULE, problems="\n".join(f"- {x}" for x in problems[:12]),
                       narration=sec.get("narration", ""), beats=json.dumps(sec.get("beats", []), ensure_ascii=False, indent=1),
                       facts=facts or "(chỉ dùng số đã có trong lời đọc và thẻ hình)")
    why = ""
    for attempt in range(2):   # 27/11: bị chặn thì cho viết lại 1 lần nữa, nói rõ lỗi (từng bị chặn oan vì số tự tính, dài hơn 3 từ)
        try:
            j = run(pr if not why else pr + "\n\nBẢN TRƯỚC BỊ CHẶN VÌ: " + why +
                    ". Sửa đúng lỗi đó, giữ trong 80 đến 180 từ.")
        except Exception as ex:
            return None, [], f"Claude lỗi: {str(ex)[:150]}"
        j = P.nodash(j) if isinstance(j, dict) else j
        if not isinstance(j, dict):
            why = "Claude không trả JSON"
            continue
        why = validate(plan, j)
        if not why:
            break
    if why:
        return None, [], why
    new = json.loads(json.dumps(plan, ensure_ascii=False))
    ns = new["sections"][0]
    ns["narration"] = j["narration"].strip()
    ns["beats"] = [{k: v for k, v in b.items() if k != "s"} for b in j["beats"]]
    first = re.split(r"(?<=[.?!])\s+", ns["narration"])[0]
    if first and first != sec.get("narration", "").split(".")[0]:
        new["hook"] = first
    good = [f for f in j.get("new_facts") or [] if isinstance(f, dict) and f.get("value") and f.get("url")]
    if good:   # có link thì lưu để đưa vào mô tả video
        new["sources"] = (plan.get("sources") or []) + [{k: f.get(k) for k in ("value", "claim", "source", "url")} for f in good]
    ch = list(j.get("changes") or [])
    return new, ch, ""


def changes_text(did: str, stage: str, changes: list[dict]) -> str:
    lines = [f"✂️ {did}: luật giá trị, bot viết lại {len(changes)} chỗ ({stage})"]
    for c in changes[:8]:
        lines.append(f"• Cũ: {c.get('cu', '')}\n  Mới: {c.get('moi', '')}\n  Vì: {c.get('ly_do', '')}")
    return "\n".join(lines)
