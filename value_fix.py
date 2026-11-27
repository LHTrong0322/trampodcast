"""Trọng 27/11: phát hiện câu hoặc thẻ KHÔNG ĐÁNG xem thì viết lại NGAY, kể cả lời đọc.

Dùng ở 2 chỗ (news_flash.build):
  A. Trước khi đọc giọng: chấm "đáng xem" cả kịch bản viết tay/đã duyệt; dưới 8 thì viết lại câu không đáng (rẻ, chưa tốn giọng).
  B. Sau review (xem trước hoặc sau dựng): lỗi KHÔNG ĐÁNG nằm ở lời đọc thì viết lại câu, đọc giọng lại, dựng lại.

Ràng buộc an toàn: chỉ sửa câu bị chỉ ra; không dấu gạch ngang dài; thẻ hình phải bám đúng cụm trong lời đọc mới.
Số liệu MỚI (Trọng 27/11, 14:10): được thêm để video có giá trị hơn, kèm link nguồn nếu có; một bot thứ hai kiểm chứng.
CHỈ chặn số đã kiểm chứng ra SAI (hoặc nói quá). Số chưa kiểm chứng được (không tìm thấy nguồn, link không mở được)
vẫn dùng bình thường, chỉ ghi chú "chưa kiểm chứng" trong danh sách thay đổi. Sai ràng buộc khác thì giữ bản cũ.
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

SỐ CHƯA THẤY NGUỒN (Trọng 27/11): ĐÚNG SỰ THẬT quan trọng hơn ĐÚNG NGUỒN. KHÔNG được xoá số chỉ vì chưa thấy trong danh sách trên, không được xoá vì "nguồn gốc không nhắc". Dữ liệu lịch sử phổ biến (đáy, đỉnh các chu kỳ trước, ATH, sự kiện lớn như FTX, Luna, halving) là kiến thức chung của ngành: giữ, không đòi nguồn trong bài, chỉ bỏ khi biết chắc là sai. Dùng WebSearch/WebFetch tra:
tìm được bài chứng minh thì GIỮ số đó và ghi vào "new_facts" (kèm link, trích dẫn) để kiểm chứng. Tra không ra nguồn thì VẪN GIỮ
(Trọng 27/11: chưa kiểm chứng được không phải là sai). CHỈ bỏ khi tra ra số sai hoặc nói quá, và ghi rõ lý do trong "changes".

THÊM SỐ LIỆU MỚI: được và NÊN, nếu nó làm câu có giá trị hơn (bối cảnh, so sánh lịch sử, hệ quả). Dùng WebSearch/WebFetch tìm
từ nguồn uy tín (Cointelegraph, CoinDesk, The Block, Decrypt, Bloomberg, Reuters, Glassnode, CryptoQuant, SoSoValue, trang chính thức),
ưu tiên tin trong 30 ngày gần đây, đúng chủ đề video. TUYỆT ĐỐI không bịa (không tự nghĩ ra số). Ý hoặc số bạn tin là đúng
nhưng chưa tìm được bài nguồn thì VẪN được dùng (Trọng 27/11), ghi vào "new_facts" với url để trống. Chỉ không dùng khi biết là sai.
Mỗi số mới ghi vào "new_facts" với link bài (nếu có) và đoạn trích nguyên văn ngắn (dưới 25 từ) có chứa con số đó.

Viết lại ĐÚNG các câu bị chỉ ra (câu khác giữ nguyên từng chữ) để mỗi câu mang 1 điều mới, có 1 con số hoặc 1 so sánh,
và thẻ hình VẼ chính con số đó (bignum, versus, chart, logo), không chép câu chữ. Câu không có gì để vẽ thì bỏ câu.
Giữ: câu mở có con số, câu kết hỏi bình luận, tổng 95 đến 150 từ, từ ngữ crypto giữ tiếng Anh, không dấu gạch ngang dài,
nói "retail", "insider", "unlock", "revenue". Mỗi "at" của thẻ phải là cụm có NGUYÊN VĂN trong lời đọc mới.
Trả DUY NHẤT JSON:
{{"narration": "toàn bộ lời đọc mới", "beats": [thẻ hình đầy đủ, cùng định dạng như trên],
  "changes": [{{"cu": "câu cũ", "moi": "câu mới hoặc (bỏ)", "ly_do": "vì sao"}}],
  "new_facts": [{{"value": "con số đúng như trong lời đọc hoặc thẻ (vd $53K, 15%)", "claim": "ý của số đó",
                 "url": "link bài nguồn", "source": "tên nguồn", "quote": "trích nguyên văn có con số"}}]}}"""

VERIFY = """Bạn là người kiểm chứng số liệu (fact-checker) độc lập. Mục tiêu: con số có ĐÚNG SỰ THẬT không. Với TỪNG mục, dùng WebFetch mở link,
tìm xem bài có thật sự chứa con số đó và có ủng hộ đúng ý (claim) không. Đơn vị, mốc thời gian, chủ thể phải khớp.
Link không mở được hoặc không có số đó thì tự tra thêm bằng WebSearch: tìm được nguồn uy tín khác chứng minh thì "dung".
"sai" CHỈ khi tìm được bằng chứng số đó sai hoặc bị nói quá. Không tìm được nguồn nào (chứng minh hay bác bỏ) thì "chua_ro":
số đó vẫn được dùng (Trọng 27/11), nên đừng ghi "sai" chỉ vì không tra ra.
{items}
Trả DUY NHẤT JSON: {{"results": [{{"i": số thứ tự, "verdict": "dung" hoặc "sai" hoặc "chua_ro", "why": "ngắn gọn"}}]}}"""

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


