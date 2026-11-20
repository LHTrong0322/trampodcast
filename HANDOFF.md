# HANDOFF: Smart Penguin Insights + Trạm Podcast Crypto (bàn giao cho đoạn chat mới)

## ⚠️ TRỌNG CHỐT 18:55 NGÀY 20/11 (GHI ĐÈ MỌI CHỈ ĐẠO TRƯỚC, ĐỌC TRƯỚC TIÊN)
- Các video dựng hôm nay 20/11 (Riko 16:36, Ludo 17:43, các "vòng sửa theo review") Trọng chê QUÁ TỆ.
  DỪNG hướng "sửa theo review 6,3/10" (vòng sửa 2...). Không dispatch thêm từ main theo hướng đó.
- KIỂU CHUẨN = video Trọng ưng ý: release insight-20261119-2125 (smart-penguin-20261119-2125-16x9.mp4, 4 phút 17 giây),
  run 44543373102, commit d7702c0 (19/11), giọng gemini:Ludo. Giọng đọc, cách trình bày, nhịp độ phải GIỐNG video này.
- Việc: cook lại bài https://x.com/zeroxkyle/status/2106571278929010769 giống hệt kiểu 2125, BỎ HẲN đoạn
  "ENA/Ethena tăng 95% trong 14 ngày" (không lời đọc, không thẻ +95%, không biểu đồ ENA, không hook/short/ảnh bìa).
- Cách làm: nhánh style-2125 (tạo từ d7702c0 + chỉ các bản sửa an toàn: lọc gạch ngang dài, số có thật, key Gemini dự phòng).

Chủ dự án: Trọng (@Trong0322), KOL crypto Việt Nam, KHÔNG biết code. Luôn trả lời tiếng Việt dễ hiểu,
giải thích thuật ngữ ngay bên cạnh. Repo: github.com/LHTrong0322/trampodcast (nhánh main = code,
nhánh podcast-data = dữ liệu + web Cloudflare Pages "trampodcast").

## ⛔ TRỌNG CHỐT 18:58 20/11: DUYỆT KỊCH BẢN TRƯỚC, CHƯA ĐƯỢC DỰNG VIDEO
- Mọi phiên Claude: KHÔNG dispatch insight.yml dựng video bài zeroxkyle cho tới khi Trọng nhắn "ok kịch bản".
- Việc cần làm trước: viết kịch bản (theo kiểu video chuẩn insight-20261119-2125, giọng Ludo, BỎ đoạn ENA tăng 95% trong 14 ngày),
  lưu vào scripts/zeroxkyle-draft.md (lời đọc từng phần, hook, tiêu đề, ý chính trên hình, ảnh bìa), push main, gửi Trọng đọc và sửa.
- Trọng duyệt xong mới dựng, và phải dựng ĐÚNG lời đọc đã duyệt (không để AI viết lại).

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
- sources.yaml mục `insight:`: brand, theme (light), voice_primary gemini:Ludo (MẶC ĐỊNH từ 20/11, Trọng chốt; Riko bị chê dở), voice_fallback vieneu:Hải Đăng,
  voice_speed auto + target_wpm 228, subtitle_lang vi, shorts_max_seconds 45, end_screen_seconds 12…

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
- KHÔNG BAO GIỜ có dấu gạch ngang dài (em dash, en dash) ở bất kỳ đâu: video, phụ đề, ảnh bìa, SEO, Telegram.
  (Trọng đã nhắc >10 lần. Đã có bot tuân thủ compliance.py chặn trước khi xuất bản.)
- Tiền tệ dạng tiếng Anh trên hình ($6B, $400M); thuật ngữ crypto giữ tiếng Anh; thuật ngữ khác (vd PTSD)
  phải dịch/giải thích tiếng Việt.
- Nền video: TRẮNG (theme light). Màu sạch, không loè loẹt. Có logo + "SMART PENGUIN INSIGHTS" từ giây đầu,
  "Source: @tácgiả", watermark logo X + @Trong0322 (đậm).
