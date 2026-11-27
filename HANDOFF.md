# HANDOFF: Smart Penguin Insights + Trạm Podcast Crypto (bàn giao cho đoạn chat mới)






## 📈 TĂNG PHÂN PHỐI KÊNH MỚI (TRỌNG CHỐT 15:32 NGÀY 26/11, áp dụng cho MỌI video từ nay)

Xác minh nâng cao YouTube không làm giảm reach, đã xác minh. 8 luật dưới đây (bỏ mục SEO đa ngôn ngữ):
1. Chống nội dung "inauthentic" (YouTube siết từ 7/2025): mỗi video phải có góc nhìn riêng (nhận định, số liệu so sánh hoặc bối cảnh ngoài bài gốc có nguồn, kết luận "vậy retail nên làm gì"), không chỉ đọc lại bài X. Đổi hook, visual, cấu trúc giữa các video. Code: tiêu chí `goc_nhin` trong `script_review.py` (chỉ diễn giải lại thì tối đa 5).
2. Shorts: hook 1 đến 2 giây đầu (số sốc, câu hỏi, cảnh báo), không intro, câu cuối nối về câu mở để lặp mượt. Code: `RUBRIC_SHORT` (hook_1s, ket).
   - TRỌNG CHỐT 27/11 (sau audit vidIQ: short "coin rác" mở "Kyle gọi crypto là..." chỉ 4,5% ở lại xem, short "NVDA +30%" 35%): câu đầu short CẤM mở bằng tên tác giả hay @handle; đoạn đầu short LUÔN là highlight đắt nhất (con số sốc, nghịch lý, kết luận bất ngờ) để tạo tò mò. Áp cho cả tiêu đề short (`short_hooks`) lẫn câu NGHE đầu tiên (cụm `from` của `short_spans`, dựng từ kịch bản duyệt thì short_hooks chỉ là chữ trên hình). Code: `video_lint.short_open_issues` (test `tests/test_short_open.py`), prompt `insight.py` + `insight_lab.py`, bot chấm trừ hook_1s/short tối đa 4.
3. Đăng đều, không spam: khoảng 5 đến 30 Shorts/tháng là vùng hiệu quả, quá 35/tháng hết tác dụng. Tin nóng giảm từ 3 xuống tối đa 1 kịch bản/ngày (`sources.yaml` news_flash.max_per_day; muốn quay lại thì đổi về 3). Lệnh topic của Trọng vẫn bỏ qua giới hạn.
4. Niche rõ + series: mỗi video thuộc 1 series có branding riêng (vd "Unlock tuần này", "Insider đang mua gì", "Macro 60 giây", "Phân tích kỹ thuật"). Nháp ghi dòng "Series:", kịch bản duyệt có trường `video_series`. Code: tiêu chí `series` trong `script_review.py`.
5. Shorts dẫn sang video dài: mọi Short gắn "Video liên quan" (Related video) trỏ về video dài. API không làm được, bot đặt lịch nhắc Trọng làm tay trong Studio (`social_schedule.py`).
6. Cộng đồng: mỗi kịch bản có sẵn 1 câu hỏi bình luận ghim kéo thảo luận; trả lời comment trong 1 đến 2 giờ đầu; đăng poll Community. Code: tiêu chí `ket`.
7. An toàn niche crypto: không từ mồi scam ("x100 chắc chắn", "giveaway", "gửi coin nhận lại", "airdrop miễn phí", "lãi đảm bảo"...), luôn có câu "không phải lời khuyên đầu tư". Mọi video YouTube tự khai nhãn AI (`containsSyntheticMedia: true`, `social_upload.YT_STATUS_BASE`), nhãn này không giảm reach. Code: `compliance.scam_hits` + kiểm tra câu miễn trừ trong gói SEO (cảnh báo).
8. Đọc analytics sau 48 đến 72 giờ: Shorts xem tỷ lệ "Đã xem" và "Đã lướt qua", video dài xem CTR và giữ chân 30 giây đầu. Video nào chạy tốt thì nhân bản format sang chủ đề khác. Báo cáo tuần: `growth_report.py`.

