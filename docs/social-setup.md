# Đăng tự động Smart Penguin Insights lên YouTube, TikTok, Facebook

Bản cho Trọng (không cần biết code). Làm một lần. Xong thì mỗi video dựng xong sẽ tự đăng.

## Cách hệ thống chạy
1. Trọng duyệt kịch bản ("ok kịch bản") → máy dựng video trên GitHub.
2. Dựng xong: gửi Telegram như cũ, rồi tự đăng lên các nền tảng đã có key.
3. Kết quả đăng (link, trạng thái) gửi vào Telegram mục "📤 ĐĂNG TỰ ĐỘNG".
4. Nền tảng nào chưa có key thì bỏ qua, video vẫn ra bình thường.

Chỗ để key: repo trampodcast > Settings > Secrets and variables > Actions.
- Tab **Secrets** (chữ bí mật, không ai đọc lại được): các khoá YT_, FB_, TIKTOK_.
- Tab **Variables** (công tắc): SOCIAL_AUTOPOST, SOCIAL_PRIVACY, FB_PUBLISH, TIKTOK_PRIVACY.

| Variable | Giá trị | Ý nghĩa |
|---|---|---|
| SOCIAL_AUTOPOST | 1 | Bật đăng tự động (0 hoặc không tạo = tắt) |
| SOCIAL_PRIVACY | private / unlisted / public | YouTube. Nên để **private** vài lần đầu, xem ổn rồi đổi public |
| FB_PUBLISH | 0 / 1 | Facebook: 0 = lưu nháp, 1 = đăng công khai ngay |
| TIKTOK_PRIVACY | SELF_ONLY / PUBLIC_TO_EVERYONE | TikTok. App chưa qua kiểm duyệt thì chỉ dùng được SELF_ONLY |

---

## 1. YouTube (tự động được hoàn toàn)

### Bước 1: Tạo dự án Google Cloud
1. Vào https://console.cloud.google.com, đăng nhập **đúng Gmail đang sở hữu kênh YouTube**.
2. Góc trên bấm chọn dự án > **New Project** > đặt tên `smart-penguin-upload` > Create.
3. Menu > **APIs & Services > Library** > tìm **YouTube Data API v3** > Enable.

### Bước 2: Màn hình xin quyền (OAuth consent screen)
1. APIs & Services > **OAuth consent screen** (hoặc Google Auth Platform > Branding).
2. User type: **External**. App name: `Smart Penguin Uploader`, email hỗ trợ: Gmail của bạn.
3. Mục **Audience / Test users**: thêm chính Gmail của bạn.
4. Mục **Publishing status**: bấm **Publish app** (chuyển sang In production).
   Lý do: để ở chế độ Testing thì chìa khoá tự hết hạn sau 7 ngày. Google sẽ báo "chưa xác minh", không sao, chỉ mình bạn dùng.

### Bước 3: Tạo Client ID
1. APIs & Services > **Credentials** > Create Credentials > **OAuth client ID**.
2. Application type: **Web application**. Tên: `uploader`.
3. Authorized redirect URIs: thêm `https://developers.google.com/oauthplayground`
4. Create → copy **Client ID** và **Client secret**.

### Bước 4: Lấy Refresh token (chìa khoá dài hạn)
1. Mở https://developers.google.com/oauthplayground
2. Bấm bánh răng ⚙ góc phải > tick **Use your own OAuth credentials** > dán Client ID, Client secret.
3. Ô bên trái "Input your own scopes" dán: `https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube`
4. Bấm **Authorize APIs** > chọn Gmail kênh > nếu báo "Google hasn't verified this app" bấm **Advanced > Go to ... (unsafe)** > Allow.
   Nếu Gmail có nhiều kênh: chọn đúng kênh Smart Penguin Insights.
5. Bấm **Exchange authorization code for tokens** → copy **Refresh token**.

### Bước 5: Tạo Secrets
- `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`

### Bước 6: Mở khoá tính năng kênh
- Vào https://www.youtube.com/verify xác minh số điện thoại. Không xác minh thì máy không đặt được **ảnh bìa tuỳ chỉnh** và video dài hơn 15 phút.

