"""Quy trình 2 lượt (Trọng 22/11):
  lượt 1 (nháp) dựng bằng giọng miễn phí VieNeu "Hải Đăng" → bot review chấm,
  rồi bot sửa phần HÌNH theo góp ý (file này) → lượt 2 dựng lại bằng giọng chính (Gemini Ludo).
Lúc gửi Telegram có cả 2 video để Trọng thấy khác biệt.

Bot chỉ sửa phần hình (beats, ảnh bìa, tiêu đề short, tóm tắt), KHÔNG đổi lời đọc: lời đọc đã chấm/duyệt ở vòng 1.
Bản sửa phải qua video_lint không tệ hơn bản cũ, không thì giữ bản cũ.
"""
from __future__ import annotations

import copy
import json
import re

from podcast import log

VISUAL_KEYS = ("hook_beats", "hook_screen", "thumb_text", "thumb_tag", "thumb_vs", "short_hooks", "outro_points", "outro_cta")
SEC_KEYS = ("beats", "bullets", "emphasis", "edu")
RUNTIME = ("posts", "voices", "voice", "lint", "images", "image_credits", "data", "script_score")

PROMPT = """Bạn là đạo diễn hình ảnh của kênh Smart Penguin Insights. Video NHÁP vừa dựng xong và bị bot review chấm:
{scores}

TOÀN BỘ góp ý của bot (Trọng yêu cầu xử lý NGHIÊM TÚC TỪNG MỤC, không bỏ qua, không làm sơ sài):
{fixes}

Kịch bản (JSON) của video.
{narration_rule}

{plan}

Luật bắt buộc (Trọng đã nhắc, không tái phạm):
- Mỗi beat có "at" là 3-5 chữ CHÉP NGUYÊN từ lời đọc của chính phần đó (sai chữ là hình hiện sai lúc).
- Kiểu beat: bignum, versus, dots, flow, logos, race, chart, wma, matrix, statement. KHÔNG dùng "question".
- Beat "wma" (biểu đồ BTC tuần + đường 200WMA/350WMA, Trọng yêu cầu 23/11) phải GIỮ NGUYÊN nếu kịch bản đang có.
- Tối đa 8 giây lời đọc (khoảng 26 chữ) phải có hình mới; không 2 beat liền nhau cùng kiểu; thẻ chữ (statement) không quá 40% số beat.
- Số liệu trên hình phải đúng với lời đọc; số giá từ đầu năm dùng ô điền {{YTD:TICKER}} / {{YTDS:TICKER}} như kịch bản đang có.
- Hình "chart" và "race" dùng được cho coin crypto lẫn cổ phiếu/chỉ số (NVDA, SPY, S&P, VIX...): ghi đúng ticker, "days" theo giai đoạn lời đọc nói.
- Nhắc dự án nào thì gắn logo dự án đó ("logo": "TICKER"). Nền luôn trắng sạch, không thêm màu nền.
- Lời đọc nói "N thứ/điều/bước" thì flow có đúng N steps; outro_points đúng số câu hook hứa.
- Kết quả so sánh quan trọng có thể thêm "music": 2.5 (giọng nghỉ, nhạc nền dâng) hoặc "hold": giây (giữ hình lâu hơn).

Trả về JSON chỉ gồm các khoá đã sửa, dạng:
{{"hook_beats": [...], "sections": [{{"beats": [...], "bullets": [...]}}, ... đủ số phần, phần nào không sửa thì để {{}}], "thumb_text": "...", ...,
  "xu_ly": [{{"muc": 1, "lam": "Đã sửa: ... (nói rõ sửa gì, ở phần nào)" hoặc "Cần Trọng quyết: ... (vì đụng lời đọc đã duyệt / lý do cụ thể)"}}, ... ĐỦ MỌI MỤC từ 1 tới {n}]}}"""

LOCKED = """Lời đọc (hook, intro, narration, outro) là bản Trọng ĐÃ DUYỆT, KHÔNG được đổi một chữ.
Chỉ được sửa phần HÌNH: hook_beats, sections[].beats, sections[].bullets, sections[].emphasis, sections[].edu,
thumb_text, thumb_tag, thumb_vs, short_hooks, outro_points, outro_cta. Góp ý nào chỉ sửa được bằng lời đọc thì ghi "Cần Trọng quyết"."""

FREE = """Kịch bản do máy viết (chưa qua Trọng duyệt): được sửa CẢ lời đọc (hook, intro, sections[].narration, outro) để làm theo
mẹo kịch bản và góp ý giữ chân, nhưng giữ đúng ý, đúng số liệu, đúng luật từ ngữ (retail, insider, unlock, revenue; thuật ngữ tiếng Anh;
không gạch ngang dài; câu chào "Chào mừng mọi người đã quay trở lại với Smart Penguin Insights" giữ nguyên). Phần hình sửa như dưới."""


def scores_text(rv: dict) -> str:
    sc = rv.get("scores") or {}
    return f"Tổng {rv.get('score')}/10. " + ", ".join(f"{k} {v}" for k, v in sc.items())


def as_list(x) -> list:
    if isinstance(x, list):
        return [str(v) for v in x if str(v).strip()]
    return [str(x)] if x and str(x).strip() else []


def base_plan(plan: dict) -> dict:
    p = copy.deepcopy(plan)
    for k in RUNTIME:
        p.pop(k, None)
    return p


