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
VALUE_MIN = 8.0   # Trọng 27/11: dang_xem dưới 8 thì KHÔNG qua, dù điểm tổng cao

VALUE_RULE = """LUẬT GIÁ TRỊ (Trọng chốt 27/11, áp dụng cho MỌI câu lời đọc, MỌI thẻ hình, ảnh, chữ trên màn hình, kể cả câu mở và câu kết):
từng câu, từng hình có xứng với thời gian người xem bỏ ra không? Mỗi câu phải mang lại 1 điều MỚI: thông tin mới, con số mới,
bối cảnh, nguyên nhân, hệ quả, hoặc việc người xem làm được. KHÔNG ĐÁNG (phải đập đi viết lại, không được giữ):
nhắc lại con số hay ý đã nói (vd đã nói "gần 5 tỷ" thì không nói lại "4 tỷ 940 triệu"); câu đệm, câu chuyển rỗng, câu chỉ để kéo dài;
câu hỏi tu từ không được trả lời; thẻ hình chỉ nhắc lại chữ của phụ đề hoặc tiêu đề mà không thêm số liệu hay hình mới;
ảnh minh hoạ chung chung không liên quan nội dung.
CÁCH LÀM ĐÚNG (gỡ xung đột với luật "chữ trên hình khớp lời đọc"): mỗi câu lời đọc mang 1 con số hoặc 1 so sánh, và thẻ hình VẼ chính con số đó (số to, so sánh 2 bên, biểu đồ, logo), không chép lại câu chữ. Câu không có gì để vẽ thì viết lại câu cho có số, hoặc bỏ câu."""

