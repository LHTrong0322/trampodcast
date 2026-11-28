"""Bot review XEM TRƯỚC, chạy TRƯỚC khi dựng (Trọng 24/11).

"Thêm 1 bước review lại ảnh trước khi dựng, bảo đảm không có lỗi font hay hiển thị xấu" và
"đẩy review lên sớm lúc xong ảnh + kịch bản, bot tưởng tượng ra video trước khi dựng và fix từ bước này".

Cách làm: chụp sẵn các khung của short (bìa, tiêu đề, mỗi thẻ hình lúc đã hiện xong, thêm khung đều mỗi ~3 giây, khung kết),
kèm lời đọc đúng giây đó, rồi Claude chấm bằng ĐÚNG các tiêu chí của bot review sau dựng (insight_publish.REVIEW_PROMPT):
trình bày (font, tràn, đè, mồ côi, lệch hàng), chữ trên hình khớp lời đọc, thẻ không khẳng định mạnh hơn lời đọc/nguồn,
so sánh phải là 2 con số, hình không đứng yên quá ~5 giây, biểu đồ vẽ xong đúng lúc lời đọc nhắc tới, 2 giây đầu đủ cuốn.
Claude trả lệnh sửa, bot áp vào props rồi chụp lại và chấm lại, tối đa 2 vòng sửa, xong mới dựng thật.
Lệnh sửa được phép: đổi chữ trên thẻ, đổi tiêu đề short (≤ 46 ký tự), dời mốc giờ thẻ, bỏ thẻ, đổi thẻ thành thẻ chữ,
thêm thẻ chữ / thẻ số / thẻ ảnh kho. Con số mới chỉ được dùng khi chính lời đọc có số đó. Lời đọc (giọng) không đổi.
Không có token Claude hoặc PREFLIGHT=0 thì bỏ qua. Bước này lỗi thì vẫn dựng tiếp như cũ.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import podcast as P

TEXT_KEYS = ("label", "text", "sub", "note")
# Trọng 28/11: bot thêm ảnh kho theo từ khoá ra ảnh lạc đề (bao đàn guitar, băng cassette, cờ quân đội) và bị review chấm KHÔNG ĐÁNG.
# Bỏ hẳn quyền thêm ảnh kho ở bước xem trước và bước sửa; hình phải là số liệu, so sánh, biểu đồ, sơ đồ.
ADD_TYPES = ("statement", "bignum", "question")

PROMPT = """Bạn là biên tập viên TikTok/YouTube Shorts kỳ cựu mảng crypto kiêm CHUYÊN GIA DỰNG VIDEO, đang XEM TRƯỚC một video ngắn 9:16 tiếng Việt
của kênh Smart Penguin Insights TRƯỚC KHI dựng thật. Mục tiêu: sửa hết lỗi ngay bây giờ để bản dựng đạt từ 8/10.

Dùng công cụ Read mở TỪNG ảnh (mỗi ảnh là 1 khung hình, đã thu nhỏ). Dòng thời gian (giây, ảnh, thẻ đang hiện, lời đang đọc):
{timeline}

Toàn bộ lời đọc: "{narration}"
Video dài {dur:.0f} giây. Tiêu đề short đang hiện trên đầu: "{title}"

Các thẻ hình (chỉ số i, giây bắt đầu s):
{beats}

LUẬT GIÁ TRỊ (Trọng chốt 27/11, áp dụng cho MỌI câu lời đọc, MỌI thẻ hình, ảnh, chữ trên màn hình, kể cả câu mở và câu kết):
từng câu, từng hình có xứng với thời gian người xem bỏ ra không? Mỗi câu phải mang lại 1 điều MỚI: thông tin mới, con số mới,
bối cảnh, nguyên nhân, hệ quả, hoặc việc người xem làm được. KHÔNG ĐÁNG (phải đập đi viết lại, không được giữ):
nhắc lại con số hay ý đã nói (vd đã nói "gần 5 tỷ" thì không nói lại "4 tỷ 940 triệu"); câu đệm, câu chuyển rỗng, câu chỉ để kéo dài;
câu hỏi tu từ không được trả lời; thẻ hình chỉ nhắc lại chữ của phụ đề hoặc tiêu đề mà không thêm số liệu hay hình mới;
ảnh minh hoạ chung chung không liên quan nội dung.
CÁCH LÀM ĐÚNG (gỡ xung đột với luật "chữ trên hình khớp lời đọc"): mỗi câu lời đọc mang 1 con số hoặc 1 so sánh, và thẻ hình VẼ chính con số đó (số to, so sánh 2 bên, biểu đồ, logo), không chép lại câu chữ. Câu không có gì để vẽ thì viết lại câu cho có số, hoặc bỏ câu.
Thẻ hoặc đoạn nào KHÔNG ĐÁNG thì ghi vào "issues" bắt đầu bằng "KHÔNG ĐÁNG:" và sửa/thay thẻ đó ngay (không được giữ).

