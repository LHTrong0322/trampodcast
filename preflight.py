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
ADD_TYPES = ("statement", "bignum", "photo", "question")

PROMPT = """Bạn là biên tập viên TikTok/YouTube Shorts kỳ cựu mảng crypto, đang XEM TRƯỚC một video ngắn 9:16 tiếng Việt
của kênh Smart Penguin Insights TRƯỚC KHI dựng thật. Mục tiêu: sửa hết lỗi ngay bây giờ để bản dựng đạt từ 8/10.

Dùng công cụ Read mở TỪNG ảnh (mỗi ảnh là 1 khung hình, đã thu nhỏ). Dòng thời gian (giây, ảnh, thẻ đang hiện, lời đang đọc):
{timeline}

Toàn bộ lời đọc: "{narration}"
Video dài {dur:.0f} giây. Tiêu đề short đang hiện trên đầu: "{title}"

Các thẻ hình (chỉ số i, giây bắt đầu s):
{beats}

CHẤM THEO ĐÚNG TIÊU CHÍ BOT REVIEW SAU DỰNG, ghi mọi lỗi vào "issues" (ghi rõ ảnh nào):
1. Trình bày: chữ đè nhau, chữ bị thẻ đè, chữ tràn hoặc bị cắt mép; lỗi font (ô vuông, mất/vỡ dấu tiếng Việt); nhãn bị ngắt giữa cụm;
   chữ mồ côi ở dòng cuối; 2 số trong thẻ so sánh không thẳng hàng, số dính chữ VS; thẻ trống hoặc gần trống; ảnh mờ vỡ.
2. Khớp lời: chữ/số trên hình phải khớp lời đang đọc lúc đó; con số trên hình mà lời đọc không nhắc thì sai.
3. Không khẳng định mạnh hơn lời đọc/nguồn (vd lời đọc "nhận ý kiến từ chính phủ" mà thẻ ghi "Chính phủ đứng sau").
4. Thẻ so sánh (versus) phải là 2 CON SỐ so được với nhau, không phải 2 chữ giống nhau.
5. Nhịp: không thẻ nào đứng yên quá khoảng 5 giây; biểu đồ phải hiện đủ lúc lời đọc nhắc tới nó.
6. 2 giây đầu (khung bìa + tiêu đề) phải đủ gây tò mò, tiêu đề ≤ 46 ký tự, tối đa 2 dòng, có con số.

LỆNH SỬA ("fixes", áp theo thứ tự). KHÔNG đổi lời đọc. Con số mới chỉ dùng khi lời đọc có đúng số đó. Không dấu gạch ngang dài.
- {{"i": n, "label"/"text"/"sub"/"note": "...", "left_label"/"right_label"/"left_note"/"right_note": "..."}}: đổi chữ trên thẻ n
- {{"i": n, "s": giây}}: dời thẻ n sang giây khác (khớp lúc lời đọc nhắc tới)
- {{"i": n, "drop": true}}: bỏ thẻ n
- {{"i": n, "to_statement": "câu ngắn ≤ 50 ký tự"}}: đổi thẻ n thành thẻ chữ
- {{"add": {{"s": giây, "type": "statement|bignum|question|photo", "text": "...", "value": "...", "label": "...", "query": "2-4 từ tiếng Anh cảnh/đồ vật, KHÔNG tên người"}}}}: thêm thẻ
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
