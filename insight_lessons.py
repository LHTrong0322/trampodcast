"""Gom BÀI HỌC cho video tiếp theo vào 1 file: <data>/insight/lessons.md (nhánh podcast-data).

Nguồn:
  1. Bot review chấm trước khi đăng (insight/reviews.json), chỉ tính video từ bản chuẩn STANDARD_TAG.
  2. Số liệu thật sau khi đăng (insight/performance.json, do growth_report.py cập nhật hằng tuần).
Dùng ở đâu:
  * Pipeline tự nạp mẹo vào bước viết kịch bản (insight.py produce).
  * Phiên Claude viết kịch bản nháp trong chat PHẢI đọc file này trước (xem HANDOFF.md):
      gh api 'repos/LHTrong0322/trampodcast/contents/insight/lessons.md?ref=podcast-data' -H 'Accept: application/vnd.github.raw'
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

STANDARD_TAG = "20261120-1915"
NAMES = {"hook_3s": "Hook 3 giây đầu", "hinh_anh_ro_rang": "Hình ảnh rõ ràng", "mau_sac_brand": "Màu sắc thương hiệu",
         "nhip_do": "Nhịp độ", "phu_de": "Phụ đề", "du_lieu_lien_quan": "Dữ liệu đúng ý", "thumbnail": "Ảnh bìa", "short_9x16": "Video ngắn"}


def _load(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def build(data_dir: Path) -> str:
    d = data_dir / "insight"
    reviews = [r for r in _load(d / "reviews.json", []) if str(r.get("tag", "")) >= STANDARD_TAG][-5:]
    perf = _load(d / "performance.json", {})
    vn = timezone(timedelta(hours=7))
    out = [f"# Bài học cho video tiếp theo (cập nhật {datetime.now(vn):%H:%M %d/%m/%Y})", ""]
    if reviews:
        avg = {}
        for r in reviews:
            for k, v in (r.get("scores") or {}).items():
                if isinstance(v, (int, float)):
                    avg.setdefault(k, []).append(v)
        avg = {k: sum(v) / len(v) for k, v in avg.items()}
        out += [f"## Bot review ({len(reviews)} video gần nhất từ bản chuẩn)",
                "Điểm trung bình: " + ", ".join(f"{NAMES.get(k, k)} {v:.1f}" for k, v in sorted(avg.items(), key=lambda x: x[1])),
                "Yếu nhất (ưu tiên sửa): " + ", ".join(NAMES.get(k, k) for k, _ in sorted(avg.items(), key=lambda x: x[1])[:3]), ""]
        tips = list(dict.fromkeys(t for r in reversed(reviews) for t in (r.get("script_tips") or [])))[:8]
        if tips:
            out += ["### Mẹo viết lời đọc"] + [f"- {t}" for t in tips] + [""]
        risks = [f"- [{r.get('tag')}] {r['retention_risk']}" for r in reversed(reviews) if r.get("retention_risk")][:3]
        if risks:
            out += ["### Đoạn dễ mất người xem"] + risks + [""]
        fixes = [f"- [{reviews[-1].get('tag')}] {x}" for x in (reviews[-1].get("can_sua") or [])]
        if fixes:
            out += ["### Việc cần sửa ở video gần nhất (phiên Claude sửa code nếu là lỗi hình ảnh)"] + fixes + [""]
    if perf.get("lessons"):
        out += [f"## Số liệu thật sau khi đăng (tuần {perf.get('week', '')})", perf.get("summary", ""), ""]
        out += ["### Bài học từ người xem thật"] + [f"- {x}" for x in perf["lessons"]] + [""]
        top = perf.get("top") or []
        if top:
            out += ["### Video hiệu quả nhất"] + [f"- {x}" for x in top[:5]] + [""]
    if len(out) <= 2:
        out.append("Chưa có dữ liệu review hay số liệu thật.")
    text = "\n".join(out).replace("\u2014", ",").replace("\u2013", ",")
    (d).mkdir(parents=True, exist_ok=True)
    (d / "lessons.md").write_text(text, encoding="utf-8")
    return text


def tips_for_script(data_dir: Path) -> list[str]:
    """Danh sách gạch đầu dòng để nạp vào prompt viết kịch bản."""
    text = build(data_dir)
    return [l[2:] for l in text.splitlines() if l.startswith("- ")][:12]


if __name__ == "__main__":
    print(build(Path(sys.argv[1] if len(sys.argv) > 1 else "public")))