CHUYÊN GIA DỰNG VIDEO (Trọng 28/11: "bot review cần feedback nhiều hơn, phải là chuyên gia dựng video để đưa ra feedback giúp video
cuốn hút và chuyên nghiệp hơn"): bạn đồng thời là editor/motion designer 10 năm cho các kênh giáo dục tài chính top đầu
(kiểu Johnny Harris, Wendover, Kurzgesagt, Coin Bureau). Ngoài lỗi, hãy góp ý NGHỀ DỰNG cụ thể, làm được ngay trong khuôn Remotion:
- Bố cục và thứ bậc thị giác: mắt người xem nhìn vào đâu trước, chữ chính đủ to chưa, khoảng trống thừa hay chật, căn lề, cân đối trái phải.
- Chuyển động: hình có "sống" không (zoom chậm, đẩy vào biểu đồ, vẽ dần đường giá, số đếm lên, highlight vòng tròn/mũi tên vào điểm đang nói),
  chuyển cảnh có mượt và có lý do không, có đoạn nào đứng hình quá lâu.
- Nhịp dựng: cắt theo nhịp câu, mỗi ý 1 hình, đoạn cần "thở" (giữ chart lâu để người xem đọc) và đoạn cần nhanh.
- Kể bằng hình: chỗ nào nên thay chữ bằng biểu đồ, sơ đồ, so sánh, ảnh minh hoạ, ví dụ trực quan; chỗ nào nên phóng to (zoom) vào 1 vùng chart.
- Typography và màu: cỡ chữ, độ đậm, số liệu nổi bật, màu xanh/đỏ đúng nghĩa, đồng bộ brand, không quá nhiều kiểu chữ.
- Âm thanh: nhạc nền, chỗ nên có tiếng nhấn (whoosh, pop) hoặc khoảng lặng để nhấn ý.
- Mở và kết: 3 giây đầu có cú móc thị giác không, kết có lý do để xem tiếp không.
Mỗi góp ý ghi rõ giây/khung, đang thế nào, đổi thành gì, vì sao cuốn hơn. Viết như brief giao cho editor, không chung chung kiểu "làm sinh động hơn".
Góp ý nghề dựng ghi vào "issues" bắt đầu bằng "DỰNG:", cái nào sửa được bằng LỆNH SỬA bên dưới thì sửa luôn.

CHẤM THEO ĐÚNG TIÊU CHÍ BOT REVIEW SAU DỰNG, ghi mọi lỗi vào "issues" (ghi rõ ảnh nào):
1. Trình bày: chữ đè nhau, chữ bị thẻ đè, chữ tràn hoặc bị cắt mép; lỗi font (ô vuông, mất/vỡ dấu tiếng Việt); nhãn bị ngắt giữa cụm;
   chữ mồ côi ở dòng cuối; 2 số trong thẻ so sánh không thẳng hàng, số dính chữ VS; thẻ trống hoặc gần trống; ảnh mờ vỡ.
2. Khớp lời: chữ/số trên hình phải khớp lời đang đọc lúc đó; con số trên hình mà lời đọc không nhắc thì sai.
3. Không khẳng định mạnh hơn lời đọc/nguồn (vd lời đọc "nhận ý kiến từ chính phủ" mà thẻ ghi "Chính phủ đứng sau").
4. Thẻ so sánh (versus) phải là 2 CON SỐ, không phải 2 chữ giống nhau. So 2 đại lượng khác loại để nêu NGHỊCH LÝ
   (vd revenue kỷ lục vs giá giảm) là HỢP LỆ và rất đáng giữ. Chú thích nhỏ (note, sub) được ghi số liệu nguồn kèm theo
   dù lời đọc không đọc ra, miễn không mâu thuẫn lời đọc.
   ĐỪNG bỏ hay biến thẻ dữ liệu tốt thành thẻ chữ chỉ vì lệch chút ít; ưu tiên sửa chữ, dời giờ. Bỏ thẻ chỉ khi nó sai hoặc vô nghĩa.
   Câu hỏi cuối video dùng thẻ question (dấu ?), không dùng thẻ trích dẫn.
5. Nhịp: không thẻ nào đứng yên quá khoảng 5 giây; biểu đồ phải hiện đủ lúc lời đọc nhắc tới nó.
6. 2 giây đầu (khung bìa + tiêu đề) phải đủ gây tò mò, tiêu đề ≤ 46 ký tự, tối đa 2 dòng, có con số.

LỆNH SỬA ("fixes", áp theo thứ tự). KHÔNG đổi lời đọc. Con số mới chỉ dùng khi lời đọc có đúng số đó. Không dấu gạch ngang dài.
- {{"i": n, "label"/"text"/"sub"/"note": "...", "left_label"/"right_label"/"left_note"/"right_note": "..."}}: đổi chữ trên thẻ n
- {{"i": n, "s": giây}}: dời thẻ n sang giây khác (khớp lúc lời đọc nhắc tới)
- {{"i": n, "drop": true}}: bỏ thẻ n
- {{"i": n, "value": "..."}}: đổi số/chữ to của thẻ bignum (số mới phải có trong lời đọc, vd lời "chưa đầy 2 tuần" → "< 2 tuần")
- {{"i": n, "to_statement": "câu ngắn ≤ 50 ký tự"}}: đổi thẻ n thành thẻ chữ
- {{"i": n, "to_question": "câu hỏi ngắn ≤ 50 ký tự"}}: đổi thẻ n thành thẻ câu hỏi
- {{"add": {{"s": giây, "type": "statement|bignum|question", "text": "...", "value": "...", "label": "..."}}}}: thêm thẻ (KHÔNG thêm ảnh kho: ảnh tìm theo từ khoá hay lạc đề)
Trả về DUY NHẤT JSON:
{{"score": điểm dự kiến 1-10 nếu dựng NGUYÊN TRẠNG,
  "ok": true nếu không còn lỗi nào đáng sửa,
  "issues": [{{"frame": "tên ảnh", "problem": "mô tả ngắn, sửa thế nào"}}],
  "fixes": [...],
  "title": "tiêu đề short mới nếu cần, không thì để trống"}}"""


def log(*a):
    print(*a, flush=True)


def _claude(prompt: str, n_files: int) -> dict:
    tok = re.sub(r"\s+", "", os.getenv("CLAUDE_CODE_OAUTH_TOKEN", ""))
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    if tok:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
    r = subprocess.run(["claude", "-p", prompt + "\n\nChỉ in ra JSON hợp lệ, không thêm chữ nào khác.",
                        "--allowedTools", "Read", "--max-turns", str(n_files + 6),
                        "--model", os.getenv("PREFLIGHT_MODEL", "sonnet"), "--output-format", "text"],
                       env=env, capture_output=True, text=True, timeout=1200)
    m = re.search(r"\{.*\}", r.stdout, re.S)
    if not m:
        raise RuntimeError(f"Claude không trả JSON: {(r.stdout or r.stderr)[:300]}")
    return json.loads(m.group(0))


def _stills(props: dict, times: list[float], work: Path) -> list[tuple[float, Path]]:
    import insight_render as R
    from PIL import Image
    work.mkdir(parents=True, exist_ok=True)
    for old in list(work.glob("pre-f*")):
        old.unlink()
    R.run_remotion(props, work / "pre.mp4", frames=",".join(f"{t:g}" for t in times))
    out = []
    for png in work.glob("pre-f*.png"):
        try:
            t = float(png.stem[5:])
        except ValueError:
            continue
        jpg = png.with_suffix(".jpg")
        Image.open(png).convert("RGB").resize((540, 960)).save(jpg, quality=85)
        out.append((t, jpg))
    return sorted(out)


def _times(props: dict) -> list[float]:
    beats = props["scenes"][0].get("beats") or []
    dur = float(props.get("duration") or 30)
    cta_from = float((props.get("cta") or {}).get("from") or dur)
    times = [0.2, 2.0]   # khung bìa và tiêu đề sau khi bìa mờ đi
    cand = [float(b.get("s", 0)) + 1.3 for b in beats] + [x * 3.0 for x in range(1, int(cta_from // 3) + 1)]
    for t in sorted(cand):
        t = round(min(t, cta_from - 0.3), 2)
        if t > 2.2 and all(abs(t - x) > 0.9 for x in times):
            times.append(t)
    times = sorted(times)[:18]
    if props.get("cta"):
        times.append(round(cta_from + 0.8, 2))
    return times


def _said(words: list, t: float) -> str:
    return " ".join(w["t"] for w in words if abs(w["s"] - t) < 1.8)[:110]


def _cur_beat(beats: list, t: float) -> str:
    cur = None
    for i, b in sorted(enumerate(beats), key=lambda x: float(x[1].get("s", 0))):
        if float(b.get("s", 0)) - 0.15 <= t:
            cur = (i, b)
    return f"thẻ [{cur[0]}] {cur[1].get('type')}" if cur else "chưa có thẻ"


def _nums_ok(val: str, narration: str) -> bool:
    """Số mới trên thẻ phải có trong lời đọc (so chữ số: '130' trong '130 tỷ', '30' trong 'hơn 30%')."""
    nums = re.findall(r"\d+(?:[.,]\d+)?", str(val))
    flat = narration.replace(".", ",")
    return all(n.replace(".", ",") in flat for n in nums)


def _photo(q: str, k: int) -> str | None:
    import insight_lab as L
    import insight_render as R
    import video as V
    if not q or L._PERSON_HINT.search(q):
        return None
    for ori in ("landscape", "portrait"):
        res = V.search_pixabay(q, ori) or V.search_pexels(q, ori) or V.search_wikimedia(q, ori) or V.search_openverse(q, ori)
        if res:
            fn = f"img/preflight_{k}.jpg"
            (R.RD / "img").mkdir(parents=True, exist_ok=True)
            res[0].convert("RGB").save(R.RD / fn, quality=90)
            return fn
    return None


def _apply(props: dict, rv: dict, narration: str) -> int:
    sc = props["scenes"][0]
    beats = sc.get("beats") or []
    dur = float(props.get("duration") or 30)
    n, drop, add = 0, set(), []
    for fx in rv.get("fixes") or []:
        if isinstance(fx.get("add"), dict):
            a = fx["add"]
            t = a.get("type")
            if t not in ADD_TYPES:
                continue
            nb = {"type": t, "s": max(0.0, min(dur - 1.0, float(a.get("s") or 0)))}
            for k in ("text", "label", "sub"):
                if a.get(k):
                    nb[k] = P.nodash(str(a[k]))
            if t == "bignum":
                if not a.get("value") or not _nums_ok(a["value"], narration):
                    continue
                nb["value"] = P.nodash(str(a["value"]))
            if t == "photo":
                src = _photo(str(a.get("query") or ""), len(add))
                if not src:
                    continue
                nb["src"] = src
            add.append(nb)
            n += 1
            continue
        try:
            i = int(fx.get("i"))
            b = beats[i]
        except (TypeError, ValueError, IndexError):
            continue
        if fx.get("drop"):
            drop.add(i)
            n += 1
            continue
        if fx.get("to_question"):
            beats[i] = {"type": "question", "s": b.get("s", 0), "text": P.nodash(str(fx["to_question"]))[:60], "sub": b.get("sub", "")}
            n += 1
            continue
        if fx.get("value") and b.get("type") == "bignum" and _nums_ok(fx["value"], narration):
            b["value"] = P.nodash(str(fx["value"]))[:14]
            n += 1
        if fx.get("to_statement"):
            beats[i] = {"type": "statement", "s": b.get("s", 0), "text": P.nodash(str(fx["to_statement"]))[:60]}
            n += 1
            continue
        if fx.get("s") is not None:
            try:
                b["s"] = max(0.0, min(dur - 1.0, float(fx["s"])))
                n += 1
            except (TypeError, ValueError):
                pass
        for k in TEXT_KEYS:
            if fx.get(k) and (k in b or k == "sub"):
                b[k] = P.nodash(str(fx[k]))
                n += 1
        for side in ("left", "right"):
            for k in ("label", "note"):
                v = fx.get(f"{side}_{k}")
                if v and isinstance(b.get(side), dict):
                    b[side][k] = P.nodash(str(v))
                    n += 1
    sc["beats"] = sorted([b for j, b in enumerate(beats) if j not in drop] + add, key=lambda b: float(b.get("s", 0)))
    if rv.get("title") and len(str(rv["title"])) <= 46:
        props["shortTitle"] = P.nodash(str(rv["title"]))
        n += 1
    return n


def check_short(props: dict, work: Path, rounds: int = 2) -> dict:
    """Bot review xem trước cho 1 short. Sửa props tại chỗ. Trả báo cáo {ok, score_before, score, issues, rounds}."""
    if not (os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")) or os.getenv("PREFLIGHT") == "0":
        return {"ok": None, "skipped": True}
    sc = props["scenes"][0]
    words = sc.get("words") or []
    narration = " ".join(w["t"] for w in words)
    rep = {"ok": False, "issues": [], "rounds": 0}
    for r in range(rounds + 1):
        beats = sc.get("beats") or []
        try:
            shots = _stills(props, _times(props), work)
            timeline = "\n".join(f"- giây {t:g}: ảnh {p.resolve()} · {_cur_beat(beats, t)} · lời: \"{_said(words, t)}\"" for t, p in shots)
            bl = "\n".join(f"[{i}] s={float(b.get('s', 0)):.1f} "
                           + json.dumps({k: v for k, v in b.items() if k not in ('s', 'src', 'at')}, ensure_ascii=False)[:240]
                           for i, b in enumerate(beats))
            rv = _claude(PROMPT.format(timeline=timeline, narration=narration[:1500], dur=float(props.get("duration") or 0),
                                       title=props.get("shortTitle", ""), beats=bl), len(shots))
        except Exception as ex:
            log(f"   ! bot review xem trước lỗi, dựng tiếp như cũ: {str(ex)[:200]}")
            rep["error"] = str(ex)[:200]
            return rep
        if r == 0:
            rep["score_before"] = rv.get("score")
        rep.update(ok=bool(rv.get("ok")), score=rv.get("score"), issues=rv.get("issues") or [], rounds=r + 1)
        log(f"   Review xem trước vòng {r + 1}: dự kiến {rv.get('score', '?')}/10, "
            + ("ổn" if rep["ok"] else f"{len(rep['issues'])} lỗi")
            + "".join(f"\n     - {x.get('frame', '')}: {x.get('problem', '')}" for x in rep["issues"][:10]))
        if rep["ok"] or r == rounds:
            break
        changed = _apply(props, rv, narration)
        log(f"   Áp {changed} chỗ sửa, chụp lại để chấm lại")
        if not changed:
            break
    return rep


# ---------------------------------------------------------------------------
# Trọng 24/11 "bot có thể sửa những lỗi được mention để cải thiện video tốt hơn":
# sau khi dựng, bot review chấm < 8 thì Claude đọc góp ý (can_sua) và sửa KỊCH BẢN HÌNH (plan), dựng lại.
# Lời đọc không đổi (giọng đã đọc xong), chỉ đổi thẻ hình, tiêu đề short, chữ ảnh bìa.
FIX_PROMPT = """Bạn là biên tập viên sửa video ngắn 9:16 tiếng Việt kênh Smart Penguin Insights. Bot review vừa chấm bản dựng
{score}/10 và góp ý như dưới. Hãy sửa KỊCH BẢN HÌNH để lần dựng sau đạt từ 8/10. KHÔNG đổi lời đọc (giọng đã đọc xong).

LỜI ĐỌC: "{narration}"
TIÊU ĐỀ SHORT: "{title}" · CHỮ ẢNH BÌA: "{thumb}" · SỐ ẢNH BÌA: "{stat}"

GÓP Ý CỦA BOT REVIEW:
{issues}

CÁC THẺ HÌNH HIỆN TẠI (i, "at" = cụm từ trong lời đọc làm mốc thẻ hiện ra):
{beats}

Loại thẻ: bignum (value, label, tone up/down), versus (left/right: label, value, note, tone; sub), statement (text, sub),
question (text, sub, chỉ dùng cho câu hỏi cuối), chart (ticker, days, label; biểu đồ giá thật, % hiện là thay đổi trong đúng số
ngày đó, chọn days sao cho chiều đi của giá KHỚP ý đang nói), KHÔNG dùng photo (ảnh kho hay lạc đề),
logos, flow, dots. Nhãn ≤ 40 ký tự, versus nhãn ≤ 16. Số mới chỉ dùng khi lời đọc có số đó (note/sub được ghi số liệu nguồn kèm theo).
Không dấu gạch ngang dài. Mỗi 3 đến 5 giây nên đổi thẻ; đọc khoảng 3.5 từ mỗi giây.

Trả về DUY NHẤT JSON: {{"beats": [danh sách thẻ MỚI ĐẦY ĐỦ, mỗi thẻ có "at" là cụm từ NGUYÊN VĂN trong lời đọc],
 "short_title": "≤ 46 ký tự hoặc để trống", "thumb_text": "hoặc để trống", "changes": ["đã sửa gì, ứng với góp ý nào"]}}"""


def plan_fix(plan: dict, rv: dict) -> list[str]:
    """Sửa plan tại chỗ theo bot review. Trả danh sách thay đổi (rỗng nếu không sửa được)."""
    sec = plan["sections"][0]
    nar = sec["narration"]
    low = nar.lower()
    issues = "\n".join(f"- {x}" for x in (rv.get("can_sua") or [])) + (f"\n- Rủi ro bỏ xem: {rv['retention_risk']}" if rv.get("retention_risk") else "")
    bl = "\n".join(f"[{i}] {json.dumps({k: v for k, v in b.items() if k not in ('src',)}, ensure_ascii=False)[:300]}"
                   for i, b in enumerate(sec.get("beats") or []))
    out = _claude_text(FIX_PROMPT.format(score=rv.get("score", "?"), narration=nar, title=plan.get("short_title") or "",
                                         thumb=plan.get("thumb_text") or "", stat=plan.get("thumb_stat") or "", issues=issues, beats=bl))
    new = []
    for b in out.get("beats") or []:
        if not isinstance(b, dict) or not str(b.get("at", "")).strip() or str(b["at"]).lower() not in low:
            continue
        if b.get("type") == "bignum" and not _nums_ok(b.get("value", ""), nar):
            continue
        if b.get("type") == "photo" and not b.get("src") and not any(x.get("type") == "photo" and x.get("query") == b.get("query") for x in sec["beats"]):
            continue   # Trọng 28/11: không thêm ảnh kho mới
        if b.get("type") == "photo":
            q = str(b.get("query") or "")
            import insight_lab as L
            if L._PERSON_HINT.search(q):
                continue
            old = next((x for x in sec["beats"] if x.get("type") == "photo" and x.get("query") == q and x.get("src")), None)
            if old:
                b["src"] = old["src"]
            else:
                b.pop("src", None)
        new.append(P.nodash(b))
    if len(new) < max(3, len(sec.get("beats") or []) // 2):
        return []
    sec["beats"] = new
    if out.get("short_title") and len(out["short_title"]) <= 46:
        plan["short_title"] = P.nodash(out["short_title"])
        plan["short_hooks"] = {"0": plan["short_title"]}
    if out.get("thumb_text"):
        plan["thumb_text"] = P.nodash(out["thumb_text"])[:40]
    return [P.nodash(str(c)) for c in out.get("changes") or []] or ["đã sửa thẻ hình theo review"]


def _claude_text(prompt: str) -> dict:
    tok = re.sub(r"\s+", "", os.getenv("CLAUDE_CODE_OAUTH_TOKEN", ""))
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    if tok:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
    r = subprocess.run(["claude", "-p", prompt + "\n\nChỉ in ra JSON hợp lệ, không thêm chữ nào khác.", "--max-turns", "3",
                        "--model", os.getenv("PREFLIGHT_MODEL", "sonnet"), "--output-format", "text"],
                       env=env, capture_output=True, text=True, timeout=900)
    m = re.search(r"\{.*\}", r.stdout, re.S)
    if not m:
        raise RuntimeError(f"Claude không trả JSON: {(r.stdout or r.stderr)[:300]}")
    return json.loads(m.group(0))