### Lưu ý YouTube
- Hạn mức miễn phí đủ đăng vài video mỗi ngày (1 video dài + 2 short = 3 lượt đăng).
- Google có thể khoá video đăng qua API ở chế độ riêng tư nếu dự án chưa được duyệt. Nếu thấy video luôn bị khoá Private:
  điền form "YouTube API Services - Audit and Quota Extension" (Google xét duyệt, mất vài tuần). Trong lúc chờ: máy vẫn đăng Private, bạn vào Studio bấm Public.
- Bình luận ghim: API không ghim được, máy vẫn gửi nội dung bình luận ghim qua Telegram để bạn dán và ghim tay (10 giây).

---

## 2. Facebook Page (tự động được)

Điều kiện: bạn là **admin của Fanpage** Smart Penguin Insights (Reels chỉ đăng được lên Trang, không đăng lên trang cá nhân).

### Bước 1: Tạo app Meta
1. Vào https://developers.facebook.com > My Apps > **Create App**.
2. Use case: chọn **Manage everything on your Page** (hoặc "Other" > loại Business).
3. Đặt tên `Smart Penguin Uploader`, nối với Business Portfolio của bạn (nếu có).
4. App Settings > Basic: copy **App ID**, **App secret**. Điền Privacy Policy URL: `https://tram-podcast-crypto.pages.dev`.

### Bước 2: Lấy token ngắn hạn
1. Mở https://developers.facebook.com/tools/explorer
2. Chọn app vừa tạo. User or Page: **User Token**.
3. Add permission: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `business_management`.
4. **Generate Access Token** > chọn đúng Fanpage > Continue/Save → copy token.

### Bước 3: Đổi sang token Trang không hết hạn
1. Mở https://colab.research.google.com > New notebook.
2. Dán toàn bộ file `tao_token_facebook.py` (trong repo) > bấm ▶.
3. Dán App ID, App secret, token ở bước 2 → nó in ra `FB_PAGE_ID` và `FB_PAGE_TOKEN` của từng Trang.

### Bước 4: Tạo Secrets
- `FB_PAGE_ID`, `FB_PAGE_TOKEN`. Variable `FB_PUBLISH` = 0 (nháp) cho vài lần đầu.

### Lưu ý Facebook
- App để chế độ Development vẫn đăng được lên Trang mà chính bạn quản trị. Không cần gửi Meta duyệt (App Review) vì chỉ bạn dùng.
- Giới hạn: tối đa 30 Reels đăng qua API mỗi 24 giờ.
- Nếu đổi mật khẩu Facebook hoặc gỡ quyền app, token chết: chạy lại bước 2 và 3.

---

## 3. TikTok (tự động một phần, cần TikTok duyệt mới đăng công khai)

Sự thật cần biết trước: app TikTok **chưa qua kiểm duyệt (audit)** chỉ đăng được video **chỉ mình tôi (SELF_ONLY)**,
và tài khoản TikTok phải đang để **riêng tư** lúc đăng. Muốn đăng công khai tự động phải gửi TikTok duyệt app (vài ngày đến 2 tuần).

### Cách A (khuyên dùng lúc đầu, không cần app): đăng tay 1 phút
- Telegram đã có sẵn video 9:16 + caption + hashtag TikTok. Mở TikTok trên điện thoại > tải video từ Telegram > dán caption > Đăng.

### Cách B: tạo app để tự đăng
1. Vào https://developers.tiktok.com > đăng nhập > **Manage apps > Connect an app**.
2. Điền: tên app `Smart Penguin Uploader`, icon (logo kênh), mô tả "Đăng video do chính tôi sản xuất lên TikTok của tôi",
   Terms of Service URL và Privacy Policy URL: `https://tram-podcast-crypto.pages.dev`.
3. **Add products**: thêm **Login Kit** và **Content Posting API**. Trong Content Posting API bật **Direct Post**.
4. Login Kit > Redirect URI: `https://tram-podcast-crypto.pages.dev/`
5. Scopes: `user.info.basic`, `video.upload`, `video.publish`.
6. Submit for review (gửi duyệt app). Trong lúc chờ có thể dùng **Sandbox** với tài khoản TikTok của bạn.
7. Có Client key, Client secret: mở Colab, dán file `tao_token_tiktok.py`, bấm ▶, làm theo → ra `TIKTOK_REFRESH_TOKEN`.
8. Tạo Secrets: `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REFRESH_TOKEN`. Variable `TIKTOK_PRIVACY` = SELF_ONLY.
9. Khi được duyệt app xong, gửi thêm form **Content Posting API audit** để mở khoá đăng công khai,
   rồi đổi `TIKTOK_PRIVACY` = PUBLIC_TO_EVERYONE. Video đăng riêng tư trước đó KHÔNG tự chuyển công khai.
