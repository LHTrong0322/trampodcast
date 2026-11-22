# HANDOFF: Smart Penguin Insights + Trạm Podcast Crypto (bàn giao cho đoạn chat mới)






## BỘ LỌC GIÁO DỤC (TRỌNG CHỐT 23:22 NGÀY 21/11)
- Nội dung video phải mang tính giáo dục nhiều hơn. Tên riêng lạ (vd DWF Labs, Assistance Fund) giải thích 1 câu lần đầu.
- So sánh 2 dự án phải có con số của CẢ HAI (vd Hyperliquid dùng khoảng 97 đến 99% phí để buyback HYPE, Aave 50 triệu đô một năm, khoảng 1/3 revenue).
- Sau mỗi kiến thức phức tạp hoặc insight: luôn có ví dụ cụ thể (số thật, coin thật, hoặc "cứ 100 đô phí thì...").
- Đã đưa vào: lời dặn AI viết kịch bản (insight.py), tiêu chí "giao_duc" của vòng 1 chấm kịch bản (script_review.py).
- Tốc độ giọng KOL hiện tại (khoảng 226 tiếng/phút): Trọng xem lại thấy bình thường, GIỮ NGUYÊN.

## NHỊP HÌNH KHỚP LỜI ĐỌC (TRỌNG CHỐT 19:15 NGÀY 21/11: "ảnh và nội dung chẳng liên quan, sáng tạo đi")
- KHÔNG gắn hình dữ liệu chung chung (Fear & Greed, heatmap) nếu lời đọc không nói tới nó.
- Mỗi phần trong kịch bản đã duyệt có "beats": danh sách nhịp hình, mỗi nhịp có "at" = cụm từ NGUYÊN VĂN trong lời đọc,
  hình bật lên đúng lúc giọng đọc nói cụm đó (insight_render.beats_for, remotion/src/beats.tsx), khoảng 5 đến 8 giây đổi một kiểu.
  Kiểu: question (câu hỏi lớn), statement (câu chốt), versus (2 coin + logo + số), bignum (số lớn + logo), dots (13/15),
  flow (các bước sáng dần; BẮT BUỘC ghi "step_at" = cụm từ nguyên văn cho từng bước để bước sáng đúng lúc đọc), logos (hàng logo), chart (giá coin thật, chỉ dùng khi xu hướng khớp lời).
  Logo coin: ghi ticker vào "logo" (vd "AAVE"), máy tự tải từ CoinGecko. "hook_beats" cho phần mở màn.
- Mẫu: scripts/kaffchad-approved.json. Viết nháp phải kèm cột "Hình" theo từng câu.
- "own_source": true = hình ghi nguồn @Trong0322 thay tác giả bài gốc (khi Trọng trình bày như quan điểm của mình).

## CHẤM 2 VÒNG (TRỌNG CHỐT 17:44 NGÀY 21/11)
- VÒNG 1, kịch bản: viết nháp xong phải cho Claude chấm (workflow `script-review.yml`, inputs draft + url bài X, file script_review.py).
  Dưới 8 điểm thì sửa đúng các góp ý "fixes" rồi chấm lại. CHỈ khi đạt từ 8 điểm mới gửi Trọng duyệt, kèm điểm từng tiêu chí.
  Chế độ tự viết (AI viết kịch bản trong insight_lab.prepare) cũng tự chấm và viết lại tối đa 2 lần.
- VÒNG 2, video: bot review cũ sau khi dựng (insight_publish.review), điểm lưu ở insight/reviews.json nhánh podcast-data.

## KINH NGHIỆM TỪ VIDEO ZEROXKYLE BẢN GIỌNG KOL (insight-20261121-1615, TRỌNG DUYỆT "ổn rồi" 16:58 NGÀY 21/11)
- Giọng chuẩn: `gemini:Ludo@kol` (mẫu N), giữ nguyên tốc độ, làm đẹp giọng studio. Lời dặn style phải NGẮN (dài là máy đọc to cả lời dặn).
- TÊN DỰ ÁN đọc liền một từ (Trọng chốt 19:13 21/11): AAVE đọc "Aave", không đánh vần. voice_ab.speakable tự đổi chữ in hoa thành dạng đọc liền, trừ danh sách viết tắt SPELL (FDV, TVL, BTC...).
- Từ ngữ BẮT BUỘC (code tự đổi ở insight_lab.fix_terms, áp cả kịch bản đã duyệt): "mở khoá" → unlock, "lợi nhuận" → revenue
  (hoặc doanh thu), "người trong cuộc" → insider, "nhỏ lẻ"/"nhà đầu tư nhỏ lẻ" → retail.