## 🎨 SOÁT TRÌNH BÀY TRƯỚC KHI HOÀN THIỆN (TRỌNG CHỐT 15:05 NGÀY 23/11: "lỗi font, lỗi dựng nhiều, chữ xấu, không thẳng hàng")
- `video_lint.layout_issues`: nhãn so sánh tối đa 26 ký tự, số so sánh tối đa 11, chú thích thẻ số 60, thẻ chữ 56, bước sơ đồ 24, chú thích chấm 48.
  Lỗi trình bày được đưa vào `insight_improve` như góp ý "[Lỗi trình bày]" nên bot tự sửa trước khi dựng bản chính.
- Bot review (REVIEW_PROMPT) có mục SOÁT TRÌNH BÀY BẮT BUỘC: chữ đè, tràn, lỗi font, ngắt dòng giữa cụm, số không thẳng hàng,
  nguồn viết liền, từ mồ côi, chữ lệch lời đọc, biểu đồ biến mất sớm. Có lỗi thì hinh_anh_ro_rang tối đa 6, cửa chặn chất lượng tự sửa thêm vòng.
- Khuôn hình: nguồn số liệu ("Nguồn: ...", hoặc trường "source") hiện chữ nhỏ dòng riêng cuối thẻ; thẻ so sánh 2 bên cùng cỡ nhãn,
  cùng chiều cao khung nhãn nên 2 số luôn thẳng hàng; nhãn dài xuống dòng ở dấu phẩy.
- Biểu đồ cổ phiếu/chỉ số nhiều năm: beat chart thêm "years": 30 (giá tháng Yahoo), tiêu đề ghi "30 năm".
- Kịch bản viết CHỮ SỐ (phụ đề hiện "9" không phải "chín"); giọng đọc tự đổi số sang chữ (vi_num.py); S&P 500 đọc "ét en pi năm trăm".
- 🔒 GIỌNG CHỐT (Trọng 15:56 23/11, sau video index fund v8: "giọng hiện tại đã ổn, áp dụng cho tất cả video về sau"): gemini:Ludo@kol với lời dặn voice_ludo2.STYLE["kol"] (giọng Bắc chuẩn Hà Nội, nghiêm túc, đáng tin). Không đổi lời dặn này. Ô voice khi dispatch để trống; gọi "gemini:Ludo" trơn cũng tự gắn @kol (insight_lab.speak). Lượt nháp vẫn VieNeu Hải Đăng như quy trình 2 lượt.

## ⚡ TIN NÓNG 4 TIẾNG + DỪNG VIDEO TUẦN (TRỌNG CHỐT 00:28 NGÀY 23/11)
- DỪNG video tổng hợp tuần: video-weekly.yml bỏ lịch (chỉ còn bấm tay), podcast.yml bỏ bước "làm sẵn đoạn video của ngày", sources.yaml video.enabled: false.
- Tin nóng (news_flash.py, sources.yaml news_flash): news-flash.yml chạy 03:17, 07:17, 11:17, 15:17, 19:17, 23:17 giờ VN, gom tin cùng nguồn podcast,
  Gemini chấm quan trọng/câu view (cần >= 9), Claude xác nhận lần 2, tối đa 3 kịch bản/ngày. KHÔNG có tin đủ lớn thì thôi, không cố.
- Kịch bản viết bằng insight_lab.prepare (INSIGHT_FORMAT=news, INSIGHT_SCRIPT_ONLY=1): format short, 1 phần, shorts [0], Claude chấm >= 8.
- TRỌNG DUYỆT TRƯỚC KHI DỰNG (Trọng 00:30 23/11): kịch bản gửi Telegram kèm nút ✅ Duyệt / ✏️ Sửa / ❌ Bỏ. Lệnh: /tin, /duyet [mã], /bo [mã],
  /sua [mã] <góp ý>, hoặc reply vào tin nháp ("ok" = duyệt, "bỏ" = bỏ, chữ khác = góp ý viết lại). Menu lệnh tự cài (setMyCommands).
  Lệnh đọc chung hộp thư với insight.inbox (news_flash.on_update được gọi trong inbox), nên link X vẫn nhận như cũ.
  Chờ quá 10 tiếng thì tự bỏ (tin cũ).
