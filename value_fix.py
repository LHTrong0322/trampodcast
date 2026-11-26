"""Trọng 27/11: phát hiện câu hoặc thẻ KHÔNG ĐÁNG xem thì viết lại NGAY, kể cả lời đọc.

Dùng ở 2 chỗ (news_flash.build):
  A. Trước khi đọc giọng: chấm "đáng xem" cả kịch bản viết tay/đã duyệt; dưới 8 thì viết lại câu không đáng (rẻ, chưa tốn giọng).
  B. Sau review (xem trước hoặc sau dựng): lỗi KHÔNG ĐÁNG nằm ở lời đọc thì viết lại câu, đọc giọng lại, dựng lại.

Ràng buộc an toàn: chỉ sửa câu bị chỉ ra; không dấu gạch ngang dài; thẻ hình phải bám đúng cụm trong lời đọc mới.
Số liệu MỚI (Trọng 27/11): được thêm để video có giá trị hơn, NHƯNG mỗi số mới phải kèm link nguồn, và một bot thứ hai
mở đúng link đó xác nhận số có thật. Số không có nguồn hoặc không qua kiểm chứng thì bị chặn. Sai ràng buộc thì giữ bản cũ.
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

THÊM SỐ LIỆU MỚI: được và NÊN, nếu nó làm câu có giá trị hơn (bối cảnh, so sánh lịch sử, hệ quả). Dùng WebSearch/WebFetch tìm
từ nguồn uy tín (Cointelegraph, CoinDesk, The Block, Decrypt, Bloomberg, Reuters, Glassnode, CryptoQuant, SoSoValue, trang chính thức),
ưu tiên tin trong 30 ngày gần đây, đúng chủ đề video. TUYỆT ĐỐI không bịa: số nào không tìm thấy trong bài thì không dùng.
Mỗi số mới ghi vào "new_facts" với link bài và đoạn trích nguyên văn ngắn (dưới 25 từ) có chứa con số đó.

Viết lại ĐÚNG các câu bị chỉ ra (câu khác giữ nguyên từng chữ) để mỗi câu mang 1 điều mới, có 1 con số hoặc 1 so sánh,
và thẻ hình VẼ chính con số đó (bignum, versus, chart, logo), không chép câu chữ. Câu không có gì để vẽ thì bỏ câu.
Giữ: câu mở có con số, câu kết hỏi bình luận, tổng 95 đến 150 từ, từ ngữ crypto giữ tiếng Anh, không dấu gạch ngang dài,
nói "retail", "insider", "unlock", "revenue". Mỗi "at" của thẻ phải là cụm có NGUYÊN VĂN trong lời đọc mới.
Trả DUY NHẤT JSON:
{{"narration": "toàn bộ lời đọc mới", "beats": [thẻ hình đầy đủ, cùng định dạng như trên],
  "changes": [{{"cu": "câu cũ", "moi": "câu mới hoặc (bỏ)", "ly_do": "vì sao"}}],
  "new_facts": [{{"value": "con số đúng như trong lời đọc hoặc thẻ (vd $53K, 15%)", "claim": "ý của số đó",
                 "url": "link bài nguồn", "source": "tên nguồn", "quote": "trích nguyên văn có con số"}}]}}"""

VERIFY = """Bạn là người kiểm chứng số liệu (fact-checker) độc lập, khó tính. Với TỪNG mục dưới đây, dùng WebFetch mở đúng link,
tìm xem bài có thật sự chứa con số đó và có ủng hộ đúng ý (claim) không. Đơn vị, mốc thời gian, chủ thể phải khớp.
Không mở được link, số không có trong bài, hoặc ý bị nói quá so với bài thì là KHÔNG ĐẠT.
{items}
Trả DUY NHẤT JSON: {{"results": [{{"i": số thứ tự, "ok": true hoặc false, "why": "ngắn gọn"}}]}}"""

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


