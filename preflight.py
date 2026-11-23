"""Soát hình TRƯỚC khi dựng (Trọng 24/11: "thêm 1 bước review lại ảnh trước khi dựng, bảo đảm không có lỗi font hay hiển thị xấu").

Cách làm: chụp sẵn vài khung (ảnh bìa, tiêu đề, mỗi thẻ hình lúc đã hiện xong), nhờ Claude NHÌN từng khung
và bắt lỗi trình bày: font lỗi (ô vuông, dấu tiếng Việt vỡ), chữ tràn/bị cắt, chữ bị thẻ đè, chữ mồ côi, lệch hàng, thẻ trống.
Có lỗi thì Claude đề xuất sửa CHỮ trên thẻ (rút gọn nhãn, đổi cách viết), bot áp vào rồi soát lại, tối đa 2 vòng.
Không bao giờ đổi con số, loại thẻ hay mốc thời gian. Không có Claude (thiếu token) thì bỏ qua bước này, dựng như cũ.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import podcast as P

TEXT_KEYS = ("label", "text", "sub", "note")

PROMPT = """Bạn là người soát hình cuối cùng cho video ngắn 9:16 tiếng Việt (TikTok/Shorts) của kênh Smart Penguin Insights.
Dùng công cụ Read mở TỪNG ảnh sau (mỗi ảnh là 1 khung hình của video, đã thu nhỏ):
{files}

Soát kỹ từng ảnh, chỉ bắt LỖI TRÌNH BÀY THẬT, nhìn thấy được:
- font lỗi: ô vuông, ký tự lạ, dấu tiếng Việt bị vỡ/lệch, chữ bị đổi sang font khác
- chữ tràn ra ngoài thẻ, bị cắt mất, bị thẻ khác hoặc phụ đề đè lên
- chữ mồ côi (1 từ đứng một mình ở dòng cuối của tiêu đề, thẻ chữ, nhãn)
- hai bên thẻ so sánh lệch hàng, số dính sát chữ VS, nhãn xuống dòng lệch nhau
- thẻ trống hoặc gần trống, ảnh vỡ/mờ, chữ quá nhỏ khó đọc trên điện thoại
Không chấm nội dung, không góp ý màu sắc hay gu thẩm mỹ chung chung.

Danh sách thẻ hình hiện tại (chỉ số i dùng để sửa):
{beats}

Nếu lỗi sửa được bằng cách đổi CHỮ (rút gọn nhãn/câu cho vừa, tránh chữ mồ côi), đưa bản sửa vào "fixes".
TUYỆT ĐỐI không đổi con số (value), loại thẻ, mốc thời gian, và không thêm ý mới. Giữ tiếng Việt tự nhiên, không dùng dấu gạch ngang dài.
Trả về DUY NHẤT JSON:
{{"ok": true nếu không còn lỗi nào đáng sửa,
  "issues": [{{"frame": "tên ảnh", "problem": "mô tả ngắn"}}],
  "fixes": [{{"i": chỉ số thẻ, "label": "...", "text": "...", "sub": "...", "left_label": "...", "right_label": "...", "left_note": "...", "right_note": "..."}}],
  "title": "tiêu đề short mới nếu tiêu đề bị lỗi, không thì để trống"}}
Trong mỗi mục fixes chỉ ghi những trường cần đổi."""


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
                       env=env, capture_output=True, text=True, timeout=900)
    m = re.search(r"\{.*\}", r.stdout, re.S)
    if not m:
        raise RuntimeError(f"Claude không trả JSON: {(r.stdout or r.stderr)[:300]}")
    return json.loads(m.group(0))


def _stills(props: dict, times: list[float], work: Path) -> list[Path]:
    import insight_render as R
    from PIL import Image
    work.mkdir(parents=True, exist_ok=True)
    base = work / "pre.mp4"
    for old in work.glob("pre-f*"):
        old.unlink()
    R.run_remotion(props, base, frames=",".join(f"{t:.2f}" for t in times))
    out = []
    for t in times:
        png = work / f"pre-f{t:.2f}.png"
        if not png.exists():
            cands = sorted(work.glob("pre-f*.png"))
            png = next((c for c in cands if abs(float(c.stem[5:]) - t) < 0.01), None)
        if png and png.exists():
            jpg = png.with_suffix(".jpg")
            Image.open(png).convert("RGB").resize((540, 960)).save(jpg, quality=85)
            out.append(jpg)
    return out


def _apply(props: dict, rv: dict) -> int:
    beats = props["scenes"][0].get("beats") or []
    n = 0
    for fx in rv.get("fixes") or []:
        try:
            b = beats[int(fx.get("i"))]
        except (TypeError, ValueError, IndexError):
            continue
        for k in TEXT_KEYS:
            if fx.get(k) and k in b:
                b[k] = P.nodash(str(fx[k]))
                n += 1
        for side in ("left", "right"):
            for k in ("label", "note"):
                v = fx.get(f"{side}_{k}")
                if v and isinstance(b.get(side), dict):
                    b[side][k] = P.nodash(str(v))
                    n += 1
    if rv.get("title") and len(str(rv["title"])) <= 46:
        props["shortTitle"] = P.nodash(str(rv["title"]))
        n += 1
    return n


def check_short(props: dict, work: Path, rounds: int = 2) -> dict:
    """Soát short trước khi dựng. Sửa props tại chỗ nếu Claude đề xuất. Trả báo cáo {ok, issues, rounds}."""
    if not (os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")) or os.getenv("PREFLIGHT") == "0":
        return {"ok": None, "skipped": True}
    beats = props["scenes"][0].get("beats") or []
    dur = float(props.get("duration") or 30)
    cta_from = float((props.get("cta") or {}).get("from") or dur)
    times = [0.2, 2.0]   # ảnh bìa (khung đầu) và tiêu đề sau khi bìa mờ đi
    for b in beats:
        t = min(float(b.get("s", 0)) + 1.3, cta_from - 0.3)
        if t > 2.2 and all(abs(t - x) > 0.6 for x in times):
            times.append(round(t, 2))
    if props.get("cta"):
        times.append(round(cta_from + 0.8, 2))
    rep = {"ok": False, "issues": [], "rounds": 0}
    for r in range(rounds + 1):
        try:
            imgs = _stills(props, times, work)
            listing = "\n".join(str(p.resolve()) for p in imgs)
            bl = "\n".join(f"[{i}] {json.dumps({k: v for k, v in b.items() if k not in ('s', 'src')}, ensure_ascii=False)[:260]}"
                           for i, b in enumerate(beats))
            rv = _claude(PROMPT.format(files=listing, beats=bl), len(imgs))
        except Exception as ex:
            log(f"   ! soát hình trước khi dựng lỗi, dựng tiếp như cũ: {str(ex)[:200]}")
            rep["error"] = str(ex)[:200]
            return rep
        rep.update(ok=bool(rv.get("ok")), issues=rv.get("issues") or [], rounds=r + 1)
        log(f"   Soát hình vòng {r + 1}: {'ổn' if rep['ok'] else str(len(rep['issues'])) + ' lỗi'}"
            + "".join(f"\n     - {x.get('frame', '')}: {x.get('problem', '')}" for x in rep["issues"][:8]))
        if rep["ok"] or r == rounds:
            break
        if not _apply(props, rv):   # lỗi không sửa được bằng chữ: dừng vòng, báo lại
            break
    rep["frames"] = [str(p) for p in imgs] if "imgs" in locals() else []
    return rep
