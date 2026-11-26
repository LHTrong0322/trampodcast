"""Trọng 27/11: phát hiện câu hoặc thẻ KHÔNG ĐÁNG xem thì viết lại NGAY, kể cả lời đọc.

Dùng ở 2 chỗ (news_flash.build):
  A. Trước khi đọc giọng: chấm "đáng xem" cả kịch bản viết tay/đã duyệt; dưới 8 thì viết lại câu không đáng (rẻ, chưa tốn giọng).
  B. Sau review (xem trước hoặc sau dựng): lỗi KHÔNG ĐÁNG nằm ở lời đọc thì viết lại câu, đọc giọng lại, dựng lại.

Ràng buộc an toàn: chỉ sửa câu bị chỉ ra, không bịa số (mọi con số mới phải có sẵn trong kịch bản cũ),
không dấu gạch ngang dài, thẻ hình phải bám đúng cụm trong lời đọc mới. Sai ràng buộc thì giữ nguyên bản cũ.
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

NGUỒN SỐ LIỆU ĐƯỢC PHÉP DÙNG (chỉ dùng con số có ở đây, không bịa số mới):
{facts}

Viết lại ĐÚNG các câu bị chỉ ra (câu khác giữ nguyên từng chữ) để mỗi câu mang 1 điều mới, có 1 con số hoặc 1 so sánh,
và thẻ hình VẼ chính con số đó (bignum, versus, chart, logo), không chép câu chữ. Câu không có gì để vẽ thì bỏ câu.
Giữ: câu mở có con số, câu kết hỏi bình luận, tổng 95 đến 150 từ, từ ngữ crypto giữ tiếng Anh, không dấu gạch ngang dài,
nói "retail", "insider", "unlock", "revenue". Mỗi "at" của thẻ phải là cụm có NGUYÊN VĂN trong lời đọc mới.
Trả DUY NHẤT JSON:
{{"narration": "toàn bộ lời đọc mới", "beats": [thẻ hình đầy đủ, cùng định dạng như trên],
  "changes": [{{"cu": "câu cũ", "moi": "câu mới hoặc (bỏ)", "ly_do": "vì sao"}}]}}"""

_NUM = re.compile(r"\d+(?:[.,]\d+)?")


def _nums(text: str) -> set[str]:
    return {m.replace(",", ".") for m in _NUM.findall(text or "")}


def problems_from(rv: dict | None, pre: dict | None = None) -> list[str]:
    """Các lỗi KHÔNG ĐÁNG từ review sau dựng (can_sua) và review xem trước (issues)."""
    out = [x for x in (rv or {}).get("can_sua", []) if "KHÔNG ĐÁNG" in str(x).upper()]
    for it in (pre or {}).get("issues", []) or []:
        t = it.get("problem", "") if isinstance(it, dict) else str(it)
        if "KHÔNG ĐÁNG" in t.upper():
            out.append(t)
    return out


def validate(old: dict, new: dict) -> str:
    """Trả "" nếu bản mới dùng được, không thì lý do bỏ."""
    nar = str(new.get("narration") or "").strip()
    if not nar or not isinstance(new.get("beats"), list) or not new["beats"]:
        return "thiếu lời đọc hoặc thẻ"
    if "—" in nar or "–" in nar:
        return "có dấu gạch ngang dài"
    n = len(nar.split())
    if not 80 <= n <= 170:
        return f"độ dài {n} từ ngoài khoảng cho phép"
    allowed = _nums(json.dumps(old, ensure_ascii=False))
    extra = _nums(nar + " " + json.dumps(new["beats"], ensure_ascii=False)) - allowed
    if extra:
        return "có số mới không có trong kịch bản cũ: " + ", ".join(sorted(extra)[:5])
    low = re.sub(r"[^\w\s]", "", nar.lower())
    for b in new["beats"]:
        at = re.sub(r"[^\w\s]", "", str(b.get("at", "")).lower()).strip()
        if not at or at not in low:
            return f"thẻ bám cụm không có trong lời đọc: {b.get('at')}"
    return ""


def rewrite(plan: dict, problems: list[str], run=None) -> tuple[dict | None, list[dict], str]:
    """Viết lại câu/thẻ không đáng. Trả (plan mới hoặc None, danh sách đổi, lý do nếu bỏ)."""
    import script_review as SR
    run = run or SR.run_claude
    sec = plan["sections"][0]
    facts = "\n".join(x for x in [plan.get("description", ""), "; ".join(sec.get("bullets", []) or [])] if x)
    pr = PROMPT.format(rule=SR.VALUE_RULE, problems="\n".join(f"- {x}" for x in problems[:12]),
                       narration=sec.get("narration", ""), beats=json.dumps(sec.get("beats", []), ensure_ascii=False, indent=1),
                       facts=facts or "(chỉ dùng số đã có trong lời đọc và thẻ hình)")
    try:
        j = run(pr)
    except Exception as ex:
        return None, [], f"Claude lỗi: {str(ex)[:150]}"
    j = P.nodash(j) if isinstance(j, dict) else j
    why = validate(plan, j if isinstance(j, dict) else {})
    if why:
        return None, [], why
    new = json.loads(json.dumps(plan, ensure_ascii=False))
    ns = new["sections"][0]
    ns["narration"] = j["narration"].strip()
    ns["beats"] = [{k: v for k, v in b.items() if k != "s"} for b in j["beats"]]
    first = re.split(r"(?<=[.?!])\s+", ns["narration"])[0]
    if first and first != sec.get("narration", "").split(".")[0]:
        new["hook"] = first
    return new, j.get("changes") or [], ""


def changes_text(did: str, stage: str, changes: list[dict]) -> str:
    lines = [f"✂️ {did}: luật giá trị, bot viết lại {len(changes)} chỗ ({stage})"]
    for c in changes[:8]:
        lines.append(f"• Cũ: {c.get('cu', '')}\n  Mới: {c.get('moi', '')}\n  Vì: {c.get('ly_do', '')}")
    return "\n".join(lines)
