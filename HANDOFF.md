# HANDOFF: Smart Penguin Insights + Trạm Podcast Crypto (bàn giao cho đoạn chat mới)

## ✅ TRỌNG CHỐT 01:41 NGÀY 21/11 (MỚI NHẤT, ĐỌC TRƯỚC TIÊN)
- VIDEO CHUẨN MỚI = release insight-20261120-1915 (bài zeroxkyle, giọng gemini:Ludo, nền TRẮNG SẠCH, bố cục + nhịp kiểu 2125).
  Trọng: "video này đã ổn, sau này chất lượng như này trở lên". Không làm video nào kém hơn bản này.
- Code chuẩn đã đưa lên main (21/11): các file video insight (insight*.py, remotion/, .github/workflows/insight.yml,
  scripts/) lấy từ nhánh style-2125. Main cũ trước khi đổi được sao lưu ở nhánh backup-main-20261121.
  File podcast hằng ngày (podcast.py, video.py, tg_send_release.py...) giữ nguyên bản main.
- Bổ sung 21/11: câu chào mở đầu luôn có logo kênh (logo.png) + SMART PENGUIN INSIGHTS + @Trong0322.
- QUY TRÌNH BẮT BUỘC: AI viết kịch bản nháp → gửi Trọng đọc trong chat (hook, tiêu đề, lời đọc từng phần, chữ trên hình,
  ảnh bìa) → Trọng sửa → Trọng nhắn "ok kịch bản" → mới dựng, dựng ĐÚNG lời đọc đã duyệt:
  lưu scripts/<ten>-approved.json (mẫu scripts/TEMPLATE-approved.json, có thumb_text/thumb_stat/thumb_points/hook_screen)
  rồi dispatch insight.yml: force=true, links=<link X>, voice=gemini:Ludo, script=scripts/<ten>-approved.json.
- TỰ HỌC TỪ BOT REVIEW (Trọng 21/11): luôn đọc podcast-data insight/reviews.json trước khi viết kịch bản nháp.
  Code tự nạp script_tips + retention_risk của 3 review gần nhất có tag >= 20261120-1915 (STANDARD_TAG trong insight.py).
  Mục "can_sua" về hình ảnh thì phiên Claude tự đánh giá rồi sửa code, dựng thử khung hình xem tận mắt trước khi đẩy.
  Review của 1915 (6,8/10) còn nêu: short chữ sát mép trên/dưới (safe zone TikTok/Reels), danh sách mở đầu nên hiện
  từng dòng theo lời đọc, biểu đồ giá giảm cần chú thích, ảnh bìa nên phóng to ô số và bớt chữ.
- TỰ HỌC (cập nhật 05:10 21/11): TRƯỚC KHI VIẾT KỊCH BẢN NHÁP, phiên Claude PHẢI đọc file bài học:
  gh api 'repos/LHTrong0322/trampodcast/contents/insight/lessons.md?ref=podcast-data' -H 'Accept: application/vnd.github.raw'
  File gom: bot review (từ bản chuẩn 1915) + số liệu thật hằng tuần. Pipeline tự nạp file này khi AI viết kịch bản.
  Bot review dùng CLAUDE (CLAUDE_CODE_OAUTH_TOKEN, gói Pro, đã kiểm tra chạy OK), Gemini chỉ dự phòng.
  growth-report.yml chạy 19:41 tối Chủ nhật: số liệu YouTube/Facebook thật, Claude phân tích, gửi Telegram, ghi lessons.md.
  Lỗi hình ảnh review 1915 đã sửa 21/11: short trong vùng an toàn TikTok/Reels, danh sách mở đầu hiện từng dòng,
  biểu đồ giá giảm có chú thích trung tính. Ảnh bìa video: Trọng đã duyệt mẫu hiện tại, chưa đổi.
- ĐĂNG LÊN MẠNG XÃ HỘI (21/11): luôn hỏi Trọng xác nhận trước khi đăng thật. Trọng muốn đăng CÔNG KHAI (không private).
  Đăng theo lịch: file kế hoạch scripts/posts/<tag>.json (tiêu đề, mô tả, tags, giờ đăng, bình luận) rồi dispatch
  social-schedule.yml với plan=<file>. YouTube dùng Lên lịch chính thức (publishAt), Facebook Reel video_state=SCHEDULED.
  Bình luận tự đăng mỗi giờ phút 07 khi tới giờ, Trọng tự ghim (API không ghim được). Trạng thái ở <tag>.state.json.
  Đăng ngay chọn lọc: social-post.yml (youtube/facebook = long, short1, short2). Mô tả luôn có Telegram https://t.me/SmartPanda0322
  Kênh YouTube id UC2tX8_Z9beionA0HVu6q4Gw (đã xác minh, ảnh bìa tự gắn được). 3 playlist đã tạo.
  Phụ đề tự động YouTube: Trọng muốn GỠ (đè lên phụ đề trong video). social_schedule.py tự gỡ track asr sau khi đăng;
  gỡ tay: dispatch yt-captions.yml (video=<id>, action=delete_asr). Trọng tắt lồng tiếng tự động trong Studio.
  YouTube handle đang đổi sang @smartpenguininsights cho giống Facebook (Trọng làm tay, API không đổi được).
  Facebook token thiếu pages_manage_engagement nên máy không bình luận được trên Reel (gửi Telegram để dán tay).
  Facebook token thiếu pages_manage_metadata nên không đổi ảnh bìa Trang được (Trọng tải tay).