RUBRIC = """Bạn là biên tập viên kịch bản YouTube crypto tiếng Việt, khó tính, chấm kịch bản cho kênh "Smart Penguin Insights"
(video 16:9 khoảng 4 phút + 2 video ngắn 9:16, giọng đọc máy vibe KOL crypto, khoảng 210 từ/phút).

Chấm THẲNG TAY từng tiêu chí trên thang 10 (số thập phân được):
- hook_3s: 3 giây đầu có con số hoặc nghịch lý, nói rõ người xem được gì, không mở bằng tên tác giả hay mục lục
- loi_hua: hứa rõ số lượng (vd "4 câu hỏi") ngay đầu và đếm to đúng như hứa
- giu_chan: cứ 40 đến 60 giây có câu móc hoặc câu hỏi chuyển phần; không có đoạn lý thuyết khô kéo dài
- gia_tri: mỗi phần có ví dụ thật + "vậy bạn làm gì" dùng được ngay; đúng với tiêu đề
- de_hieu: câu ngắn (đa số dưới 20 từ), đọc to nghe tự nhiên; thuật ngữ thường có giải thích ngắn, nhưng KHÔNG bắt buộc giải thích hết (Trọng chốt 21/11: có đoạn được viết chuyên nghiệp như pro researcher), không trừ điểm vì thế
- chinh_xac: số liệu khớp bài gốc, không bịa, không hô hào mua bán, có câu "không phải lời khuyên đầu tư" Trọng 27/11: số CHƯA thấy trong nguồn được đưa KHÔNG tự động là sai; ghi vào fixes dạng "cần kiểm chứng: <số>, tra nguồn" thay vì đòi xoá, chỉ đòi bỏ khi biết chắc số sai. ĐÚNG SỰ THẬT quan trọng hơn ĐÚNG NGUỒN: số đúng, chứng minh được ở bất kỳ nguồn uy tín nào là hợp lệ, không trừ điểm vì "không có trong nguồn được đưa". Dữ liệu lịch sử phổ biến (đáy, đỉnh các chu kỳ trước, ATH, sự kiện lớn như FTX, Luna, halving) là kiến thức chung của ngành: giữ, không đòi nguồn trong bài, chỉ bỏ khi biết chắc là sai
- quy_tac: đúng quy tắc từ ngữ của Trọng (xem bên dưới)
- ket: kết bằng nhắc lại ý chính trong 1 câu + kêu gọi bình luận cụ thể; có sẵn 1 câu hỏi cho bình luận ghim (kéo thảo luận, vd "Bạn đang hold coin nào?")
- hinh_anh: chữ trên hình ngắn gọn, đổi kiểu hình thường xuyên, ảnh bìa đọc được khi thu nhỏ (tối đa 2 dòng chữ lớn)
- short: 2 video ngắn có câu mở gây tò mò, tự đứng được một mình. Trọng 27/11: câu đầu CẤM mở bằng tên tác giả, phải là HIGHLIGHT đắt nhất (con số sốc, nghịch lý, kết luận bất ngờ) tạo tò mò giữ chân; short nào mở bằng tên tác giả thì short tối đa 4
- giao_duc (BỘ LỌC GIÁO DỤC, Trọng chốt 21/11): tên riêng lạ (quỹ, tổ chức, cơ chế như DWF Labs, Assistance Fund) được giải thích 1 câu lần đầu;
  mọi so sánh phải có con số cụ thể của CẢ HAI bên (vd % revenue dùng buyback của từng dự án);
  SAU mỗi kiến thức phức tạp hoặc insight phải có ví dụ cụ thể, dễ hình dung (số thật, coin thật, hoặc phép so sánh đời thường như "cứ 100 đô phí...").
  Thiếu một trong ba điều này thì giao_duc tối đa 6.
- dang_xem (LUẬT GIÁ TRỊ, Trọng chốt 27/11): soát TỪNG câu lời đọc và TỪNG thẻ hình theo LUẬT GIÁ TRỊ bên dưới.
  Có 1 câu hoặc 1 thẻ không đáng thì dang_xem tối đa 6, có từ 2 chỗ trở lên thì tối đa 4. Mỗi chỗ không đáng phải ghi vào fixes
  dạng "Câu/thẻ '...' không đáng xem vì ..., viết lại thành: ...".
- goc_nhin (CHỐNG NỘI DUNG "INAUTHENTIC", Trọng chốt 26/11): video phải có góc nhìn RIÊNG của kênh, không chỉ đọc lại bài X.
  Cần ít nhất: 1 nhận định riêng, 1 số liệu so sánh hoặc bối cảnh thêm ngoài bài gốc (có nguồn), và kết luận "vậy retail nên làm gì".
  Hook, cấu trúc, câu chuyển phần không được rập khuôn y hệt video trước. Chỉ diễn giải lại bài gốc thì goc_nhin tối đa 5.
- series (Trọng chốt 26/11): kịch bản ghi rõ thuộc series nào (dòng "Series:" trong nháp hoặc trường "video_series"), mạch nội dung khớp series đó;
  không ghi series thì series tối đa 6.

LƯU Ý: câu mở "Chào mừng mọi người đã quay trở lại với Smart Penguin Insights" là BẮT BUỘC theo Trọng (kèm logo kênh), không trừ điểm vì câu này; chỉ trừ nếu phần mở đầu dài quá 3 câu.

QUY TẮC TỪ NGỮ CỦA TRỌNG (vi phạm thì quy_tac tối đa 5):
- Không dùng dấu gạch ngang dài (em dash, en dash).
- Nói insider (không "người trong cuộc"), retail (không "nhỏ lẻ"), unlock (không "mở khoá"),
  revenue hoặc doanh thu (không "lợi nhuận").
- Thuật ngữ giữ tiếng Anh (buyback, tokenomics, holder, narrative...). Viết tắt phổ thông (FDV, DCA, TVL, VC, ETF, ATH, TGE,
  DEX, CEX, KOL...) dùng nguyên, KHÔNG giải thích. Chỉ viết tắt dài hoặc ít gặp mới kèm giải thích ngắn.
- An toàn niche crypto (Trọng chốt 26/11): không dùng từ mồi scam như "x100 chắc chắn", "giveaway", "gửi coin nhận lại",
  "airdrop miễn phí", "lãi đảm bảo", "cam kết lợi nhuận"; phải có câu "không phải lời khuyên đầu tư".

LUẬT GIÁ TRỊ (Trọng chốt 27/11, áp dụng cho MỌI câu lời đọc, MỌI thẻ hình, ảnh, chữ trên màn hình, kể cả câu mở và câu kết):
từng câu, từng hình có xứng với thời gian người xem bỏ ra không? Mỗi câu phải mang lại 1 điều MỚI: thông tin mới, con số mới,
bối cảnh, nguyên nhân, hệ quả, hoặc việc người xem làm được. KHÔNG ĐÁNG (phải đập đi viết lại, không được giữ):
nhắc lại con số hay ý đã nói (vd đã nói "gần 5 tỷ" thì không nói lại "4 tỷ 940 triệu"); câu đệm, câu chuyển rỗng, câu chỉ để kéo dài;
câu hỏi tu từ không được trả lời; thẻ hình chỉ nhắc lại chữ của phụ đề hoặc tiêu đề mà không thêm số liệu hay hình mới;
ảnh minh hoạ chung chung không liên quan nội dung.
CÁCH LÀM ĐÚNG (gỡ xung đột với luật "chữ trên hình khớp lời đọc"): mỗi câu lời đọc mang 1 con số hoặc 1 so sánh, và thẻ hình VẼ chính con số đó (số to, so sánh 2 bên, biểu đồ, logo), không chép lại câu chữ. Câu không có gì để vẽ thì viết lại câu cho có số, hoặc bỏ câu.

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


# Trọng 22/11: video ngắn (short-first, kịch bản có "format": "short") chấm theo tiêu chí RIÊNG,
# không trừ điểm vì "ngắn hơn 4 phút", không bắt có 2 short, không bắt mục lục hay đếm phần như video dài.
RUBRIC_SHORT = """Bạn là biên tập viên video ngắn 9:16 (YouTube Shorts, TikTok, Reels) tiếng Việt, khó tính, chấm kịch bản cho kênh
"Smart Penguin Insights". Đây là kịch bản SHORT-FIRST: sản phẩm chính là video ngắn dưới 60 giây (phần trong "shorts",
đọc: short_hooks + narration của phần đó + short_cta). Video dài 16:9 đi kèm chỉ là bản phụ: KHÔNG chấm và KHÔNG trừ điểm
vì thời lượng, số phần, mục lục hay số lượng short của nó. Giọng máy khoảng 210 từ/phút, đoạn "edu" đọc chậm 5%.