- news-flash-gate.yml (15 phút/lần, rất nhẹ): chỉ gọi news-flash.yml mode poll khi có kịch bản chờ VÀ có tin nhắn mới, hoặc có bản đã duyệt;
  đang có podcast/insight/news-flash chạy thì đợi lượt sau (cùng concurrency group "podcast", tránh đè mất lượt podcast).
- Dựng sau khi duyệt: giọng VieNeu "Hải Đăng" (không 2 lượt, không Ludo), short 9:16 theo khung Smart Penguin Insights, CTA cuối
  news_flash.short_cta. insight_publish.publish_news chỉ gửi short + ảnh bìa + caption + bot review, KHÔNG tự đăng. Review lưu insight/news-reviews.json.
- Cập nhật 23/11 tối: lịch gate 15 phút gần như không chạy (GitHub bỏ lượt, có lúc lỗi billing) nên duyệt rất lag. Giờ run nào gửi kịch bản
  (pick, topic, revise, setscript, poll) tự ở lại đọc Telegram tối đa NF_WAIT_MIN=30 phút: duyệt thì dựng ngay trong run đó, góp ý thì viết lại.
  Gate giảm còn mỗi tiếng (dự phòng). Claude chấm tin và viết kịch bản tin nóng trước, Gemini dự phòng.
  Mode: topic (Trọng chỉ định chủ đề, brief trong scripts/flash-briefs/), revise (góp ý dài), setscript (Trọng tự sửa kịch bản, gửi lại chờ duyệt).
- Trạng thái: podcast-data flash/state.json (drafts: waiting, revise, approved, building, built, failed, rejected, expired), kịch bản flash/scripts/<mã>.json.

## KHUNG CHUẨN SHORT, RÚT TỪ VIDEO ĐÃ DUYỆT 2, 3, 4 (TRỌNG 24/11, SAU SHORT NVDA REVIEW 5/10)
- Tiêu đề short (short_title / short_hooks) ≤ 46 ký tự, tối đa 2 dòng, có con số. Video đã duyệt: 25 đến 46. video_lint chặn > 46.
- Đổi hình mỗi 3 đến 5 giây (video_lint: short tối đa 5.5 giây không đổi hình). Mỗi con số trong lời đọc có đúng 1 thẻ hiện cùng lúc.
- Thẻ versus: 2 bên là 2 CON SỐ (không "Đang điều tra" vs "Đang điều tra"), nhãn ngắn ≤ 16 ký tự cùng 1 dòng, thêm "note" nhỏ dưới số
  (vd "+103% so với cùng kỳ") và "sub" 1 câu giải thích. Số to tự co cho không dính chữ VS.
- Thẻ chữ không khẳng định mạnh hơn nguồn ("Chính phủ Mỹ đứng sau Nvidia" bị review trừ điểm, đổi thành trích đúng lời).
- Thẻ "photo" (mới 24/11): ảnh từ Pixabay, Pexels, Wikimedia, Openverse theo từ khoá cảnh/đồ vật. KHÔNG tìm ảnh theo tên người thật
  (insight_lab._PERSON_HINT + video_lint chặn): video không đưa ảnh người thật lấy từ mạng. Mỗi short tin nóng 2 đến 4 ảnh.
- Bố cục InsightShort: thẻ tự dời xuống khi tiêu đề dài (không đè chữ). Dòng nguồn: tin nóng ghi "Nguồn: <báo>" (plan.source_label), video
  của Trọng không ghi "Source: @Trong0322". Phụ đề và thẻ chữ chia dòng cân (text-wrap: balance) nên không còn chữ mồ côi.