def validate(old: dict, new: dict, verified: list[dict] | None = None) -> str:
    """Trả "" nếu bản mới dùng được, không thì lý do bỏ. verified: số mới đã qua kiểm chứng (có link)."""
    nar = str(new.get("narration") or "").strip()
    if not nar or not isinstance(new.get("beats"), list) or not new["beats"]:
        return "thiếu lời đọc hoặc thẻ"
    if "\u2014" in nar or "\u2013" in nar:
        return "có dấu gạch ngang dài"
    n = len(nar.split())
    if not 80 <= n <= 170:
        return f"độ dài {n} từ ngoài khoảng cho phép"
    allowed = _nums(json.dumps(old, ensure_ascii=False))
    for f in verified or []:
        if str(f.get("url", "")).startswith("http"):
            allowed |= _nums(f"{f.get('value', '')} {f.get('claim', '')}")
    extra = _nums(nar + " " + json.dumps(new["beats"], ensure_ascii=False)) - allowed
    if extra:
        return "có số mới chưa có nguồn đã kiểm chứng: " + ", ".join(sorted(extra)[:5])
    low = re.sub(r"[^\w\s]", "", nar.lower())
    for b in new["beats"]:
        at = re.sub(r"[^\w\s]", "", str(b.get("at", "")).lower()).strip()
        if not at or at not in low:
            return f"thẻ bám cụm không có trong lời đọc: {b.get('at')}"
    return ""


def verify(facts: list[dict], run=None) -> list[dict]:
    """Bot thứ hai mở từng link, chỉ giữ số liệu có thật trong bài. Lỗi thì coi như không đạt hết."""
    import script_review as SR
    facts = [f for f in facts or [] if isinstance(f, dict) and str(f.get("url", "")).startswith("http") and f.get("value")]
    if not facts:
        return []
    run = run or (lambda pr: SR.run_claude(pr, tools="WebFetch", turns=20, timeout=900))
    items = "\n".join(f"{i}. số {f['value']} | ý: {f.get('claim', '')} | link: {f['url']} | trích: {f.get('quote', '')}"
                      for i, f in enumerate(facts))
    try:
        res = run(VERIFY.format(items=items)).get("results") or []
    except Exception:
        return []
    ok = {int(r.get("i", -1)) for r in res if r.get("ok") is True}
    return [f for i, f in enumerate(facts) if i in ok]


def rewrite(plan: dict, problems: list[str], run=None, check=None) -> tuple[dict | None, list[dict], str]:
    """Viết lại câu/thẻ không đáng. Trả (plan mới hoặc None, danh sách đổi, lý do nếu bỏ).
    Số mới phải qua verify(); số nào trượt kiểm chứng thì cả bản viết lại bị bỏ, giữ bản cũ."""
    import script_review as SR
    run = run or (lambda pr: SR.run_claude(pr, tools="WebSearch,WebFetch", turns=30, timeout=1200))
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
    if not isinstance(j, dict):
        return None, [], "Claude không trả JSON"
    claimed = [f for f in j.get("new_facts") or [] if isinstance(f, dict)]
    good = verify(claimed, run=check) if claimed else []
    why = validate(plan, j, good)
    if why:
        if claimed and len(good) < len(claimed):
            why += f" ({len(claimed) - len(good)}/{len(claimed)} số mới trượt kiểm chứng)"
        return None, [], why
    new = json.loads(json.dumps(plan, ensure_ascii=False))
    ns = new["sections"][0]
    ns["narration"] = j["narration"].strip()
    ns["beats"] = [{k: v for k, v in b.items() if k != "s"} for b in j["beats"]]
    first = re.split(r"(?<=[.?!])\s+", ns["narration"])[0]
    if first and first != sec.get("narration", "").split(".")[0]:
        new["hook"] = first
    if good:   # lưu nguồn để mô tả video và lần chấm sau biết số này đã kiểm chứng
        new["sources"] = (plan.get("sources") or []) + [{k: f.get(k) for k in ("value", "claim", "source", "url")} for f in good]
    ch = list(j.get("changes") or [])
    for f in good:
        ch.append({"cu": "(số mới)", "moi": f"{f.get('value')}: {f.get('claim', '')}", "ly_do": f"đã kiểm chứng, nguồn {f.get('source', '')} {f.get('url', '')}"})
    return new, ch, ""


def changes_text(did: str, stage: str, changes: list[dict]) -> str:
    lines = [f"✂️ {did}: luật giá trị, bot viết lại {len(changes)} chỗ ({stage})"]
    for c in changes[:8]:
        lines.append(f"• Cũ: {c.get('cu', '')}\n  Mới: {c.get('moi', '')}\n  Vì: {c.get('ly_do', '')}")
    return "\n".join(lines)