- Không dùng ảnh lạc đề; hình phải KHỚP mạch kể. Số liệu phải có thật và nhất quán giữa video dài và short.
- Ảnh bìa hứa GIÁ TRỊ hành động được (vd "Cách lọc coin rác"), không giật tít tiêu cực đã cũ.
- Trả lời "khả thi hay không" trước với ý tưởng MỚI lớn, chờ Trọng confirm. Trọng đăng YouTube/TikTok bằng tay.
- Không dùng nhiều tài khoản Gemini miễn phí để lách quota.

## 6. Việc ĐANG DỞ (Trọng giao lúc 14:23 ngày 20/11/2026), mục tiêu video 9/10
Quyết định Trọng đã chốt (20/11): phụ đề TIẾNG VIỆT theo câu đầy đủ (subtitle_lang: vi, hàm vi_subs);
"video 1" = bản nền trắng insight-20261120-1115-light (lấy kiểu nền), "video 3" = bản slate (lấy cách viết câu chữ rõ ý);
giọng gemini:Ludo (dự phòng vieneu:Hải Đăng), theme light.
1. ✅ (20/11 16:20) Áp dụng góp ý bot review 5,4/10: hook hiện đủ chữ giây 0, 1 con số (phải nằm trong câu hook,
   hàm hook_stat); intro bỏ mục lục, có open_loop; "nhịp hình" đổi ở cuối câu mỗi 5-8s (BeatStage: data, số lớn,
   ảnh Ken Burns, thuật ngữ, logo, tối đa 1 trích X); stat_compare chữ → thẻ chữ (text_cards); CountUp tĩnh với
   "10/10"; short: hook 1,8s đầu, tiêu đề fitSize, phụ đề đáy 440px tránh cột phải 150px; outro actions + question.
2. ✅ Biểu đồ khớp mạch kể: insight_lab.event_charts (period_days, end_days_before_post, claim_pct; CoinGecko
   market_chart/range tính từ ngày đăng bài; lệch lời đọc thì bỏ biểu đồ). Bỏ việc tự ép biểu đồ 30 ngày cho dự án.
3. ✅ Ảnh bìa: thumb_text hứa giá trị, chặn chữ tiêu cực (BAD_THUMB), checklist thumb_points bên phải, cùng số với hook.
4. ✅ Thuật ngữ không thuộc crypto: prompt + lưới an toàn insight_lab.vi_terms (PTSD → sang chấn tâm lý...).
5. ✅ compliance.py (bot tuân thủ) chạy trong publish() trước Release/Telegram: quét props/SEO/notes, OCR khung hình;
   gạch ngang trên hình → Release NHÁP + báo Telegram. Mọi tin Telegram qua podcast._tg_safe_post (nodash).
   Đã quét sạch gạch ngang dài trong mã nguồn. Tiến độ trên video đổi thành chấm tròn (vạch ngang bị OCR nhầm).
6. ✅ Run 44711829987 (giọng Riko, 16:36) → Release insight-20261120-1636-light, review 6,3/10 (trước 5,4), bot tuân thủ đạt.
   Vòng sửa 2 (commit "Vòng sửa 2 theo review 6,3/10", đẩy lúc ~17:50): hook teaser 3 tiêu chí, cảnh số liệu toàn màn hình,
   phần chẵn đảo bố cục, phụ đề nền xanh than chữ trắng 50px, short ẩn phụ đề lúc hook, không lặp số hook, thử lại
   CoinGecko range (lần trước báo "không có giá" ENA 20/09→04/10), lưu lab zip vào Release + input lab_tag để dựng lại
   không tốn TTS. Một phiên khác (đang nói chuyện với Trọng) đã chạy run 44721587962 (commit e416259, giọng Ludo,
   CHƯA có vòng sửa 2). Việc tiếp: đọc review run đó; nếu < 9 thì dispatch lại với code mới (giọng Ludo, theme light).
7. Sau mỗi lần dựng: tải Release, tự xem khung hình, đọc review mới nhất, báo Trọng ngắn gọn.