- BOT REVIEW XEM TRƯỚC, TRƯỚC KHI DỰNG (preflight.py, Trọng 24/11 "đẩy review lên sớm lúc xong ảnh + kịch bản"): mỗi short chụp sẵn
  khung bìa, tiêu đề, từng thẻ (lúc hiện xong), khung đều mỗi ~3 giây, khung kết, kèm lời đọc đúng giây đó. Claude chấm bằng ĐÚNG tiêu chí
  bot review sau dựng (trình bày, font, chữ đè/tràn/mồ côi, khớp lời, không khẳng định quá lời đọc, versus phải 2 số, nhịp ≤ ~5 giây,
  biểu đồ đúng lúc, 2 giây đầu) và trả lệnh sửa: đổi chữ thẻ, đổi tiêu đề ≤ 46, dời mốc giờ, bỏ thẻ, đổi thành thẻ chữ, thêm thẻ
  chữ/số/ảnh kho (số mới phải có trong lời đọc, ảnh không theo tên người). Áp, chụp lại, chấm lại, tối đa 2 vòng sửa, rồi mới dựng.
  Telegram nhận "🔎 Bot review xem trước" kèm điểm dự kiến trước → sau. Lời đọc không đổi ở bước này. Thiếu token/PREFLIGHT=0 thì bỏ qua.
- TỰ SỬA THEO REVIEW SAU DỰNG (news_flash.build + preflight.plan_fix, Trọng 24/11): dựng xong bot review chấm < 8 thì Claude đọc can_sua,
  viết lại danh sách thẻ hình (mỗi thẻ neo "at" nguyên văn lời đọc, số bignum phải có trong lời đọc, ảnh không theo tên người), dựng lại
  (giọng giữ nguyên), tối đa news_flash.fix_rounds = 2 vòng. Telegram nhận "🔁 Bot tự sửa theo review: điểm a → b → c". Bản sửa có quá ít
  thẻ hợp lệ thì bỏ, giữ bản cũ. GIỌNG TIN NÓNG (Trọng 24/11): mặc định giọng xịn như video đã duyệt, sources.yaml news_flash.voice = gemini:Ludo@kol;
  Hải Đăng là giọng NHÁP: Trọng có lúc muốn xem nháp Hải Đăng trước, bấm nút "🎙 Dựng nháp Hải Đăng trước" hoặc /nhap.
  Gemini hết lượt thì dừng và báo, không tự đổi giọng (luật 20/11). Workflow có input voice để đổi tay. Số ảnh bìa: dấu + màu xanh, dấu − màu đỏ.
- Ảnh người thật (kể cả ảnh chế Trump đăng về Huang 23/11): KHÔNG đưa vào video. Kể sự kiện bằng lời đọc + thẻ chữ.
- LUẬT CỨNG ĐIỂM (Trọng 26/11, sau short ETF 6.0 → 5.6 → 5.4): video ra điểm thấp hơn KHÔNG BAO GIỜ được chấp nhận.
  news_flash.build giữ vòng điểm cao nhất (vòng cuối kém hơn thì dựng lại bản tốt nhất rồi mới gửi); dựng lại 1 tin đã có video
  (state drafts.<mã>.best_score) mà bản mới thấp hơn thì không gửi, báo "⛔" trên Telegram. Env NF_FIX_ROUNDS đổi số vòng tự sửa.
- Short sau review 27/11: header hạ xuống top 270 (trước 230); nhãn dự án (chip) chỉ hiện khi tiêu đề short nói về dự án đó; chữ ghi chú thẻ so sánh to hơn (38).
  Mẹo kịch bản đã áp dụng: mở bằng câu hỏi "vì sao" có con số, có câu nối khi chuyển chủ đề (Bitcoin sang altcoin), kết bằng lựa chọn "bình luận 1 hoặc 2".
- Review 27/11 (Claude, short ETF 6.3): mở bằng CON SỐ rồi mới hỏi "vì sao" (gộp 2 mẹo trái nhau của Gemini và Claude); thẻ đầu và tiêu đề
  cùng 1 con số; câu nhắc altcoin phải đi kèm số; biểu đồ: nguồn 1 dòng riêng ở chân thẻ, "Không phải tín hiệu mua bán" dòng riêng, chữ to hơn; phụ đề ngắt theo dấu câu.
