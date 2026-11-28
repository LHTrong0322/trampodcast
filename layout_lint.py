"""Máy đo bố cục (Trọng 28/11: "hình ảnh cẩu thả... bot kiểm tra đang làm cái quái gì vậy?").

Trước khi xuất video, dựng thử ảnh nhỏ mỗi 0.5 giây (remotion/lint.mjs + src/probe.tsx) và đo vị trí THẬT của mọi dòng chữ:
  de_chu         chữ đè lên chữ
  bi_che         chữ bị thẻ/ảnh che MỘT PHẦN (lòi ra mép thẻ)
  chu_bi_cat     chữ bị cắt mép khung
  tran_man_hinh  chữ ra ngoài màn hình
  tu_mo_coi      một từ đứng trơ trọi ở dòng cuối
Lỗi chỉ tính khi kéo dài từ 1 giây trở lên (bỏ qua khung đang chạy hiệu ứng chuyển cảnh).
Không dùng AI, không tốn lượt. Kết quả còn gom toàn bộ chữ hiện trên hình để soát chính tả (spell_check).
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
NAMES = {"de_chu": "chữ đè lên chữ", "bi_che": "chữ bị thẻ che một phần", "chu_bi_cat": "chữ bị cắt mép",
         "tran_man_hinh": "chữ tràn ra ngoài màn hình", "tu_mo_coi": "từ mồ côi ở dòng cuối"}
SERIOUS = {"de_chu", "bi_che", "chu_bi_cat", "tran_man_hinh"}


def log(*a):
    print(*a, flush=True)


def run(props: dict, work: Path, step: float = 0.5) -> dict:
    """Chạy máy đo trên props của Remotion. Trả JSON thô {fps, duration, frames:[{t, texts, issues}]}."""
    work.mkdir(parents=True, exist_ok=True)
    pj, out = work / "lint-props.json", work / "lint.json"
    pj.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    env = {**os.environ, "CONCURRENCY": os.getenv("CONCURRENCY", "")}
    subprocess.run(["node", "lint.mjs", str(pj.resolve()), str(out.resolve()), str(step)], cwd=ROOT / "remotion",
                   check=True, env=env, timeout=1800, capture_output=True, text=True)
    return json.loads(out.read_text(encoding="utf-8"))


def persistent(raw: dict, min_s: float = 1.0) -> list[dict]:
    """Gộp lỗi giống nhau ở các khung liền nhau thành 1 đoạn {kind, text, other, start, end}; chỉ giữ đoạn dài >= min_s."""
    frames = raw.get("frames") or []
    step = (frames[1]["t"] - frames[0]["t"]) if len(frames) > 1 else 0.5
    open_: dict[tuple, dict] = {}
    done: list[dict] = []
    for fr in frames:
        keys = set()
        for it in fr.get("issues") or []:
            k = (it.get("kind"), it.get("text", "")[:60], it.get("other", "")[:40])
            keys.add(k)
            if k in open_ and fr["t"] - open_[k]["end"] <= step * 1.5:
                open_[k]["end"] = fr["t"]
            else:
                if k in open_:
                    done.append(open_.pop(k))
                open_[k] = {"kind": k[0], "text": k[1], "other": k[2], "start": fr["t"], "end": fr["t"]}
        for k in [k for k in open_ if k not in keys and fr["t"] - open_[k]["end"] > step * 1.5]:
            done.append(open_.pop(k))
    done += open_.values()
    out = [d for d in done if d["end"] - d["start"] + step >= min_s]
    # cùng 1 lỗi trên nhiều từ của cùng 1 dòng: gộp theo (kind, giây bắt đầu)
    merged: dict[tuple, dict] = {}
    for d in sorted(out, key=lambda x: (x["start"], x["kind"])):
        k = (d["kind"], d["start"], d["other"])
        if k in merged:
            merged[k]["text"] = (merged[k]["text"] + " " + d["text"])[:90]
            merged[k]["end"] = max(merged[k]["end"], d["end"])
        else:
            merged[k] = dict(d)
    return list(merged.values())


def texts(raw: dict) -> list[str]:
    """Mọi cụm chữ từng hiện trên hình (không trùng), để soát chính tả."""
    seen, out = set(), []
    for fr in raw.get("frames") or []:
        for t in fr.get("texts") or []:
            t = " ".join(str(t).split())
            if len(t) > 1 and t not in seen:
                seen.add(t)
                out.append(t)
    return out


def report(issues: list[dict], limit: int = 12) -> list[str]:
    """Câu dễ đọc cho Telegram và cho bot sửa."""
    out = []
    for d in sorted(issues, key=lambda x: x["start"])[:limit]:
        s = f"giây {d['start']:.0f} đến {d['end'] + 0.5:.0f}: {NAMES.get(d['kind'], d['kind'])}: \"{d['text'][:60]}\""
        if d.get("other"):
            s += f" (với \"{d['other'][:40]}\")"
        out.append(s)
    return out


def check(props: dict, work: Path) -> dict:
    """Chạy máy đo, không bao giờ làm hỏng lượt dựng: lỗi máy đo thì trả ok=None."""
    try:
        raw = run(props, work)
    except Exception as ex:
        msg = getattr(ex, "stderr", "") or str(ex)
        log(f"   ! máy đo bố cục lỗi, bỏ qua: {str(msg)[-300:]}")
        return {"ok": None, "issues": [], "texts": [], "lines": []}
    iss = persistent(raw)
    serious = [d for d in iss if d["kind"] in SERIOUS]
    res = {"ok": not serious, "issues": iss, "serious": len(serious), "texts": texts(raw), "lines": report(iss)}
    log(f"   📐 Máy đo bố cục: {len(raw.get('frames') or [])} khung, {len(serious)} lỗi nặng, {len(iss) - len(serious)} lỗi nhẹ")
    for line in res["lines"]:
        log("      · " + line)
    return res