- CHỐNG LẶP: Gemini hay đọc lặp câu mở đầu. Mỗi đoạn được nghe lại bằng Whisper (tts_qa.check), lặp/thiếu/thừa thì đọc lại,
  4 lần vẫn lỗi thì DỪNG, không gửi. Dựng xong chạy video-qa.yml (tag + kịch bản) xác nhận "Không thấy chỗ lặp" TRƯỚC khi báo Trọng.
  Đoạn ngắn (dưới 60 từ) không tách dòng; lời dặn TTS có "đọc đúng 1 lần".
- Câu mở đầu: nói lợi ích cho người xem trước, rồi mới nhắc tên tác giả (vd "Phần lớn altcoin chu kỳ này sẽ về 0...").
- Ảnh bìa: câu hỏi gây tò mò + số bộ lọc ("ALTCOIN NÀO ĐÁNG HOLD? 3 BỘ LỌC") + biểu tượng cảnh báo đỏ.
- Hình (theo review): phụ đề to, tô vàng từ khoá/số, không ngắt cụt; dòng đang nói nổi bật; zoom chậm; giới thiệu kênh khoảng 6 giây.
  Review vẫn 5.8: lần sau cần 3 giây đầu có hình mạnh (biểu đồ/con số chạy), mục lục ngắn hơn, đổi kiểu hình mỗi 15 đến 20 giây.
- AN TOÀN ĐĂNG: biến SOCIAL_AUTOPOST trên GitHub đang = 1. Bấm dựng tay luôn để autopost=false (mặc định), chỉ đăng khi Trọng duyệt.
- Lượt Gemini miễn phí reset 15:00 giờ VN; một lần dựng tốn khoảng 8 đến 12 lượt đọc giọng.

## GIỌNG ĐỌC (TRỌNG CHỌN 14:35 NGÀY 21/11)
- Trọng chọn mẫu N: giọng Ludo "vibe KOL crypto", tự tin, cuốn, giọng Sài Gòn thành thị, KHÔNG làm chậm.
- Dựng video với voice = `gemini:Ludo@kol` (insight_lab.speak: lời dặn STYLE["kol"] trong voice_ludo2.py,
  chuẩn hoá chữ speakable, mỗi câu một dòng, chặn bản dài bất thường, làm đẹp giọng voice_master.CHAIN tempo 1.0).
- Kho key Gemini tự chuyển: INSIGHT_GEMINI_API_KEY, GEMINI_API_KEY, GEMINI_API_KEY2..9, GEMINI_API_KEYS. Lượt reset 15:00 giờ VN.

## ✅ TRỌNG CHỐT 02:22 NGÀY 22/11 (SHORT)
- Short = highlight cắt từ video dài: lấy TRỌN lời đọc 1 phần (không cắt câu), thêm hook đọc trước, dựng lại khung 9:16.
- CUỐI MỌI SHORT có câu đọc + chữ lớn "Xem full video trên kênh Smart Penguin Insights nhé!" (sources.yaml insight.short_cta,
  kịch bản có thể ghi đè bằng khoá short_cta). Khung kết NỀN TRẮNG, chỉ logo + câu mời + @Trong0322, KHÔNG có dòng "Nội dung do AI tổng hợp".
  Code (đường dựng chính thức Remotion): insight_lab.prepare đọc thêm phần "short_cta" 1 lần; insight_render ghép vào cuối mỗi short
  (trừ sẵn vào shorts_max_seconds) và truyền prop cta; remotion/src/InsightShort.tsx vẽ EndCard.
- sources.yaml insight: shorts tối đa 5, shorts_max_seconds 59 (dưới 60s để đăng được YouTube, Facebook, TikTok).

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