- LUẬT GIÁ TRỊ (Trọng chốt 27/11, LUẬT CỨNG): từng câu, từng thẻ, ảnh, chữ phải xứng với thời gian người xem bỏ ra; câu lặp số/ý đã nói,
  câu đệm, thẻ chỉ nhắc lại phụ đề, ảnh chung chung = KHÔNG ĐÁNG, phải đập đi viết lại. Có ở 4 bước: viết kịch bản (insight_lab.NEWS_PROMPT),
  chấm kịch bản (script_review: tiêu chí dang_xem, dưới 8 thì KHÔNG qua dù điểm tổng cao), review xem trước khi dựng (preflight.PROMPT),
  review sau dựng (insight_publish.REVIEW_PROMPT, còn đoạn không đáng thì tối đa 6). Văn bản luật: script_review.VALUE_RULE. Test: tests/test_value_gate.py.
  Tin gốc mỏng thì phải đào thêm bối cảnh có nguồn (vd ETF 27/11: quý 3 bị xoá sạch, BTC cách giá vốn TB 11%) thay vì nói lại 1 con số.
- CHẤM ĐỐI ĐẦU (Trọng 27/11): dựng lại 1 tin đã có bản chính (state drafts.<mã>.best_tag) thì news_flash.head_to_head tải bản cũ từ release,
  chấm lại CẢ 2 bản bằng luật hiện hành, cùng bot, cùng lượng thông tin, rồi mới so. Mới thấp hơn cũ: không gửi làm bản chính, nhưng vẫn gửi
  video vào Telegram kèm "⛔ KHÔNG ĐẠT, chỉ để xem, KHÔNG đăng" (không tạo release, không đặt lịch).
- PHÁT HIỆN LÀ SỬA NGAY (Trọng 27/11, value_fix.py, test tests/test_value_fix.py):
  A. news_flash.value_gate_script: MỌI kịch bản (kể cả viết tay, đã duyệt) chấm "đáng xem" TRƯỚC khi đọc giọng; dưới 8 thì viết lại câu không đáng.
  B. Sau review (xem trước hoặc sau dựng) còn lỗi "KHÔNG ĐÁNG" thì viết lại lời đọc, đọc giọng lại, dựng lại (tối đa 1 lần mỗi lượt).
  Chốt an toàn: thẻ bám đúng cụm lời đọc, không gạch dài. SỐ MỚI (Trọng 27/11): ĐƯỢC thêm nếu làm video giá trị hơn, bot tra bằng
  WebSearch/WebFetch, mỗi số kèm link + trích dẫn, rồi bot thứ hai (value_fix.verify) mở đúng link xác nhận; số không link hoặc trượt
  kiểm chứng thì cả bản viết lại bị bỏ, giữ bản cũ. Số đã kiểm chứng lưu ở plan["sources"], tin "✂️" liệt kê kèm link.
  Mỗi lần viết lại đều báo Telegram "✂️" kèm câu cũ, câu mới, lý do. Tắt bằng env VALUE_FIX=0.
- ĐÚNG SỰ THẬT > ĐÚNG NGUỒN (Trọng 27/11): đừng chăm chăm đúng nguồn được đưa. Số chứng minh được ở bất kỳ nguồn uy tín nào là hợp lệ;
  bot chấm và bot viết lại KHÔNG được xoá số chỉ vì "không có trong nguồn", phải tra web, chỉ bỏ khi số sai hoặc tra kỹ không ra.
  Dữ liệu lịch sử phổ biến (đáy/đỉnh chu kỳ trước, ATH, FTX, Luna, halving) là kiến thức chung: giữ, tra không ra cũng không được bỏ.
  Kịch bản viết tay nên kèm plan["sources"] (value, claim, source, url, quote) để bot biết số đã có chứng cứ.
- Luật giá trị + khớp lời đọc không còn đá nhau: mỗi câu lời đọc mang 1 con số, thẻ hình VẼ con số đó, không chép câu chữ.
- Bố cục short sau review 27/11 (ETF 5.5): khung kết nền trắng che ngay khung đầu (hết chồng chữ lên thẻ câu hỏi); câu phụ của thẻ chữ/câu hỏi
  tách mỗi câu 1 dòng, không ngắt giữa "Có: 1"; thẻ so sánh 2 bên hiện cùng lúc (hết lệch hàng); thẻ cao 600 (trước 560), phụ đề bottom 430;
  beats_for khớp được cả khi giọng đọc chép số khác ("75 nghìn" thành "75.000"/"bảy mươi lăm"), test tests/test_beat_timing.py.
