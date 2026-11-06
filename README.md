# 🎙️ Trạm Podcast Crypto — Podcast tin crypto tự động

Mỗi ngày 2 lần (khoảng 6:47 sáng và 6:47 tối giờ VN), hệ thống sẽ tự động:

1. **Gom tin** từ các kênh Telegram (@unfolded, @Fivemincryptoann, @ThuanCapital, @WatcherGuru, Wu Blockchain) và 8 trang tin crypto lớn (CoinDesk, The Block, Cointelegraph, Decrypt, Blockworks, DL News, The Defiant, Bitcoin Magazine).
2. **AI (Gemini) lọc tin**: chỉ giữ tin có giá trị cho investor (pháp lý, vĩ mô/chính trị, dòng tiền ETF, dự án, hack, on-chain), bỏ shill/giveaway, gộp tin trùng.
3. **Dịch sang tiếng Việt**, giữ nguyên thuật ngữ chuyên ngành (ETF, airdrop, unlock, TVL…).
4. **Viết kịch bản podcast** cho MC "Bé Mai" và **đọc thành MP3** bằng giọng nữ trẻ, dễ thương (Gemini TTS).
5. **Đăng lên web** của bạn + **gửi file audio vào Telegram** + tạo **feed podcast** để nghe bằng app podcast.

Chi phí: **0đ** nếu nằm trong gói miễn phí của Gemini, GitHub và Cloudflare.

---

## Cài đặt (khoảng 20 phút, làm 1 lần)

### Bước 1 — Lấy Gemini API key (miễn phí)
1. Vào **https://aistudio.google.com** → đăng nhập Gmail.
2. Bấm **Get API key** → **Create API key**.
3. Copy đoạn key (dạng `AIza...`) → dán tạm vào Notes. **Không chia sẻ key này cho ai.**

### Bước 2 — Tạo repo GitHub
1. Vào **https://github.com/new**.
2. Repository name: `tram-podcast-crypto` · chọn **Private** · bấm **Create repository**.
3. Bấm link **uploading an existing file** → kéo thả các file/thư mục sau từ file zip đã giải nén:
   - `sources.yaml`, `README.md`
   - thư mục `scripts` (chứa `podcast.py`)
   - thư mục `site` (chứa `index.html`, `cover.svg`, `cover.png`)
   → bấm **Commit changes**.
4. **Thư mục `.github` là thư mục ẩn** nên kéo thả hay bị sót. Tạo nó bằng tay:
   - Bấm **Add file → Create new file**.
   - Ô tên file gõ chính xác: `.github/workflows/podcast.yml`
   - Mở file `podcast.yml` trong zip bằng Notepad/TextEdit → copy toàn bộ → dán vào → **Commit changes**.

### Bước 3 — Cất key vào "két sắt" của GitHub
Trong repo: **Settings → Secrets and variables → Actions → tab Secrets → New repository secret**. Tạo lần lượt:

| Name | Value |
|---|---|
| `GEMINI_API_KEY` | key ở Bước 1 |
| `TELEGRAM_BOT_TOKEN` | token bot Telegram (dùng lại bot của RSI Radar cũng được) |
| `TELEGRAM_CHAT_ID` | ID chat/kênh muốn nhận podcast |

> Không cần Telegram thì bỏ qua 2 dòng cuối, podcast vẫn lên web bình thường.
> Muốn gửi vào **kênh** Telegram: thêm bot làm admin của kênh, Chat ID dạng `-100xxxxxxxxxx`.

### Bước 4 — Chạy thử tập đầu tiên
1. Vào tab **Actions** của repo → nếu có nút xanh "I understand my workflows…" thì bấm.
2. Chọn **Trạm Podcast Crypto — tạo tập podcast** bên trái → **Run workflow**.
3. Ô "Lấy tin trong bao nhiêu giờ" gõ `24` → **Run workflow**.
4. Đợi 5–10 phút. Dấu ✅ xanh là xong, Telegram sẽ nhận được file audio.
   Bấm vào lần chạy để xem log: nguồn nào ✓ lấy được bao nhiêu tin, nguồn nào ✗ lỗi.

> Nếu bước "Lưu & xuất bản" báo lỗi quyền (403): **Settings → Actions → General → Workflow permissions → Read and write permissions → Save**, rồi chạy lại.

### Bước 5 — Đưa lên web bằng Cloudflare Pages
1. Vào **dash.cloudflare.com → Workers & Pages → Create → tab Pages → Connect to Git**.
2. Chọn repo `tram-podcast-crypto`.
3. Cấu hình:
   - **Production branch**: `podcast-data` ← quan trọng, nhánh này do bot tạo ở Bước 4
   - **Framework preset**: None
   - **Build command**: để trống
   - **Build output directory**: để trống
4. **Save and Deploy** → bạn có link dạng `https://tram-podcast-crypto.pages.dev`.
5. Quay lại GitHub: **Settings → Secrets and variables → Actions → tab Variables → New repository variable**:
   Name `SITE_URL`, Value là link vừa có (không có dấu `/` ở cuối).
   → Từ tập sau, web sẽ có **feed podcast** và Telegram có nút "Nghe trên web".

Xong! Từ giờ mọi thứ chạy tự động 2 lần/ngày.

### Bước 6 (nên làm) — Bật USERBOT để đọc mọi kênh Telegram
Mặc định hệ thống đọc trang xem trước `t.me/s/tênkênh`, nhưng có kênh tắt tính năng này hoặc là kênh private.
Bật userbot thì hệ thống đọc bằng **chính tài khoản Telegram của bạn** → đọc được **mọi kênh bạn đã tham gia**.