## Khung chất lượng video (Trọng 22/11: mọi mục bot review ít nhất 7/10)
- `video_lint.py` soát kịch bản trước khi dựng: cứ tối đa 8 giây lời đọc phải đổi hình, thẻ câu hỏi không đứng trơ, có ít nhất 1 biểu đồ giá (race/chart), lời đọc nói "N thứ" thì hình đủ N ý, outro đúng số câu đã hứa, phần hook hứa riêng phải có `emphasis`, ảnh bìa có `thumb_tag`, tiêu đề short có số hoặc dấu hỏi. Chạy: `python video_lint.py scripts/<ten>-approved.json`. Build tự in lỗi vào log; vòng 1 chấm kịch bản AI bị trừ điểm theo lỗi này.
- Kiểu hình mới: `race` (2-3 coin cùng xuất phát 0%, `days: "ytd"` hoặc số ngày, giá thật CoinGecko), `chart` có `days`. Thẻ statement xen kẽ nền đậm để đỡ đơn điệu.
- Phần nhấn (`"emphasis": "CÂU NGƯỜI TA BỎ QUA"`): nền cam nhạt, màu nhấn cam, nhãn riêng.
- Tiêu đề phần hiện gần như ngay (không còn khung chữ bị cắt dở).
- Short: 1,3 giây đầu chính là ảnh bìa (số liệu + logo), thẻ hình to hơn (960x560), phụ đề nâng lên khỏi vùng giao diện app che.
- Ảnh bìa YouTube: số to hơn khoảng 20%, nhãn phụ `thumb_tag` màu nhấn.

## LỖI ĐÃ BỊ TRỌNG NHẮC, KHÔNG ĐƯỢC TÁI PHẠM (22/11)
1. KHÔNG BAO GIỜ để im lặng trơn (nghe như video mất tiếng). Muốn giữ hình lâu: `"hold": giây` chỉ kéo dài HÌNH. Muốn giọng nghỉ cho người xem thấm: `"music": giây` (2-3 giây) trên beat, giọng nghỉ sau câu đó và NHẠC NỀN DÂNG LÊN (Trọng 22/11 cho phép). Mốc chữ được dời đúng khoảng nghỉ nên hình vẫn khớp lời; video ngắn không chèn nghỉ.
2. Hình đang chạy hiệu ứng không được biến mất giữa chừng: mỗi kiểu hình có thời gian tối thiểu (MIN_BEAT: race 5.5s, chart 4s, versus 3.5s...). Hình phụ không đủ chỗ thì bị bỏ, không cắt hình trước.
3. Thời gian dựng được phép dài hơn, chất lượng và giá trị cho người xem là trên hết. Không vội.
4. Tên dự án đọc liền: tên viết hoa đổi thành 1 từ (voice_ab.speakable), tên máy vẫn đọc vấp thì thêm vào voice_ab.PRON (hiện có Aave đọc "A vê"). Sau mỗi bản dựng, đọc bản nghe lại của video-qa để soát tên dự án.
5. VĨNH VIỄN không dùng thẻ nền màu đậm/gradient, nền phần nhấn cũng không tô màu. Chỉ nền sạch (trắng), nhấn bằng màu chữ và nhãn.
6. Nhắc tới dự án nào thì hiện logo dự án đó (insight_render.mention_logo tự gắn logo cho thẻ chữ/số; insight_lab.NAME_TICKER + ticker viết hoa trong lời đọc để tải logo).
7. Không dùng thẻ "question" (chỉ có chữ câu hỏi, review trừ điểm): thay bằng số liệu, biểu đồ, logo kèm số. video_lint báo lỗi nếu còn.
8. Biểu đồ/so sánh (race, versus, chart) chiếm trọn khung, cột chữ lùi đi: khung hình đổi bố cục, không lúc nào cũng "chữ trái thẻ phải".
9. Sau mỗi bản dựng: đọc reviews.json, mục nào dưới 7 thì sửa khung rồi dựng lại cho tới khi đạt. Bot review nay xem 18 khung kèm giây, lời đang đọc và số lần đổi hình đo bằng máy.

