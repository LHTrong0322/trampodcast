# Podcast trigger: lên tập đúng 5:00 sáng

Cloudflare Worker này bấm "Run workflow" podcast thay cho cron GitHub (hay trễ nhiều tiếng).
Cài 1 lần, mất khoảng 10 phút, miễn phí.

## Bước 1: Tạo token GitHub

1. Vào https://github.com/settings/personal-access-tokens/new
2. Token name: `tram-podcast-trigger`. Expiration: chọn dài nhất bạn muốn (hết hạn thì làm lại bước này).
3. Repository access: **Only select repositories**, chọn `trampodcast`.
4. Permissions, mục Repository permissions: **Actions** chọn **Read and write**. Không cần quyền nào khác.
5. Bấm **Generate token**, copy chuỗi `github_pat_...` (chỉ hiện 1 lần, không gửi cho ai).

## Bước 2: Tạo Worker trên Cloudflare

1. Vào https://dash.cloudflare.com, mục **Workers & Pages**, bấm **Create**, chọn **Create Worker** (Start with Hello World).
2. Đặt tên `tram-podcast-trigger`, bấm **Deploy**.
3. Bấm **Edit code**, xoá hết code mẫu, dán toàn bộ nội dung file `worker.js` ở thư mục này, bấm **Deploy**.

## Bước 3: Thêm token vào Worker

1. Trong Worker vừa tạo, vào **Settings**, mục **Variables and Secrets**, bấm **Add**.
2. Type: **Secret**. Name: `GH_TOKEN`. Value: dán token ở Bước 1. Bấm **Deploy**.

## Bước 4: Đặt giờ chạy

1. Vẫn trong **Settings**, mục **Trigger Events** (hoặc Triggers), bấm **Add**, chọn **Cron Triggers**.
2. Thêm 2 lịch (giờ UTC):
   - `0 22 * * *` (5:00 sáng VN)
   - `20 22 * * *` (5:20 sáng VN, dự phòng)
3. Lưu lại.

## Bước 5: Thử ngay

Trong tab Cron Triggers bấm thử (Test / Trigger) hoặc chờ sáng mai. Vào tab Actions của repo:
sẽ thấy 1 lượt "Trạm Podcast Crypto, tạo tập podcast" vừa chạy. Nếu hôm nay đã có tập, lượt đó tự bỏ qua
(log ghi "Hôm nay đã có tập..."), như vậy là đúng.

## Cách quay lại

Xoá Worker trên Cloudflare là xong. Cron GitHub cũ vẫn còn trong `podcast.yml`, podcast vẫn chạy như trước (chỉ là hay trễ).