Chấm THẲNG TAY từng tiêu chí trên thang 10 (số thập phân được):
- hook_1s: câu đầu (short_hooks) gây tò mò trong 1 đến 2 giây, có con số hoặc nghịch lý, dưới 15 từ.
  Trọng 27/11: câu đầu CẤM mở bằng tên tác giả, phải là HIGHLIGHT đắt nhất (con số sốc, nghịch lý, kết luận bất ngờ) tạo tò mò giữ chân; mở bằng tên tác giả hay @handle thì hook_1s tối đa 4
- mot_y: cả short xoay quanh MỘT ý chính, không lan man; người xem nhận được "câu trả lời" trước giây 40
- giu_chan: không có đoạn quá 5 giây không có thông tin mới; câu ngắn, nhịp nhanh, có twist hoặc "nhưng" giữa video
- do_dai: tổng hook + lời đọc + CTA trong khoảng 30 đến 59 giây (tính khoảng 3,5 từ/giây); quá 59 giây là lỗi nặng
- gia_tri: có ví dụ hoặc con số cụ thể và một việc người xem làm được ngay
- de_hieu: người mới hiểu ngay khi nghe 1 lần; thuật ngữ lạ được giải thích nửa câu
- chinh_xac: số liệu khớp nguồn, không bịa, không hô hào mua bán Trọng 27/11: số CHƯA thấy trong nguồn được đưa KHÔNG tự động là sai; ghi vào fixes dạng "cần kiểm chứng: <số>, tra nguồn" thay vì đòi xoá, chỉ đòi bỏ khi biết chắc số sai. ĐÚNG SỰ THẬT quan trọng hơn ĐÚNG NGUỒN: số đúng, chứng minh được ở bất kỳ nguồn uy tín nào là hợp lệ, không trừ điểm vì "không có trong nguồn được đưa". Dữ liệu lịch sử phổ biến (đáy, đỉnh các chu kỳ trước, ATH, sự kiện lớn như FTX, Luna, halving) là kiến thức chung của ngành: giữ, không đòi nguồn trong bài, chỉ bỏ khi biết chắc là sai
- quy_tac: đúng quy tắc từ ngữ của Trọng (xem bên dưới)
- ket: câu kết gọn, có lời mời theo dõi hoặc câu hỏi để bình luận; câu cuối nối được về câu mở để video lặp mượt (tăng loop)
- hinh_anh: hình (beats) đổi khoảng 3 đến 6 giây một lần, chữ trên hình rất ngắn, đọc được trên điện thoại
- giao_duc (BỘ LỌC GIÁO DỤC): tên riêng lạ giải thích 1 câu lần đầu; so sánh có số của CẢ HAI bên; sau kiến thức khó có ví dụ cụ thể.
  Thiếu một trong ba điều này thì giao_duc tối đa 6.