- Short dọc không chạy đếm số trên thẻ (CountUp): bot review chụp trúng số đếm dở rồi trừ điểm "số lệch". Trước thẻ đầu tiên, thẻ đầu hiện từ giây 0.
- en_money gộp số kép: "4 tỷ 940 triệu đô la" → "$4.94B" (trước ra "4B $940M" trên phụ đề).
- thumb_subject: "penguin" (26/11) = bìa 16:9 không lấy logo dự án làm chủ thể tròn (tin không xoay quanh 1 dự án, vd ETF).
- Bố cục short sau review 26/11 (short ETF 6.0): nguồn tin bỏ khỏi header, chỉ ghi nhỏ trong thẻ số liệu (beat.source hoặc "Nguồn: ..." trong sub,
  tự tách dòng); nhãn dự án (chip) chỉ hiện từ lúc lời đọc nhắc tới; phụ đề nâng lên bottom 470 (trước 390); thẻ chuyển nhanh khoảng 0,15 giây.
  Lời đọc short tin nóng phải MỞ BẰNG đúng câu hook có con số (không chào hỏi), mỗi câu 1 số.
- Ảnh bìa tin nóng: dùng thumb_text + thumb_stat Trọng chọn, dòng dưới "Tin nóng · @Trong0322" (không "Xem bản đầy đủ trên YouTube").
  Không cắt cứng 60 ký tự nữa (từng mất dấu %). Ảnh gửi Telegram dạng JPEG nhẹ (PNG 1MB bị Telegram Desktop kẹt).

## TELEGRAM KHÔNG NHẬN LỆNH DUYỆT (sửa 24/11)
- Nguyên nhân: run gửi kịch bản chỉ chờ trả lời 30 phút; lượt canh dự phòng mỗi tiếng chạy theo lịch hẹn giờ GitHub, mà GitHub bỏ hết lượt từ 10:00 đến 14:00 ngày 24/11.
- Sửa: news-flash.yml cuối run, nếu còn kịch bản chờ (dưới 24 giờ, news_flash.py watch) thì gọi news-flash-gate.yml loop=1.
  Lượt loop đọc Telegram mỗi phút, thấy lệnh mới thì đợi hàng "podcast" TRỐNG HẲN (kể cả lượt đang chờ) rồi mới gọi poll, tối đa khoảng 5 tiếng rồi tự gọi lượt mới.