- Refresh token TikTok sống khoảng 1 năm: mỗi năm chạy lại bước 7.
- Máy tự gắn nhãn "nội dung có AI" (giọng đọc AI) theo luật TikTok.

---

## 4. Setup + SEO từng kênh (làm tay một lần, máy không làm được)

### YouTube
1. **Tên kênh**: Smart Penguin Insights. **Handle**: @smartpenguininsights (hoặc gần nhất còn trống).
2. **Mô tả kênh** (dán vào Studio > Customization > Basic info):
   "Smart Penguin Insights: tóm tắt và phân tích những bài viết crypto chất lượng nhất trên X, bằng tiếng Việt dễ hiểu.
   Tư duy đầu tư, tokenomics, dòng tiền, bài học từ các dự án lớn. Video mới mỗi tuần. Không phải lời khuyên đầu tư. Liên hệ: @Trong0322"
3. **Từ khoá kênh** (Settings > Channel > Basic info > Keywords):
   crypto, đầu tư crypto, phân tích crypto, altcoin, bitcoin, tokenomics, kiến thức crypto, smart penguin insights
4. **Ảnh đại diện**: logo chim cánh cụt. **Banner** 2560x1440 (vùng an toàn giữa 1546x423): tên kênh + câu "Insight crypto dễ hiểu mỗi tuần".
5. **Playlist**: "Tư duy đầu tư crypto", "Phân tích dự án", "Shorts insight". Bật **Default upload settings**: ngôn ngữ Tiếng Việt, danh mục Education.
6. **Watermark** (Branding > Video watermark): logo, hiện suốt video → tăng đăng ký.
7. **End screen** mỗi video dài: thêm "Subscribe" + "Video gần nhất" (API không làm được, Studio có nút "Import from video" để chép từ video trước, 10 giây).
8. **Ngoài máy làm sẵn mỗi video**: tiêu đề có từ khoá đứng đầu, mô tả có chương thời gian, tags, hashtag, ảnh bìa.

### TikTok
1. Chuyển sang **Business account** (Settings > Account > Switch to Business) để xem số liệu và gắn link.
2. **Tên hiển thị**: Smart Penguin Insights · Crypto. **Username**: @smartpenguininsights.
3. **Bio** (80 ký tự): "Insight crypto dễ hiểu mỗi ngày 🐧 Không phải lời khuyên đầu tư"
4. Link bio: kênh YouTube. Ghim 3 video hay nhất.
5. Caption có từ khoá ở câu đầu (TikTok tìm kiếm theo chữ trong caption và chữ trên video), 3 đến 5 hashtag: #crypto #dautucrypto #bitcoin #altcoin #smartpenguin.
6. Giờ đăng gợi ý cho người xem Việt Nam: 11:30 đến 12:30 hoặc 20:00 đến 22:00.

### Facebook Page
1. Tên Trang: Smart Penguin Insights. Danh mục: **Education website** hoặc **Media/news company**.
2. Username trang: @smartpenguininsights. Ảnh đại diện logo, ảnh bìa 1640x624.
3. Phần Giới thiệu: dùng lại mô tả kênh YouTube (ngắn gọn 1 đến 2 câu).
4. Nút hành động: **Follow** hoặc **Watch video** (link YouTube).
5. Bật **Professional dashboard** để xem số liệu Reels. Reels 9:16 tiếp cận tốt hơn video dài trên Facebook.

### Lưu ý tuân thủ (crypto ở Việt Nam)
- Mọi caption và mô tả đã có dòng "Không phải lời khuyên đầu tư, DYOR". Không thêm link sàn, mã giới thiệu hay kêu gọi mua bán trong video tự đăng.
- YouTube/Facebook/TikTok có thể hạn chế quảng cáo nội dung crypto; nội dung kiến thức thì đăng bình thường.