- dang_xem (LUẬT GIÁ TRỊ, Trọng chốt 27/11): soát TỪNG câu lời đọc và TỪNG thẻ hình theo LUẬT GIÁ TRỊ bên dưới.
  Có 1 câu hoặc 1 thẻ không đáng thì dang_xem tối đa 6, có từ 2 chỗ trở lên thì tối đa 4. Mỗi chỗ không đáng phải ghi vào fixes
  dạng "Câu/thẻ '...' không đáng xem vì ..., viết lại thành: ...".
- goc_nhin (CHỐNG NỘI DUNG "INAUTHENTIC", Trọng chốt 26/11): có nhận định riêng hoặc "vậy retail nên làm gì", không chỉ đọc lại tin/bài X;
  câu mở và cấu trúc không rập khuôn y hệt short trước. Chỉ đọc lại nguồn thì goc_nhin tối đa 5.

QUY TẮC TỪ NGỮ CỦA TRỌNG (vi phạm thì quy_tac tối đa 5):
- Không dùng dấu gạch ngang dài (em dash, en dash).
- Nói insider (không "người trong cuộc"), retail (không "nhỏ lẻ"), unlock (không "mở khoá"),
  revenue hoặc doanh thu (không "lợi nhuận") với dự án crypto.
- Thuật ngữ giữ tiếng Anh. Viết tắt phổ thông (FDV, DCA, TVL, VC, ETF, ATH...) dùng nguyên, KHÔNG giải thích.
- An toàn niche crypto (Trọng chốt 26/11): không dùng từ mồi scam như "x100 chắc chắn", "giveaway", "gửi coin nhận lại",
  "airdrop miễn phí", "lãi đảm bảo", "cam kết lợi nhuận"; phải có câu "không phải lời khuyên đầu tư".

LUẬT GIÁ TRỊ (Trọng chốt 27/11, áp dụng cho MỌI câu lời đọc, MỌI thẻ hình, ảnh, chữ trên màn hình, kể cả câu mở và câu kết):
từng câu, từng hình có xứng với thời gian người xem bỏ ra không? Mỗi câu phải mang lại 1 điều MỚI: thông tin mới, con số mới,
bối cảnh, nguyên nhân, hệ quả, hoặc việc người xem làm được. KHÔNG ĐÁNG (phải đập đi viết lại, không được giữ):
nhắc lại con số hay ý đã nói (vd đã nói "gần 5 tỷ" thì không nói lại "4 tỷ 940 triệu"); câu đệm, câu chuyển rỗng, câu chỉ để kéo dài;
câu hỏi tu từ không được trả lời; thẻ hình chỉ nhắc lại chữ của phụ đề hoặc tiêu đề mà không thêm số liệu hay hình mới;
ảnh minh hoạ chung chung không liên quan nội dung.
CÁCH LÀM ĐÚNG (gỡ xung đột với luật "chữ trên hình khớp lời đọc"): mỗi câu lời đọc mang 1 con số hoặc 1 so sánh, và thẻ hình VẼ chính con số đó (số to, so sánh 2 bên, biểu đồ, logo), không chép lại câu chữ. Câu không có gì để vẽ thì viết lại câu cho có số, hoặc bỏ câu.

