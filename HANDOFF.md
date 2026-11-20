# HANDOFF: Smart Penguin Insights + Trạm Podcast Crypto (bàn giao cho đoạn chat mới)

Chủ dự án: Trọng (@Trong0322), KOL crypto Việt Nam, KHÔNG biết code. Luôn trả lời tiếng Việt dễ hiểu,
giải thích thuật ngữ ngay bên cạnh. Repo: github.com/LHTrong0322/trampodcast (nhánh main = code,
nhánh podcast-data = dữ liệu + web Cloudflare Pages "trampodcast").

## 1. Hai sản phẩm
1. **Trạm Podcast Crypto** (podcast.py, video.py, workflow podcast.yml + video-weekly.yml): tin crypto hằng ngày
   ~5:00 VN, giọng Gemini "Fola", MC Mai Hương; video tổng hợp tuần (Chủ nhật). Đang chạy ổn, ít đụng tới.
2. **Smart Penguin Insights** (kênh YouTube/TikTok chia sẻ insight, KHÔNG phải đọc tin): Trọng gửi link bài X vào
   bot Telegram → bot viết kịch bản → đọc giọng → dựng video bằng **Remotion** (kiểu "hình dữ liệu thật") →
   GitHub Release + gửi Telegram (video dài 16:9, 2-3 short 9:16, ảnh bìa, gói SEO, bot review).

## 2. File chính của Insight
- insight.py: hộp thư Telegram (inbox) + `produce()` = quy trình chính (có thanh tiến độ % trên Telegram).
- insight_lab.py: `prepare()` đọc bài X đầy đủ (fxtwitter), viết kịch bản (PROMPT), dữ liệu thật (CoinGecko,
  alternative.me), lọc ảnh bằng AI, màu brand dự án, đọc giọng TỪNG ĐOẠN (không gộp, tránh cắt giữa câu).
- insight_render.py: dựng Remotion: timeline, phụ đề EN (dịch theo câu), số liệu chỉ lấy số CÓ THẬT trong bài
  (`real_number`), câu trích X nguyên văn đã kiểm (`verified_quotes`), thuật ngữ, short.
- insight_publish.py: ảnh bìa (Remotion "Thumb"), SEO (YouTube + TikTok), Release, Telegram, `Progress`,
  BOT REVIEW (Claude qua CLAUDE_CODE_OAUTH_TOKEN bằng `claude -p`, dự phòng Gemini), lưu insight/reviews.json.
- remotion/src: Insight.tsx (cảnh), InsightShort.tsx, Thumb.tsx, data.tsx (Fear&Greed, heatmap, biểu đồ có
  đỉnh/đáy, checklist…), ui.tsx (font, THEMES light/blue/slate/dark, Captions, CountUp, nodash JS `clean`).
- Font: Space Grotesk (tiêu đề), Unbounded (số lớn), Lexend (phụ đề) trong fonts/web + remotion/src/fonts.json.
- podcast.py `nodash()`: hàm lọc gạch ngang dài dùng chung.
- sources.yaml mục `insight:`: brand, theme (light), voice_primary gemini:Riko, voice_fallback vieneu:Hải Đăng,
  voice_speed auto + target_wpm 228, subtitle_lang en, shorts_max_seconds 45, end_screen_seconds 12…

## 3. Workflow GitHub
- insight.yml: chạy tay với input force=true, links=<link X>, voice=(vd vieneu:Hải Đăng | gemini:Riko),
  themes=(vd light hoặc light,blue,slate). Có bước tự báo lỗi vào Telegram. Mất ~60-90 phút.
- check-claude.yml: kiểm tra key Claude. voice-samples.yml: gửi mẫu giọng vào Telegram.
- Session Claude Code KHÔNG tạo/xoá Release được, chỉ đọc; dispatch workflow bằng
  `gh api -X POST repos/LHTrong0322/trampodcast/actions/workflows/insight.yml/dispatches -f ref=main -f 'inputs[...]=...'`.

## 4. Secrets
GEMINI_API_KEY (podcast), INSIGHT_GEMINI_API_KEY (Insight, project mới: text dùng gemini-3-flash-preview /
gemini-3.8-flash / gemini-3.5-flash-lite; 2.5 không dùng được), TTS chỉ gemini-3.8-flash-tts, ~10 lượt/ngày/project,
reset 15:00 VN. 1 video ≈ 8 lượt TTS. CLAUDE_CODE_OAUTH_TOKEN (gói Claude Pro, có thể dính xuống dòng → code đã
tự xoá khoảng trắng). TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PIXABAY_API_KEY, PEXELS_API_KEY.