## 7. Bài học vận hành
- Trọng hay nhắn liên tục khi đang chờ → ứng dụng ngắt lượt trả lời. Đừng chạy lệnh chờ lâu trong lượt trả lời;
  dùng send_later để tự hẹn kiểm tra, và luôn KIỂM TRA LẠI trạng thái sau khi bị ngắt (đã từng mất cả đêm vì
  lệnh "huỷ + chạy lại" bị ngắt giữa chừng).
- Trước khi dispatch: chạy kiểm tra khói (import + thuộc tính module) để tránh lỗi ngớ ngẩn.
- Có thể dựng thử nhanh vài khung hình trên máy bằng `python insight_render.py --lab <thư mục lab> --frames "3,40"`
  (Chrome có sẵn ở /usr/bin/google-chrome; lab mẫu cũ ở nhánh lab-renders).
- Session Claude: `gh auth status` báo token sai nhưng `gh api` REST vẫn chạy. CoinGecko bị chặn từ máy session
  (chỉ test được trên GitHub). Dựng thử khung hình nhanh: harness gọi insight_render.render với run_remotion bị thay
  bằng bản chỉ xuất ảnh (ONLY_FRAMES) cho cả video dài và short.

## 8. Cấu hình xuất bản theo nền tảng (platform_export.py, thêm 20/11/2026)
Sau khi Remotion dựng xong, `insight_publish.publish()` gọi `platform_export.prepare()` TRƯỚC khi tạo Release:
mã hoá lại tại chỗ video dài + short, chuẩn hoá âm lượng, chỉnh ảnh bìa, tạo ảnh bìa dọc, rồi ffprobe kiểm tra.
Sai thông số → `SpecError` (strict: true) → workflow fail → Telegram báo lỗi. insight.yml có bước `selftest` trước khi
cook (hỏng thì dừng sớm). Thông số ở sources.yaml `insight.publish`, vùng an toàn ở `insight.safe_zones`.
Lệnh tay: `python platform_export.py check|fix <file...>`.

| Hạng mục | Video dài YouTube | Short (1 file cho Shorts/TikTok/Reels) |
|---|---|---|
| Kích thước | 2560x1440 (dựng 1080p rồi nâng bằng lanczos; `LONG_RENDER_SCALE=1.3333` để dựng thẳng 1440p) | 1080x1920 |
| fps / GOP | 30 / GOP đóng 15 khung | 30 / GOP đóng 15 khung |
| Codec hình | H.264 High, yuv420p, BT.709, CRF 16, trần 24 Mbps | H.264 High, yuv420p, BT.709, CRF 17, trần 12 Mbps |
| Âm thanh | AAC 384k, 48 kHz stereo, -14 LUFS, đỉnh -1 dBTP | như video dài |
| File | moov đầu file (faststart) | như video dài; nên 30-45s, cảnh báo > 60s, lỗi > 180s |
| Ảnh bìa | 1280x720, dưới 2MB (PNG quá nặng → JPG) | cover-9x16-*.jpg 1080x1920 (khung giây 1,2) |

Vùng an toàn 1080x1920 (px từ mép, trên/dưới/trái/phải): TikTok 240/660/120/120, Reels 269/672/65/65,
Shorts giữ nội dung trong khung 4:5 giữa (285/285); cột nút bên phải ~180px. Vùng chung: x 120-900, y 285-1248.
Đo thực tế: video dài 230s nâng 1440p mất 4,5 phút trên máy 2 nhân (GitHub 4 nhân ~2,5 phút), file ~170MB.
Nguồn: support.google.com/youtube/answer/1722171 (mã hoá + bitrate: 1440p30 16 Mbps, 1080p30 8 Mbps),
/answer/15424877 (Shorts tối đa 3 phút; > 1 phút có claim bản quyền có thể bị chặn), /answer/72431 (ảnh bìa),
postfa.st/sizes/tiktok/video, manypixels.co (vùng an toàn TikTok), postfa.st/sizes/facebook/reels (Meta 14%/35%/6%),
postfa.st/sizes/youtube/shorts.