def validate(old: dict, new: dict, wrong: list[dict] | None = None) -> str:
    """Trả "" nếu bản mới dùng được, không thì lý do bỏ. wrong: số mới đã kiểm chứng ra SAI.
    Trọng 27/11 (14:10): số chưa kiểm chứng được vẫn dùng bình thường, chỉ chặn số kiểm chứng ra sai."""
    nar = str(new.get("narration") or "").strip()
    if not nar or not isinstance(new.get("beats"), list) or not new["beats"]:
        return "thiếu lời đọc hoặc thẻ"
    if "\u2014" in nar or "\u2013" in nar:
        return "có dấu gạch ngang dài"
    n = len(nar.split())
    if not 80 <= n <= 185:
        return f"độ dài {n} từ ngoài khoảng cho phép"
    used = _nums(nar + " " + json.dumps(new["beats"], ensure_ascii=False)) - _nums(json.dumps(old, ensure_ascii=False))
    bad = set()
    for f in wrong or []:
        bad |= _nums(str(f.get("value", "")))
    if used & bad:
        return "có số mới đã kiểm chứng ra sai: " + ", ".join(sorted(used & bad)[:5])
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


def verify(facts: list[dict], run=None) -> tuple[list[dict], list[dict]]:
    """Bot thứ hai kiểm chứng từng số. Trả (đã chứng minh đúng, đã chứng minh SAI).
    Số còn lại là chưa kiểm chứng được: vẫn dùng (Trọng 27/11). Bot kiểm chứng lỗi thì không coi số nào là sai."""
    import script_review as SR
    facts = [f for f in facts or [] if isinstance(f, dict) and f.get("value")]
    if not facts:
        return [], []
    run = run or (lambda pr: SR.run_claude(pr, tools="WebSearch,WebFetch", turns=25, timeout=900))
    items = "\n".join(f"{i}. số {f['value']} | ý: {f.get('claim', '')} | link: {f.get('url') or '(chưa có, tự tra)'} | trích: {f.get('quote', '')}"
                      for i, f in enumerate(facts))
    try:
        res = run(VERIFY.format(items=items)).get("results") or []
    except Exception:
        return [], []

    def verdict(r: dict) -> str:
        v = str(r.get("verdict", "")).lower()
        if v in ("dung", "sai", "chua_ro"):
            return v
        return "dung" if r.get("ok") is True else "chua_ro"   # kiểu trả cũ: false không có nghĩa là sai
    vs = {int(r.get("i", -1)): verdict(r) for r in res if isinstance(r, dict)}
    return ([f for i, f in enumerate(facts) if vs.get(i) == "dung"],
            [f for i, f in enumerate(facts) if vs.get(i) == "sai"])


def rewrite(plan: dict, problems: list[str], run=None, check=None) -> tuple[dict | None, list[dict], str]:
    """Viết lại câu/thẻ không đáng. Trả (plan mới hoặc None, danh sách đổi, lý do nếu bỏ).
    Số mới qua verify(): số kiểm chứng ra SAI thì cả bản viết lại bị bỏ, giữ bản cũ; số chưa kiểm chứng được vẫn dùng."""
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
                    ". Sửa đúng lỗi đó: số nào đã kiểm chứng ra SAI thì bỏ hoặc thay bằng số đúng; số chưa kiểm chứng được thì cứ giữ"
                    " (số tự tính thì ghi rõ phép tính trong claim); giữ trong 80 đến 180 từ.")
        except Exception as ex:
            return None, [], f"Claude lỗi: {str(ex)[:150]}"
        j = P.nodash(j) if isinstance(j, dict) else j
        if not isinstance(j, dict):
            why = "Claude không trả JSON"
            continue
        claimed = [f for f in j.get("new_facts") or [] if isinstance(f, dict)]
        good, wrong = verify(claimed, run=check) if claimed else ([], [])
        why = validate(plan, j, wrong)
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
    if good:   # lưu nguồn để mô tả video và lần chấm sau biết số này đã kiểm chứng
        new["sources"] = (plan.get("sources") or []) + [{k: f.get(k) for k in ("value", "claim", "source", "url")} for f in good]
    ch = list(j.get("changes") or [])
    for f in good:
        ch.append({"cu": "(số mới)", "moi": f"{f.get('value')}: {f.get('claim', '')}", "ly_do": f"đã kiểm chứng, nguồn {f.get('source', '')} {f.get('url', '')}"})
    for f in claimed:
        if f not in good and f not in wrong:
            ch.append({"cu": "(số mới)", "moi": f"{f.get('value')}: {f.get('claim', '')}",
                       "ly_do": "chưa kiểm chứng được nguồn, vẫn dùng (chỉ bỏ khi kiểm chứng ra sai)"})
    return new, ch, ""


def changes_text(did: str, stage: str, changes: list[dict]) -> str:
    lines = [f"✂️ {did}: luật giá trị, bot viết lại {len(changes)} chỗ ({stage})"]
    for c in changes[:8]:
        lines.append(f"• Cũ: {c.get('cu', '')}\n  Mới: {c.get('moi', '')}\n  Vì: {c.get('ly_do', '')}")
    return "\n".join(lines)