- Hàng "podcast" (podcast, insight, news-flash, insight-lab, video-weekly, voice-samples) chỉ giữ 1 lượt chờ: gọi thêm khi đang có lượt chờ sẽ HUỶ lượt chờ đó (video Dow 24/11 bị huỷ vì vậy). Trước khi dispatch tay, kiểm tra không có run pending.
- Quay lại cách cũ: git revert commit này.
- RUN MA (27/11): tắt insight.yml (disable) khi run vừa dispatch còn "queued" làm run kẹt queued mãi, không có job, không huỷ được (45136391598, 45298785025, 45872833600). Dispatch xong phải ĐỢI run sang in_progress (hoặc pending) rồi mới disable. Run 45880951145 cũng kẹt queued khi dispatch ngay sau lúc vừa huỷ 1 run pending: huỷ xong đợi run kia completed hẳn rồi mới dispatch. insight.yml không có lịch (chỉ workflow_dispatch).

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
  SHORT LUÔN CÓ BÌNH LUẬN (Trọng 23/11): kế hoạch YouTube short không ghi "comment" thì social_schedule.short_comment tự tạo
  (câu hỏi + link video dài cùng tag), đăng 5 phút sau giờ công khai; social_post đăng short công khai cũng tự bình luận.
  MỌI VIDEO ĐỀU CÓ BÌNH LUẬN KÉO VỀ TELEGRAM (Trọng 26/11): bình luận gắn link YouTube bị ẩn hết, nên mọi bình luận
  trên YouTube (video dài + short), Facebook (video dài + Reel) và TikTok đi qua social_upload.cta_comment: xoá dòng có
  link YouTube, luôn kết bằng 1 câu call to action Telegram https://t.me/SmartPanda0322, cố định 1 câu (Trọng 27/11): "🐧 Cả nhà join group Telegram để nhận nhiều insights sớm hơn nhé 👉 <link>". Kế hoạch không ghi bình luận thì máy tự tạo
  (5 phút sau giờ đăng). TikTok không có API bình luận: tiktok_handoff gửi sẵn bình luận qua Telegram để Trọng dán và ghim;
  đăng TikTok qua vidIQ cũng phải dán bình luận này tay. Link video dài vẫn nằm ở mô tả short YouTube.
  Viết kế hoạch vẫn nên ghi "comment" riêng cho từng short (câu hỏi hợp nội dung + link bản đầy đủ).
  TIKTOK (Trọng 23/11): chưa đăng tự động (app TikTok chưa qua audit thì chỉ đăng riêng tư). Khi đặt lịch một short,
  social_schedule.tiktok_handoff gửi Telegram file short + caption (plan["tiktok"]["caption"], không có thì lấy caption Reel)
  + giờ đăng; Trọng tự bấm đăng/hẹn giờ trong app TikTok. Chạy lại plan cũ thì chỉ gửi phần TikTok còn thiếu (cờ tiktok_sent).
  CẬP NHẬT 23/11 23:56: TikTok đã nối vidIQ (account _000rBMsglcGS3J4706N717ICAW4au_F7cIu). Claude đặt lịch TikTok bằng
  công cụ vidIQ (vidiq_video_upload từ link raw nhánh tiktok-upload, rồi draft + publish): cùng giờ với Reel Facebook,
  caption = caption Reel + dòng "Xem bản đầy đủ trên YouTube: Smart Penguin Insights", KHÔNG link, KHÔNG bình luận,
  công khai, cho bình luận, đồng ý điều khoản nhạc, BẬT nhãn AI. Trọng duyệt sẵn: caption giống Reel là được đăng.
  Gửi tay qua Telegram đã tắt (TIKTOK_TELEGRAM = False).
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
- ĐÃ BỎ (Trọng 23/11, xoá vĩnh viễn): gom link X qua Telegram để tối tự cook video Insight. Bot không nhận link,
  không gửi "Đã nhận link", không còn /list, /cook. inbox() chỉ còn đọc lệnh tin nóng. Link chỉ nhập lúc bấm chạy insight.yml.
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

- Trọng 23/11 ("sao chính còn thua bản nháp?"): CỬA CHẶN CHẤT LƯỢNG. Mọi lượt chấm đều chấm 2 lần lấy trung bình (1 lần lệch ±0,5 đến 1).
  Bản chính phải chấm lại và không được thua bản nháp (tổng thấp hơn, hoặc một mục tụt từ 1 điểm). Thua thì bot sửa thêm 1 vòng
  theo góp ý của chính bản đó, dựng lại, chọn bản điểm cao nhất, báo kết quả ở mục "🚦 CỬA CHẶN" trên Telegram. Code: insight.quality_gate.
- Trọng 23/11: số tăng (+) luôn màu xanh, số giảm (-) màu đỏ (insight_render.sign_tone); mũi tên chỉ hiện khi số có dấu.
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