BÀI HỌC TỪ CÁC VIDEO TRƯỚC:
{lessons}

NGUỒN SỐ LIỆU:
{source}

KỊCH BẢN:
{draft}

Điểm tổng = trung bình các tiêu chí. Trả về DUY NHẤT JSON:
{{"score": số, "scores": {{"hook_1s": số, ...}},
  "fixes": ["việc sửa cụ thể, chỉ rõ câu nào, sửa thành gì"],
  "rewrites": {{"short_hook": "câu mở viết lại nếu hook_1s dưới 8, không thì để trống"}},
  "nhan_xet": "2 câu tóm tắt"}}"""


def is_short(draft: str) -> bool:
    """Kịch bản JSON có "format": "short" (hoặc nháp .md ghi dòng "Dạng: short") thì chấm theo tiêu chí video ngắn."""
    try:
        d = json.loads(draft)
        if isinstance(d, dict):
            return str(d.get("format", "")).lower() == "short"
    except Exception:
        pass
    return bool(re.search(r"^\W*Dạng\W*:?\W*short\b", draft, re.I | re.M))


def run_claude(prompt: str, tools: str = "", turns: int = 6, timeout: int = 900) -> dict:
    """tools: công cụ cho phép (vd "WebSearch,WebFetch" để tra và kiểm chứng số liệu trên mạng)."""
    tok = re.sub(r"\s+", "", os.getenv("CLAUDE_CODE_OAUTH_TOKEN", ""))
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    if tok:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
    model = os.getenv("SCRIPT_REVIEW_MODEL", "sonnet")
    cmd = ["claude", "-p", prompt + "\n\nChỉ in ra JSON hợp lệ, không thêm chữ nào khác.",
           "--max-turns", str(turns), "--model", model, "--output-format", "text"]
    if tools:
        cmd += ["--allowedTools", tools]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout)
    m = re.search(r"\{.*\}", r.stdout, re.S)
    if not m:
        raise RuntimeError(f"Claude không trả JSON: {(r.stdout or r.stderr)[:300]}")
    return json.loads(m.group(0))


def review(draft: str, source: str = "", lessons: str = "", fmt: str = "") -> dict:
    short = fmt == "short" or (not fmt and is_short(draft))
    rv = run_claude((RUBRIC_SHORT if short else RUBRIC).format(draft=draft, source=source or "(không có)", lessons=lessons or "(chưa có)"))
    sc = rv.get("scores") or {}
    if sc and not rv.get("score"):
        rv["score"] = round(sum(float(v) for v in sc.values()) / len(sc), 1)
    rv["pass"] = float(rv.get("score") or 0) >= PASS
    try:   # Trọng 27/11: còn câu hoặc thẻ không đáng xem thì không được chốt, phải viết lại
        if float(sc.get("dang_xem", 10)) < VALUE_MIN:
            rv["pass"] = False
    except (TypeError, ValueError):
        pass
    rv["format"] = "short" if short else "long"
    return rv


if __name__ == "__main__":
    draft = Path(sys.argv[1]).read_text(encoding="utf-8")
    source = Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) > 2 and Path(sys.argv[2]).exists() else ""
    lessons = Path("lessons.md").read_text(encoding="utf-8") if Path("lessons.md").exists() else ""
    rv = review(draft, source, lessons)
    print("=====REVIEW=====")
    print(json.dumps(rv, ensure_ascii=False, indent=1))
    print("=====END=====")
