"""VÒNG 1: Claude chấm kịch bản TRƯỚC khi gửi Trọng duyệt (Trọng chốt 21/11).

Quy trình 2 vòng chấm:
  Vòng 1 (file này): chấm kịch bản nháp trên thang 10. Dưới 8 điểm thì sửa theo góp ý rồi chấm lại.
                     Chỉ khi đạt từ 8 điểm trở lên mới chốt nháp gửi Trọng.
  Vòng 2 (insight_publish.review): chấm video sau khi dựng (bot review cũ).

Dùng tay:  python script_review.py scripts/<ten>-draft.md
In ra JSON: {"score": 8.4, "scores": {...}, "pass": true, "fixes": [...], "rewrites": {...}}
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

PASS = 8.0

RUBRIC = """Bạn là biên tập viên kịch bản YouTube crypto tiếng Việt, khó tính, chấm kịch bản cho kênh "Smart Penguin Insights"
(video 16:9 khoảng 4 phút + 2 video ngắn 9:16, giọng đọc máy vibe KOL crypto, khoảng 210 từ/phút).

Chấm THẲNG TAY từng tiêu chí trên thang 10 (số thập phân được):
- hook_3s: 3 giây đầu có con số hoặc nghịch lý, nói rõ người xem được gì, không mở bằng tên tác giả hay mục lục
- loi_hua: hứa rõ số lượng (vd "4 câu hỏi") ngay đầu và đếm to đúng như hứa
- giu_chan: cứ 40 đến 60 giây có câu móc hoặc câu hỏi chuyển phần; không có đoạn lý thuyết khô kéo dài
- gia_tri: mỗi phần có ví dụ thật + "vậy bạn làm gì" dùng được ngay; đúng với tiêu đề
- de_hieu: câu ngắn (đa số dưới 20 từ), thuật ngữ khó có giải thích ngắn lần đầu, đọc to nghe tự nhiên
- chinh_xac: số liệu khớp bài gốc, không bịa, không hô hào mua bán, có câu "không phải lời khuyên đầu tư"
- quy_tac: đúng quy tắc từ ngữ của Trọng (xem bên dưới)
- ket: kết bằng nhắc lại ý chính trong 1 câu + kêu gọi bình luận cụ thể
- hinh_anh: chữ trên hình ngắn gọn, đổi kiểu hình thường xuyên, ảnh bìa đọc được khi thu nhỏ (tối đa 2 dòng chữ lớn)
- short: 2 video ngắn có câu mở gây tò mò, tự đứng được một mình

QUY TẮC TỪ NGỮ CỦA TRỌNG (vi phạm thì quy_tac tối đa 5):
- Không dùng dấu gạch ngang dài (em dash, en dash).
- Nói insider (không "người trong cuộc"), retail (không "nhỏ lẻ"), unlock (không "mở khoá"),
  revenue hoặc doanh thu (không "lợi nhuận").
- Thuật ngữ giữ tiếng Anh (buyback, tokenomics, holder, narrative...). Viết tắt phổ thông (FDV, DCA, TVL, VC, ETF, ATH, TGE,
  DEX, CEX, KOL...) dùng nguyên, KHÔNG giải thích. Chỉ viết tắt dài hoặc ít gặp mới kèm giải thích ngắn.

BÀI HỌC TỪ CÁC VIDEO TRƯỚC (kênh đang yếu nhất ở nhịp độ, hook 3 giây và video ngắn):
{lessons}

BÀI GỐC (để kiểm tra số liệu):
{source}

KỊCH BẢN NHÁP:
{draft}

Điểm tổng = trung bình các tiêu chí. Trả về DUY NHẤT JSON:
{{"score": số, "scores": {{"hook_3s": số, ...}},
  "fixes": ["việc sửa cụ thể, chỉ rõ phần nào, câu nào, sửa thành gì"],
  "rewrites": {{"hook": "câu hook viết lại nếu hook dưới 8, không thì để trống", "...": "..."}},
  "nhan_xet": "2 câu tóm tắt"}}"""


def run_claude(prompt: str) -> dict:
    tok = re.sub(r"\s+", "", os.getenv("CLAUDE_CODE_OAUTH_TOKEN", ""))
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    if tok:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
    model = os.getenv("SCRIPT_REVIEW_MODEL", "sonnet")
    r = subprocess.run(["claude", "-p", prompt + "\n\nChỉ in ra JSON hợp lệ, không thêm chữ nào khác.",
                        "--max-turns", "3", "--model", model, "--output-format", "text"],
                       env=env, capture_output=True, text=True, timeout=900)
    m = re.search(r"\{.*\}", r.stdout, re.S)
    if not m:
        raise RuntimeError(f"Claude không trả JSON: {(r.stdout or r.stderr)[:300]}")
    return json.loads(m.group(0))


def review(draft: str, source: str = "", lessons: str = "") -> dict:
    rv = run_claude(RUBRIC.format(draft=draft, source=source or "(không có)", lessons=lessons or "(chưa có)"))
    sc = rv.get("scores") or {}
    if sc and not rv.get("score"):
        rv["score"] = round(sum(float(v) for v in sc.values()) / len(sc), 1)
    rv["pass"] = float(rv.get("score") or 0) >= PASS
    return rv


if __name__ == "__main__":
    draft = Path(sys.argv[1]).read_text(encoding="utf-8")
    source = Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) > 2 and Path(sys.argv[2]).exists() else ""
    lessons = Path("lessons.md").read_text(encoding="utf-8") if Path("lessons.md").exists() else ""
    rv = review(draft, source, lessons)
    print("=====REVIEW=====")
    print(json.dumps(rv, ensure_ascii=False, indent=1))
    print("=====END=====")