**6.1 — Lấy api_id và api_hash**
1. Vào **https://my.telegram.org** → nhập số điện thoại (+84…) → nhập mã Telegram gửi vào app.
2. Bấm **API development tools** → điền App title: `tram podcast`, Short name: `trampodcast`, Platform: Desktop → **Create application**.
3. Copy **App api_id** (số) và **App api_hash** (chuỗi dài).

**6.2 — Tạo chìa khoá TG_SESSION (dùng Google Colab, không cần cài gì)**
1. Vào **https://colab.research.google.com** → **New notebook**.
2. Mở file `tao_session_telegram.py` → copy toàn bộ → dán vào ô code → bấm nút ▶.
3. Nhập lần lượt: api_id → api_hash → số điện thoại (+84…) → mã Telegram gửi vào app (có bật xác minh 2 bước thì nhập thêm mật khẩu).
4. Màn hình in ra **danh sách kênh bạn đang tham gia** (tên/ID dùng cho `sources.yaml`) và một **chuỗi rất dài** → copy nguyên chuỗi đó.

**6.3 — Thêm 3 secret vào GitHub** (Settings → Secrets and variables → Actions → New repository secret):

| Name | Value |
|---|---|
| `TG_API_ID` | api_id |
| `TG_API_HASH` | api_hash |
| `TG_SESSION` | chuỗi dài ở 6.2 |

**6.4 — Tham gia kênh**: tài khoản của bạn phải **đã join** kênh muốn đọc. Kênh private không có username thì ghi ID dạng `-100xxxxxxxxxx` (lấy từ danh sách in ra ở 6.2) vào `sources.yaml`.

Chạy thử như Bước 4 → log sẽ hiện dòng `Đọc Telegram bằng tài khoản userbot: x/y kênh`.
Kênh nào userbot đọc không được thì hệ thống tự quay về cách đọc web preview.

> ⚠️ **Bảo mật**: `TG_SESSION` có quyền đăng nhập tài khoản Telegram của bạn. Chỉ để trong GitHub Secrets, không gửi cho ai, xoá ô Colab sau khi xong.
> Muốn an toàn hơn: dùng **một tài khoản Telegram phụ** chỉ để join các kênh tin.
> Muốn thu hồi: Telegram → Cài đặt → Thiết bị → kết thúc phiên tương ứng.
> Hệ thống chỉ **đọc** tin, không gửi tin hay tương tác gì bằng tài khoản này.

---

## Cách nghe
- **Web**: mở link Pages trên điện thoại → "Thêm vào màn hình chính" để dùng như app. Có tua ±15s, chỉnh tốc độ 1.15×/1.3×/1.5×, nhớ vị trí đang nghe, xem lời thoại và link nguồn gốc của từng tin.
- **Telegram**: file audio + danh sách tin kèm link nguồn.
- **App podcast**: thêm feed `https://<link-của-bạn>/feed.xml`
  (Pocket Casts / Podcast Addict: "Add by URL"; Apple Podcasts: Thư viện → ⋯ → "Theo dõi chương trình bằng URL").

---

## Tuỳ chỉnh (chỉ cần sửa `sources.yaml` trên GitHub, bấm ✏️ để sửa)

| Muốn… | Sửa chỗ nào |
|---|---|
| Thêm/bớt kênh Telegram | mục `telegram:` — chỉ ghi username, kênh phải **public** |
| Thêm trang tin | mục `rss:` — thêm 1 dòng `{ name: "...", url: "link RSS" }` |
| Đổi giọng | `voice:` — thử `Laomedeia`, `Zephyr`, `Autonoe`, `Aoede` |
| Giọng "cute" hơn/nghiêm túc hơn | sửa đoạn `voice_style:` |
| Tập dài/ngắn hơn | `target_minutes:` |
| Đổi tên MC / tên show | `host_name:` / `name:` |
| Đổi giờ phát | file `.github/workflows/podcast.yml`, dòng `cron` (giờ UTC = giờ VN − 7) |

### Thêm nguồn X (Twitter), vd @CryptoWendyO
X không cho đọc dữ liệu miễn phí, nên cần một dịch vụ chuyển tài khoản X thành link RSS:
1. Vào **rss.app** (hoặc dịch vụ tương tự) → tạo feed từ link `https://x.com/CryptoWendyO`.
2. Copy link RSS (đuôi `.xml`) → dán vào mục `x_rss:` trong `sources.yaml` (bỏ dấu `#` đầu dòng).
Lưu ý các dịch vụ này thường giới hạn tần suất cập nhật ở gói miễn phí — kiểm tra gói trước khi dùng.

---

## Gặp lỗi?
- **Một nguồn bị ✗**: không sao, các nguồn khác vẫn chạy. Với kênh Telegram: bật userbot (Bước 6) và kiểm tra tài khoản đã join kênh đó chưa.
- **"bận (429)" / hết lượt**: gói free của Gemini TTS có giới hạn số lần đọc mỗi ngày. Hệ thống tự đợi và tự chuyển model dự phòng. Nếu vẫn hết, có thể gắn thanh toán ở Google AI Studio — ước tính khoảng 0,2–0,3 USD/tập 7 phút.
- **Model không tồn tại (404)**: Google đổi tên model thường xuyên. Sửa danh sách `models:` trong `sources.yaml` theo tên mới ở trang https://ai.google.dev/gemini-api/docs/models.
- **Giọng đọc lỡ đọc cả chỉ dẫn**: hiếm gặp; chạy lại hoặc đổi model TTS.
- **Repo public lâu không có commit mới**: GitHub có thể tạm dừng lịch chạy sau 60 ngày — vào tab Actions bấm Enable lại.

⚠️ Nội dung do AI tổng hợp, có thể sai sót. Không phải lời khuyên đầu tư.