def improve(plan: dict, rv: dict, locked: bool = True) -> tuple[dict, list[str]]:
    """Trả (kịch bản đã sửa hình, danh sách thay đổi). Lỗi gì cũng trả lại kịch bản cũ."""
    import script_review as SR
    import video_lint as VL
    plan = base_plan(plan)
    fixes = ([f"[Nên sửa] {x}" for x in as_list(rv.get("can_sua"))] + [f"[Dễ mất người xem] {x}" for x in as_list(rv.get("retention_risk"))]
             + [f"[Mẹo kịch bản] {x}" for x in as_list(rv.get("script_tips"))])
    # Trọng 23/11: lỗi trình bày máy tự soát (nhãn dài, nguồn viết liền...) cũng phải sửa trước khi dựng bản chính
    beats = list(plan.get("hook_beats") or []) + [b for s in plan.get("sections") or [] for b in s.get("beats") or []]
    fixes += [f"[Lỗi trình bày] {x}" for x in VL.layout_issues(beats)]
    if not fixes:
        return plan, []
    listing = "\n".join(f"{i + 1}. {x}" for i, x in enumerate(fixes))
    ask = PROMPT.format(scores=scores_text(rv), fixes=listing[:8000], n=len(fixes),
                        narration_rule=LOCKED if locked else FREE,
                        plan=json.dumps(plan, ensure_ascii=False, indent=1)[:60000])
    patch = {}
    for attempt in range(3):   # bắt trả lời ĐỦ từng mục, thiếu thì hỏi lại
        try:
            patch = SR.run_claude(ask)
        except Exception as ex:
            log(f"   ! bot sửa lỗi (lần {attempt + 1}): {str(ex)[:200]}")
            continue
        done = {int(x.get("muc", 0)) for x in patch.get("xu_ly") or [] if isinstance(x, dict) and str(x.get("muc", "")).isdigit()}
        miss = [i + 1 for i in range(len(fixes)) if i + 1 not in done]
        if not miss:
            break
        ask += f"\n\nLần trước BỎ SÓT mục {miss}. Trả lại JSON đầy đủ, xử lý ĐỦ mọi mục."
    if not patch:
        log("   ! bot không sửa được, giữ bản nháp")
        return plan, [f"Chưa xử lý được: {x}" for x in fixes]
    new = copy.deepcopy(plan)
    for k in VISUAL_KEYS:
        if k in patch and patch[k] not in (None, "", []):
            new[k] = patch[k]
    for i, sp in enumerate((patch.get("sections") or [])[: len(new.get("sections") or [])]):
        if isinstance(sp, dict):
            for k in SEC_KEYS:
                if k in sp and sp[k] not in (None, ""):
                    new["sections"][i][k] = sp[k]
    if locked:   # lời đọc đã duyệt không được đổi
        for k in ("hook", "intro", "outro"):
            new[k] = plan.get(k)
        for a, b in zip(new.get("sections") or [], plan.get("sections") or []):
            a["narration"] = b.get("narration")
    else:
        for k in ("hook", "intro", "outro"):
            if isinstance(patch.get(k), str) and patch[k].strip():
                new[k] = patch[k]
        for i, sp in enumerate((patch.get("sections") or [])[: len(new.get("sections") or [])]):
            if isinstance(sp, dict) and isinstance(sp.get("narration"), str) and sp["narration"].strip():
                new["sections"][i]["narration"] = sp["narration"]
    for s in new.get("sections") or []:
        s["beats"] = [b for b in (s.get("beats") or []) if isinstance(b, dict) and b.get("type") != "question"]
    for a, b in zip(new.get("sections") or [], plan.get("sections") or []):   # Trọng 23/11: biểu đồ 200WMA không được rơi mất
        lost = [x for x in b.get("beats") or [] if x.get("type") == "wma"]
        if lost and not any(x.get("type") == "wma" for x in a.get("beats") or []):
            low = (a.get("narration") or "").lower()
            a["beats"] = sorted((a.get("beats") or []) + lost, key=lambda x: (low.find(str(x.get("at", "")).lower()) % 10**6))
    old_n, new_n = len(VL.lint(plan)), len(VL.lint(new))
    bad_at = [x for x in VL.lint(new) if "lời đọc không có cụm này" in x]
    if new_n > old_n or bad_at:
        log(f"   ! bản sửa tệ hơn ({old_n} → {new_n} lỗi khung, {len(bad_at)} hình gắn sai chữ): bỏ phần sửa hình lỗi")
        # giữ lời đọc đã sửa (nếu được phép) nhưng lấy lại hình cũ cho phần bị gắn sai chữ
        for a, b in zip(new.get("sections") or [], plan.get("sections") or []):
            if any(str(x.get("at", "")).lower() not in (a.get("narration") or "").lower() for x in a.get("beats") or []):
                a["beats"] = b.get("beats") if a.get("narration") == b.get("narration") else a.get("beats")
        if len(VL.lint(new)) > old_n:
            return plan, [f"{i + 1}. {f[:140]}\n   → Bản sửa làm khung tệ hơn nên giữ bản nháp, cần xem lại tay" for i, f in enumerate(fixes)]
    xl = {int(x["muc"]): str(x.get("lam", "")) for x in patch.get("xu_ly") or [] if isinstance(x, dict) and str(x.get("muc", "")).isdigit()}
    changes = [f"{i + 1}. {f[:140]}\n   → {xl.get(i + 1, 'CHƯA XỬ LÝ')}" for i, f in enumerate(fixes)]
    log(f"   Bot xử lý {len(xl)}/{len(fixes)} góp ý, lỗi khung {old_n} → {new_n}" + "".join(f"\n     {c}" for c in changes))
    return new, changes