## 5. Quy tắc BẮT BUỘC của Trọng
- KHÔNG BAO GIỜ có dấu gạch ngang dài (— – ―) ở bất kỳ đâu: video, phụ đề, ảnh bìa, SEO, Telegram.
  (Trọng đã nhắc >10 lần. Cần thêm "bot kiểm tra" chặn trước khi xuất bản.)
- Tiền tệ dạng tiếng Anh trên hình ($6B, $400M); thuật ngữ crypto giữ tiếng Anh; thuật ngữ khác (vd PTSD)
  phải dịch/giải thích tiếng Việt.
- Nền video: TRẮNG (theme light). Màu sạch, không loè loẹt. Có logo + "SMART PENGUIN INSIGHTS" từ giây đầu,
  "Source: @tácgiả", watermark logo X + @Trong0322 (đậm).
- Không dùng ảnh lạc đề; hình phải KHỚP mạch kể. Số liệu phải có thật và nhất quán giữa video dài và short.
- Ảnh bìa hứa GIÁ TRỊ hành động được (vd "Cách lọc coin rác"), không giật tít tiêu cực đã cũ.
- Trả lời "khả thi hay không" trước với ý tưởng MỚI lớn, chờ Trọng confirm. Trọng đăng YouTube/TikTok bằng tay.
- Không dùng nhiều tài khoản Gemini miễn phí để lách quota.

## 6. Việc ĐANG DỞ (Trọng giao lúc 14:23 ngày 20/11/2026), mục tiêu video 9/10
1. Áp dụng toàn bộ góp ý bot review Claude (5,4/10) cho video nền trắng gần nhất (insight-20261120-1115-light):
   hook hiện đủ chữ ngay giây 0 (không hiệu ứng gõ), MỘT con số cho hook; bỏ/rút mục lục còn 2-3s; thêm "vòng lặp
   mở"; mỗi 5-8s đổi cảnh, bớt trích dẫn nối tiếp; stat_compare không vẽ thanh rỗng khi giá trị là chữ; CountUp
   không chạy số với dạng "10/10" (bị hiện 9/10); short: hook gây sốc 1-2s đầu, tiêu đề không bị cắt, phụ đề cao
   hơn vùng nút TikTok; kết bằng 3 tiêu chí hành động + câu hỏi kéo bình luận.
   LƯU Ý: review khuyên phụ đề tiếng Việt, nhưng Trọng đã yêu cầu phụ đề TIẾNG ANH → hỏi lại Trọng.
2. Biểu đồ phải khớp mạch kể: vd "ENA tăng 95% trong 14 ngày" (sự kiện trong quá khứ) nhưng lại vẽ giá 30 ngày
   gần nhất (đang giảm). Sửa: lấy giá theo KHOẢNG THỜI GIAN của sự kiện (ngày đăng bài trừ N ngày, CoinGecko
   market_chart/range), hoặc thay bằng thẻ số liệu nếu không xác định được.
3. Ảnh bìa: hứa giá trị hành động được.
4. Dịch/giải thích thuật ngữ không phải crypto (PTSD…) sang tiếng Việt trong lời đọc và trên hình.
5. Tìm và chặn TẬN GỐC dấu gạch ngang dài còn sót (OCR khung hình bằng tesseract có sẵn; kiểm tra props, SEO,
   Telegram) + build "bot tuân thủ" chạy trên GitHub trước khi xuất bản (quét mọi chữ, có vi phạm thì tự sửa/chặn).
6. Khi lượt Gemini hồi (sau 15:00 VN): dựng lại video hoàn chỉnh bài
   https://x.com/zeroxkyle/status/2106571278929010769 với giọng Gemini (ưu tiên Riko; Trọng từng dùng Ludo cho
   "video 3"), theme light. Hỏi Trọng câu "video 1 và text của video 3" nghĩa là gì nếu chưa rõ.
7. Sau mỗi lần dựng: tải Release, tự xem khung hình, đọc review mới nhất, báo Trọng ngắn gọn.

## 7. Bài học vận hành
- Trọng hay nhắn liên tục khi đang chờ → ứng dụng ngắt lượt trả lời. Đừng chạy lệnh chờ lâu trong lượt trả lời;
  dùng send_later để tự hẹn kiểm tra, và luôn KIỂM TRA LẠI trạng thái sau khi bị ngắt (đã từng mất cả đêm vì
  lệnh "huỷ + chạy lại" bị ngắt giữa chừng).
- Trước khi dispatch: chạy kiểm tra khói (import + thuộc tính module) để tránh lỗi ngớ ngẩn.
- Có thể dựng thử nhanh vài khung hình trên máy bằng `python insight_render.py --lab <thư mục lab> --frames "3,40"`
  (Chrome có sẵn ở /usr/bin/google-chrome; lab mẫu cũ ở nhánh lab-renders).