- TỪ CHUYÊN NGÀNH (Trọng 13:08 21/11): ưu tiên giữ TIẾNG ANH (buyback, unlock, revenue, tokenomics, holder,
  overhang, DCA...), không dịch. Viết tắt PHỔ THÔNG (FDV, DCA, TVL, VC, ETF, ATH, APY, TGE, DEX, CEX, KOL, PMF...)
  dùng nguyên, KHÔNG giải thích, cho pro. CHỈ viết tắt DÀI / ÍT GẶP mới kèm giải thích tiếng Việt ngắn lần đầu.
  Đã thêm vào SYSTEM trong insight.py; áp dụng cả khi viết kịch bản nháp trong chat.
- FACEBOOK KHÔNG GẮN LINK TRONG BÀI (Trọng 13:03 21/11): Facebook bóp tiếp cận bài có link. Caption Reel và mô tả
  video Facebook phải sạch link (social_upload.strip_links làm tự động ở mọi đường đăng). Link YouTube + Telegram chỉ
  đặt ở BÌNH LUẬN đầu. Không bình luận được thì BỎ QUA, không gắn link ở đâu cả.
- TỪ NGỮ (Trọng 21/11): dùng "insider" thay "người trong cuộc", "retail" thay "nhỏ lẻ / nhà đầu tư nhỏ lẻ" trong lời đọc
  và chữ trên hình (đã thêm vào SYSTEM trong insight.py; nhớ áp dụng khi viết kịch bản nháp).
- insight.yml đang TẮT (disabled_manually) để chặn lịch tự dựng 3 tiếng/lần khi chưa duyệt kịch bản.
  Dispatch: bật (PUT .../workflows/insight.yml/enable), dispatch, rồi tắt lại ngay; run đang chạy vẫn chạy tiếp.
- Đăng tự động lên YouTube/TikTok/Facebook: xem docs/social-setup.md (chờ Trọng thêm key vào GitHub Secrets).
- Phiên Claude chat không đặt được hẹn giờ tự kiểm tra (send_later bị chặn vì chưa gắn máy tính), nhắc Trọng nhắn lại.

## (CŨ) TRỌNG CHỐT 18:55 NGÀY 20/11
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

## 🛠 NHÁNH style-2125 ĐÃ SẴN SÀNG (phiên lịch tự động 19:05 20/11), CHƯA DỰNG vì chờ Trọng duyệt kịch bản
- Nhánh `style-2125` = code đúng lúc dựng video 2125 (d7702c0) + chỉ các sửa an toàn: lọc gạch ngang dài (kịch bản, SEO,
  Telegram, chữ trên hình; vạch cạnh "01 INSIGHT" và thanh tiến độ trên cùng đổi thành chấm tròn), chỉ hiện số có thật,
  key dự phòng GEMINI_API_KEY2, model text mới, CHỈ giọng Ludo (hết lượt cả 2 key thì DỪNG, không tự đổi giọng),
  không nạp mẹo từ review hôm nay, báo lỗi Telegram. Cấm ENA/Ethena/95%/14 ngày: trong PROMPT + lọc bằng code
  (insight_lab.scrub_plan, insight_render._guard dừng dựng nếu chữ trên hình còn nhắc, SEO cũng lọc; heatmap bỏ ENA).
- Dựng ĐÚNG kịch bản đã duyệt: chuyển bản Trọng duyệt (scripts/zeroxkyle-draft.md) sang JSON theo mẫu
  `scripts/TEMPLATE-approved.json` (trên nhánh style-2125), commit file JSON vào NHÁNH style-2125, rồi dispatch thêm
  `-f 'inputs[script]=scripts/<tên>.json'` → bỏ qua bước AI viết kịch bản, đọc đúng từng chữ.
- Lệnh dựng (chỉ chạy SAU KHI Trọng nhắn "ok kịch bản"):
  `gh api -X PUT repos/LHTrong0322/trampodcast/actions/workflows/insight.yml/enable` (workflow đang bị tắt lúc 19:02)
  `gh api -X POST repos/LHTrong0322/trampodcast/actions/workflows/insight.yml/dispatches -f ref=style-2125 -f 'inputs[force]=true' -f 'inputs[links]=https://x.com/zeroxkyle/status/2106571278929010769' -f 'inputs[voice]=gemini:Ludo' -f 'inputs[script]=scripts/<tên>.json'`
  Lưu ý: bật lại workflow thì lịch cron "17 */3" của bản main cũng chạy lại (có thể tự dựng kiểu main nếu hộp thư
  Telegram có link chờ trong 19h-23h VN). Muốn an toàn: dispatch xong thì tắt lại (PUT .../disable) khi run đã chạy.
- Kiểu chuẩn video 2125 (đã xem khung hình): nền TỐI xanh tím than, hook số to giữa màn hình, intro thẻ bài X +
  danh sách "5 INSIGHT TRONG VIDEO", mỗi phần: tiêu đề trái + bullets, thẻ dữ liệu phải (Fear&Greed, checklist,
  biểu đồ coin, câu trích), thẻ số nhỏ góc dưới phải, phụ đề 1 dòng đáy màn hình, outro "TÓM LẠI". Dài ~4 phút.

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
