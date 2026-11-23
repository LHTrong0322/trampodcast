# CLAUDE.md: Trạm Podcast Crypto + Smart Penguin Insights

## 0. Bot chạy tự động: ĐỌC TRƯỚC

Nếu bạn đang chạy không có người (`claude -p` trong GitHub Actions: chấm kịch bản, xác nhận tin nóng, review video, growth report...):
BỎ QUA toàn bộ các mục bên dưới. Làm đúng và chỉ đúng prompt được giao, giữ nguyên định dạng đầu ra (ví dụ chỉ in JSON khi được yêu cầu).
Không hỏi lại, không in phần "ASSUMPTIONS", không gọi skill engineering.

Các mục dưới đây chỉ áp dụng cho phiên code có Trọng (sửa code, thêm tính năng, sửa lỗi).

## 1. Chủ dự án

- Trọng (@Trong0322), không có nền code, làm theo kiểu vibe coding. Giải thích bằng tiếng Việt dễ hiểu, hướng dẫn từng bước rõ ràng.
- Tuyệt đối không dùng dấu gạch dài (em dash, en dash) ở bất cứ đâu: code, comment, commit message, text video, caption. Dùng dấu phẩy hoặc dấu hai chấm.
- Bối cảnh, quyết định và quy tắc nội dung đã chốt nằm ở `HANDOFF.md`: đọc trước khi sửa phần liên quan.

## 2. Quy trình code: bộ agent-skills (addyosmani/agent-skills)

Bộ skill nằm sẵn trong `.claude/skills/` (phiên bản ghi ở `.claude/AGENT-SKILLS-VERSION`).

- Trước mọi task code, áp dụng skill `using-agent-skills` để chọn đúng quy trình.
- Feature mới: `/spec` → `/plan` → `/build` → `/test` → `/review` → `/ship`.
- Lỗi, bot chạy fail, workflow đỏ: dùng `debugging-and-error-recovery` (tái hiện, tìm nguyên nhân gốc, sửa tối thiểu, chặn lỗi quay lại).
- Ý tưởng còn mơ hồ: dùng `interview-me` để hỏi Trọng cho rõ trước khi code.
- Đụng tới key/token/secret (Gemini, Telegram, YouTube, Facebook, Claude): áp dụng `security-and-hardening`. Không bao giờ in secret ra log.

## 3. Điều chỉnh cho dự án này

- Test: chỉ viết test cho logic quan trọng (lọc tin, chấm điểm, lịch đăng, xử lý key dự phòng). Không bắt buộc TDD cho phần dựng hình, giọng đọc, giao diện.
- Pipeline podcast chạy mỗi ngày khoảng 5:00 sáng giờ VN: không được làm hỏng nó. Thay đổi lớn ở `podcast.py`, `news_flash.py`, `insight*.py`, `.github/workflows/` phải nói rõ rủi ro và cách quay lại trước khi làm.
- Những việc không hoàn tác được (đăng bài thật lên YouTube/Facebook/TikTok, xoá video, đổi secret): phải hỏi Trọng trước.
- Giữ phạm vi: chỉ sửa đúng phần được giao, thấy chỗ khác cần cải thiện thì ghi lại và hỏi.