## Nhịp đọc đoạn giáo dục (Trọng 22/11)
- Phần có `"edu": true` (giảng kiến thức/khái niệm quan trọng) đọc chậm hơn 5% (config insight.edu_speed = 0.95). Các phần khác giữ nguyên tốc độ như video 2.
- Danh sách video đã đánh số: scripts/posts/VIDEOS.md (video 1 = Kyle, video 2 = Kaffchad).
- Số giá trong kịch bản dùng ô điền tự động: {YTD:HYPE} (trị tuyệt đối % từ 1/1, làm tròn 5), {YTDS:HYPE} (có dấu), {DATE} (ngày dựng). insight_lab.live_numbers điền bằng giá thật lúc dựng, nên lời đọc, biểu đồ, ảnh bìa, short luôn cùng một bộ số (review 22/11 trừ điểm vì 3 bộ số khác nhau). Biểu đồ ghi rõ "tới dd/mm".

## Video là sản phẩm của Trọng (own_source) (22/11)
- Kịch bản có "own_source": true thì mô tả, caption, bình luận ghim, tiêu đề short trên MỌI mạng xã hội không nhắc tác giả/bài gốc (không handle, không link x.com của người khác, không dòng "Source ý tưởng gốc"). insight_publish.seo_pack tự xoá bằng strip_source. Khi tự viết file kế hoạch đăng (scripts/posts/*.json) cũng phải tuân theo.
- Hashtag: caption không chứa hashtag, danh sách không trùng, tối đa 5 (YouTube 3). Mọi chỗ ghép caption dùng hashtags.with_tags; gói SEO chuẩn hoá bằng insight_publish.clean_tags (Trọng 22/11: caption bị spam hashtag trùng).

## Quy trình 2 lượt (Trọng 22/11, mặc định cho mọi video)
1. Lượt 1 (nháp): dựng bằng giọng miễn phí VieNeu "Hải Đăng" (config insight.draft_voice), KHÔNG tạo Release, KHÔNG gửi Telegram, KHÔNG đăng; bot review chấm bản nháp (insight_publish.review_draft).
2. Bot sửa (insight_improve.improve): xử lý NGHIÊM TÚC TỪNG MỤC "Nên sửa", "Dễ mất người xem", "Mẹo kịch bản", bắt trả lời đủ mọi mục ("Đã sửa: ..." hoặc "Cần Trọng quyết: ..."), thiếu thì hỏi lại. Kịch bản Trọng duyệt: khoá lời đọc, chỉ sửa hình. Kịch bản máy viết: được sửa cả lời đọc. Bản sửa phải qua video_lint không tệ hơn.
3. Lượt 2 (bản chính): dựng bằng giọng chính (Gemini Ludo) từ kịch bản đã sửa, gửi Telegram như cũ + video nháp + danh sách xử lý từng góp ý + bảng so điểm nháp → chính.
Tắt: config insight.two_pass: false hoặc env INSIGHT_TWO_PASS=0. Job timeout 200 phút.

## Sửa sau khi Trọng xem video 3 AI bubble (22/11)
- Mở đầu dựng lại hoàn toàn (IntroScene): màn 1 tên kênh + tiêu đề lớn (tô màu đúng các chữ của thumb_text) + con số gây sốc lớn bên phải; màn 2 tiêu đề thu lên góc, các chương trượt vào thành hàng thẻ số lớn, sáng lần lượt.
- Không còn vòng tròn chữ bị cắt ("45 n", "CapE", "Nvid"): không có logo thì ticker ngắn hiện nhãn đủ chữ, còn lại không vẽ.
- Cổ phiếu (NVDA, AAPL, MSFT...) lấy logo công ty (insight_lab.STOCKS), chỉ số (VIX, S&P...) không tra CoinGecko (bị gắn nhầm logo token tên VIX). Nhắc Nvidia/Amazon/... trong lời đọc là tự có logo.
- Bài cổ phiếu/vĩ mô: "lợi nhuận" = earnings (EPS, P/E), "tỷ lệ rủi ro so với lợi nhuận" = risk/reward; chỉ dự án crypto mới đổi lợi nhuận → revenue (insight_lab.fix_terms_plan).
- Cổ phiếu/chỉ số dùng biểu đồ được (Trọng 22/11): giá lấy từ Yahoo Finance, dự phòng Stooq (insight_lab._stock_series); không lấy được thì bỏ hình đó, không dừng cả bản dựng.
- Short có thẻ cuối "Xem bản đầy đủ" 3 giây (remotion EndCard, social_schedule.with_endcard) và bìa riêng cho từng short ("thumb"/"endcard" trong file kế hoạch đăng). Bìa short có hình dán theo chủ đề (short_covers._icon).
