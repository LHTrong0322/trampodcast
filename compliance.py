#!/usr/bin/env python3
"""
BOT TUÂN THỦ (chạy trên GitHub TRƯỚC khi tạo Release / gửi Telegram).

Quét MỌI chữ sắp xuất bản theo quy tắc bắt buộc của Trọng (HANDOFF mục 5):
  1. KHÔNG có dấu gạch ngang dài (, , ,  ...) ở bất kỳ đâu: chữ trên video (props Remotion), phụ đề,
     ảnh bìa, SEO, mô tả Release, tin Telegram. Chữ thì tự sửa; nếu OCR thấy gạch ngang dài NGAY TRÊN
     KHUNG HÌNH (không sửa được nữa) thì CHẶN xuất bản và báo Telegram.
  2. Có logo + "SMART PENGUIN INSIGHTS" từ giây đầu, watermark @Trong0322, "Source: @tácgiả" (cảnh báo).
  3. Số liệu trên hình phải có thật trong bài gốc và nhất quán giữa video dài và short (cảnh báo).
  4. Ảnh bìa không giật tít tiêu cực (cảnh báo).

  python compliance.py selftest                 → tự kiểm tra bộ lọc
  python compliance.py scan <file.json|.txt>... → quét chữ trong file
  python compliance.py ocr <video.mp4|ảnh.png>  → OCR khung hình tìm gạch ngang dài
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import podcast as P

DASH_CHARS = P.DASHES  # các loại gạch ngang dài (em dash, en dash, horizontal bar...)
DASH_RE = re.compile(f"[{DASH_CHARS}]")
# gạch nối đứng giữa câu kiểu "a - b" (cũng bị coi là gạch ngang)
SPACED_HYPHEN_RE = re.compile(r"(?<=\S)\s+-{1,3}\s+(?=\S)")
# trên ảnh (OCR): chỉ tính khi gạch ngang dài nằm giữa 2 CHỮ thật (tránh nhầm với đường kẻ trang trí)
OCR_DASH_RE = re.compile(rf"[0-9A-Za-zÀ-ỹ]{{2,}}\s*[{DASH_CHARS}]+\s*[0-9A-Za-zÀ-ỹ]{{2,}}")
SKIP_KEYS = {"audio", "avatar", "cover", "logo", "images", "img", "url", "file", "projectLogo", "bg", "series", "spark"}
BAD_THUMB = re.compile(r"SẮP CHẾT|\bCHẾT\b|\bSẬP\b|TOANG|BAY MÀU|VỀ 0|LỪA ĐẢO|\bSCAM\b", re.I)


def find_dashes(x, path: str = "") -> list[tuple[str, str]]:
    """Trả về [(vị trí, đoạn chữ)] có gạch ngang dài / gạch nối giữa câu."""
    out = []
    if isinstance(x, str):
        for m in list(DASH_RE.finditer(x)) + list(SPACED_HYPHEN_RE.finditer(x)):
            out.append((path or "text", x[max(0, m.start() - 25):m.end() + 25].replace("\n", " ")))
    elif isinstance(x, dict):
        for k, v in x.items():
            if k not in SKIP_KEYS:
                out += find_dashes(v, f"{path}.{k}" if path else str(k))
    elif isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            out += find_dashes(v, f"{path}[{i}]")
    return out


def fix(x):
    """Tự sửa: thay gạch ngang dài bằng dấu phẩy (dùng chung bộ lọc nodash của cả dự án)."""
    return P.nodash(x)


def clean_file(p: Path) -> list[tuple[str, str]]:
    """Quét 1 file JSON/chữ; có vi phạm thì sửa thẳng trong file. Trả về các vi phạm đã sửa."""
    if not p.exists():
        return []
    raw = p.read_text(encoding="utf-8")
    try:
        obj = json.loads(raw)
    except Exception:
        obj = None
    bad = find_dashes(obj if obj is not None else raw)
    if bad:
        if obj is not None:
            fixed = P.nodash({k: v for k, v in obj.items()}) if isinstance(obj, dict) else P.nodash(obj)
            # giữ nguyên các trường đường dẫn file/ảnh
            if isinstance(obj, dict):
                for k in SKIP_KEYS & set(obj):
                    fixed[k] = obj[k]
            p.write_text(json.dumps(fixed, ensure_ascii=False, indent=1 if "\n" in raw[:200] else None), encoding="utf-8")
        else:
            p.write_text(P.nodash(raw), encoding="utf-8")
    return [(f"{p.name}:{w}", s) for w, s in bad]


# ---------------------------------------------------------------------------
# OCR khung hình
# ---------------------------------------------------------------------------
def _langs() -> str:
    try:
        r = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, timeout=30)
        have = set(r.stdout.split())
    except Exception:
        return ""
    return "+".join(x for x in ("vie", "eng") if x in have) or "eng"


def duration(video: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def grab(video: Path, t: float, out: Path) -> bool:
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", str(out)],
                       capture_output=True)
    return r.returncode == 0 and out.exists()


def ocr(img: Path, lang: str) -> str:
    try:
        r = subprocess.run(["tesseract", str(img), "-", "-l", lang, "--psm", "11"], capture_output=True, text=True, timeout=120)
        return r.stdout
    except Exception:
        return ""


def sample_times(dur: float, short: bool) -> list[float]:
    if dur <= 0:
        return []
    ts = [0.3, 1, 3, 10, 30, dur / 2, dur - 2] if not short else [0.3, 1.5, 4, dur / 2, dur - 2]
    step = 20 if not short else 8  # quét đều cả video
    ts += [x for x in range(int(step / 2), int(dur), step)]
    return sorted({round(min(max(0.1, t), dur - 0.2), 1) for t in ts})


def ocr_media(path: Path, short: bool = False, work: Path | None = None) -> dict:
    """OCR các khung hình mẫu của 1 video (hoặc 1 ảnh). Trả về {'dash': [...], 'texts': {giây: chữ}}."""
    lang = _langs()
    res = {"dash": [], "texts": {}, "ok": bool(lang)}
    if not lang:
        return res
    work = work or Path(tempfile.mkdtemp(prefix="ocr-"))
    work.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
        items = [(0.0, path)]
    else:
        items = []
        for t in sample_times(duration(path), short):
            f = work / f"{path.stem}-{t:.1f}.png"
            if grab(path, t, f):
                items.append((t, f))
    for t, f in items:
        txt = ocr(f, lang)
        res["texts"][t] = txt
        for m in OCR_DASH_RE.finditer(txt):
            res["dash"].append({"file": path.name, "t": t, "text": m.group(0), "frame": str(f)})
    return res


# ---------------------------------------------------------------------------
# kiểm tra toàn bộ trước khi xuất bản
# ---------------------------------------------------------------------------
def nums(s: str) -> set:
    return {x.replace(",", ".") for x in re.findall(r"\d+(?:[.,]\d+)?", s or "")}


def check_publish(res: dict, seo: dict, out_dir: Path, thumb: Path | None, extra_texts: list[str] | None = None,
                  do_ocr: bool = True) -> dict:
    """Chạy toàn bộ quy tắc. Trả về báo cáo {ok, blocked, fixed, warnings, ocr_dash}.
    seo được sửa tại chỗ (dict); các file props/seo trong out_dir được sửa thẳng."""
    rep = {"fixed": [], "warnings": [], "ocr_dash": [], "blocked": False}
    # 1) chữ: props video dài/short, props ảnh bìa, SEO, mô tả Release, tin nhắn
    for p in sorted(out_dir.glob("props-*.json")) + sorted(out_dir.glob("*.props.json")) + sorted(out_dir.glob("seo-*.json")):
        rep["fixed"] += clean_file(p)
    bad = find_dashes(seo, "seo")
    if bad:
        rep["fixed"] += bad
        fixed = fix(seo)
        seo.clear()
        seo.update(fixed)
    for i, t in enumerate(extra_texts or []):
        rep["fixed"] += [(f"tin_nhan[{i}]", s) for _, s in find_dashes(t)]
    rep["fixed"] += [(f"plan.{w}", s) for w, s in find_dashes({k: v for k, v in res["plan"].items() if k not in ("posts",)})]
    # 2) số liệu: con số trên hình phải có thật trong bài gốc; video dài và short dùng cùng số
    src = nums(" ".join(p.get("text", "") for p in res["plan"].get("posts") or []))
    for sc in res.get("scenes", []):
        for k in ("stat", "keyStat"):
            v = sc.get(k) or ""
            if v and not nums(v) <= src:
                rep["warnings"].append(f"Số '{v}' ({sc.get('type')} {sc.get('idx', '')}) không thấy trong bài gốc")
    # 3) ảnh bìa
    thumb_props = out_dir.glob("*.props.json")
    for tp in thumb_props:
        try:
            tx = json.loads(tp.read_text(encoding="utf-8")).get("text", "")
            if BAD_THUMB.search(tx):
                rep["warnings"].append(f"Ảnh bìa có chữ tiêu cực: {tx}")
        except Exception:
            pass
    # 4) OCR khung hình: gạch ngang dài trên hình thì KHÔNG tự sửa được → chặn
    if do_ocr and shutil.which("tesseract"):
        work = out_dir / "_ocr"
        media = [(Path(res["long"]), False)] + [(Path(s["path"]), True) for s in res.get("shorts", [])]
        if thumb and Path(thumb).exists():
            media.append((Path(thumb), False))
        first_txt = ""
        all_txt = ""
        for m, short in media:
            if not m.exists():
                continue
            r = ocr_media(m, short, work)
            rep["ocr_dash"] += r["dash"]
            all_txt += " ".join(r["texts"].values())
            if m == Path(res["long"]) and r["texts"]:
                first_txt = r["texts"][min(r["texts"])]
        if rep["ocr_dash"]:
            rep["blocked"] = True
        if first_txt and "PENGUIN" not in first_txt.upper():
            rep["warnings"].append("OCR không thấy 'SMART PENGUIN INSIGHTS' ở giây đầu video dài")
        if all_txt and "Trong0322" not in all_txt.replace(" ", ""):
            rep["warnings"].append("OCR không thấy watermark @Trong0322")
        if all_txt and "Source" not in all_txt:
            rep["warnings"].append("OCR không thấy 'Source: @tácgiả'")
    elif do_ocr:
        rep["warnings"].append("Máy dựng chưa có tesseract nên chưa OCR khung hình")
    rep["ok"] = not rep["blocked"]
    return rep


def report_text(rep: dict) -> str:
    lines = ["🛡 BOT TUÂN THỦ: " + ("❌ CHẶN XUẤT BẢN" if rep["blocked"] else "✅ đạt")]
    if rep["fixed"]:
        lines.append(f"• Đã tự sửa {len(rep['fixed'])} chỗ có gạch ngang dài trong chữ (thay bằng dấu phẩy)")
    if rep["ocr_dash"]:
        lines.append("• Thấy gạch ngang dài NGAY TRÊN HÌNH (không sửa được, cần dựng lại):")
        lines += [f"   {d['file']} giây {d['t']}: \"{d['text']}\"" for d in rep["ocr_dash"][:8]]
    for w in rep["warnings"][:8]:
        lines.append("• Lưu ý: " + w)
    return P.nodash("\n".join(lines))


def selftest():
    em, en, bar = "\u2014", "\u2013", "\u2015"  # viết dạng mã để chính file này không chứa gạch ngang dài
    s = f"Altcoin {em} sắp chết {en} thật sự {bar} không - đâu"
    assert find_dashes(s), "không bắt được gạch ngang"
    assert not find_dashes(fix(s)), fix(s)
    assert not find_dashes(fix({"a": [s], "b": {"c": s}})), "sửa đệ quy lỗi"
    assert OCR_DASH_RE.search(f"Kyle {em} nhà đầu tư") and not OCR_DASH_RE.search(f"O2 {em}{em}"), "OCR regex lỗi"
    print("✓ compliance selftest ok")


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "selftest":
        return selftest()
    cmd, files = sys.argv[1], [Path(x) for x in sys.argv[2:]]
    if cmd == "scan":
        bad = [b for f in files for b in clean_file(f)]
        print(json.dumps(bad, ensure_ascii=False, indent=1))
        sys.exit(1 if bad else 0)
    if cmd == "ocr":
        hits = [d for f in files for d in ocr_media(f, "short" in f.name)["dash"]]
        print(json.dumps(hits, ensure_ascii=False, indent=1))
        sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