## VIDEO 100y BTC (23/11)
- Kịch bản Trọng duyệt 01:03 23/11: scripts/100y-btc-approved.json (link https://x.com/100y_eth/status/2124147616028188896).
- Mới: beat "wma" = biểu đồ giá BTC theo tuần + đường 200WMA, 350WMA (dữ liệu thật: Yahoo, dự phòng Stooq, CryptoCompare;
  insight_lab.wma_data, remotion/src/beats.tsx Wma). Không lấy được giá tuần thì bỏ beat, ghi log, không dừng dựng.
- Mới: "short_spans" (cùng thứ tự với "shorts"): mỗi short lấy đúng đoạn tinh tuý {"from": cụm đầu, "to": cụm cuối} trong phần,
  không cố định từ đầu phần (Trọng 23/11: short lấy tinh tuý, không cố định số lượng hay theo từng phần).
- Trọng 24/11 "xong lượt nào gửi lượt đó trước": bản nháp (lượt 1) gửi Telegram NGAY khi xong (video dài + short + lỗi chính + bot sửa gì),
  bản chính lượt 2 cũng gửi ngay nếu phải sửa thêm vòng 3. Code: insight.two_pass_draft, insight.quality_gate.
- Bật/tắt insight.yml khi dispatch tay: CHỜ run chuyển sang in_progress rồi mới tắt lại. Tắt ngay sau dispatch làm run kẹt "queued" mãi (23-24/11 kẹt 2 run).

## Ảnh bìa kiểu "viral sạch" (Trọng chốt 26/11)

Rút từ các thumbnail tài chính viral 12x đến 75x Trọng gửi, giữ phong cách sạch của kênh (nền sáng lưới nhạt, Be Vietnam Pro, thẻ trắng bo góc, lề 64px).
- Luật: 1 con số làm nhân vật chính; chữ ít, viết thường có dấu như câu nói (không IN HOA cả câu); câu hỏi gây tò mò; nhãn vàng nổi; chủ thể tròn lớn (logo dự án, không có thì avatar penguin) thay khuôn mặt; ảnh bìa bổ sung cho tiêu đề, không lặp y nguyên.
- Code: `remotion/src/Thumb.tsx` (5 bố cục: stat, pill, vs, before, question), chọn bố cục ở `insight_publish.thumb_style`, soát ở `video_lint.py`.
- Trường kịch bản: `thumb_stat` (số sốc), `thumb_text` (≤ 24 ký tự), `thumb_tag` (nhãn ≤ 24), `thumb_kicker` (dòng nhỏ ≤ 30), `thumb_points` (≤ 3 chip), `thumb_vs`, `thumb_before` + `thumb_after`, `thumb_style` (tuỳ chọn). Mẫu: `scripts/TEMPLATE-approved.json`.
- Mẫu đã duyệt: Video 3 bố cục stat ("-$6T", "Cú rũ hay sụp đổ?"), Video 4 bố cục before ("$10K" → "$1.6M").
- Ảnh bìa chốt lại sau khi dựng: đặt ở `scripts/posts/thumbs/<mã>.png` (vd `20261123-1718.png`), bot đặt lịch tự dùng thay ảnh trong Release.
- Luật cứng (Trọng 26/11, có test `tests/test_thumb_rules.py`): ảnh bìa YouTube và short nhắc tới dự án nào thì PHẢI có logo dự án đó (`insight_publish.subject_logo`, `short_covers._logo`); chủ đề khớp hình dán (bong bóng vỡ, giảm, tăng, đồng hồ, lửa, cân, kính lúp) thì PHẢI có hình dán (`insight_publish.topic_icon`). Kịch bản chỉ định được: `thumb_logo` (mã dự án), `thumb_icon`, hoặc `thumb_subject: "penguin"` khi tin không xoay quanh 1 dự án.
- Bố cục cũ (classic, hero, sticker, stack, biển cảnh báo) đã bỏ; muốn quay lại thì `git revert` commit e95d0df.
- Ảnh bìa short 9:16 (`ShortThumb.tsx`, Trọng 26/11) cùng phong cách: tiêu đề viết thường có dấu, số trong tiêu đề tô đỏ/xanh theo ngữ cảnh (sau "giảm, mất, bốc hơi" là đỏ, sau "tăng" là xanh), 1 thẻ trắng có con số khổng lồ (key_stat) hoặc 2 thẻ đối đầu (thumb_vs), không có số thì avatar penguin; nhãn vàng "Xem full trên YouTube" (tin nóng: "Tin nóng hôm nay"). Có số thì bỏ danh sách ý cho ít chữ. Giữ vùng an toàn trên 230px, dưới 440px.

## VIDEO CÓ LIÊN QUAN + MÀN HÌNH KẾT THÚC (Trọng 27/11)
Mọi short YouTube PHẢI gắn 'Video có liên quan' (dẫn sang short kế tiếp, short cuối sang video dài, short lẻ sang video dài gần nhất). Mọi video dài gắn màn hình kết thúc mẫu '1 video, 1 đăng ký' (Phù hợp nhất với người xem + Đăng ký). Không có API: làm trong YouTube Studio bằng trình duyệt trong app Claude (đã đăng nhập). YouTube chỉ cho chọn video đã công khai, nên ghi đích cuối ở scripts/posts/related.json và gắn lại khi đích lên sóng.
