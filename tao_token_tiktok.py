# =====================================================================
#  LẤY TIKTOK_REFRESH_TOKEN, chạy 1 lần (mỗi năm chạy lại 1 lần).
#  Cách dễ nhất: vào https://colab.research.google.com → New notebook
#  → dán TOÀN BỘ file này vào 1 ô → bấm ▶ → làm theo hướng dẫn hiện ra.
#  Xem đầy đủ: docs/social-setup.md (phần TikTok)
# =====================================================================
import urllib.parse

import requests

client_key = input("Dán Client key (TikTok for Developers > app của bạn): ").strip()
client_secret = input("Dán Client secret: ").strip()
redirect_uri = input("Dán Redirect URI đã khai báo trong Login Kit (vd https://trampodcast.pages.dev/): ").strip()

url = ("https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
    "client_key": client_key, "scope": "user.info.basic,video.publish,video.upload",
    "response_type": "code", "redirect_uri": redirect_uri, "state": "smartpenguin"}))
print("\n1) Mở link này, đăng nhập TikTok của kênh, bấm Cho phép (Authorize):\n")
print(url)
print("\n2) Trình duyệt sẽ chuyển sang Redirect URI (trang có thể trắng hoặc báo lỗi, KHÔNG sao).")
back = input("   Copy NGUYÊN địa chỉ trên thanh trình duyệt lúc đó rồi dán vào đây: ").strip()
code = urllib.parse.parse_qs(urllib.parse.urlparse(back).query).get("code", [back])[0]

r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
    "client_key": client_key, "client_secret": client_secret, "code": code,
    "grant_type": "authorization_code", "redirect_uri": redirect_uri},
    headers={"Content-Type": "application/x-www-form-urlencoded"}).json()
if "refresh_token" not in r:
    print("\nLỗi:", r)
else:
    print("\n" + "=" * 70)
    print("Tạo 3 GitHub Secret (repo trampodcast > Settings > Secrets and variables > Actions):")
    print("TIKTOK_CLIENT_KEY    =", client_key)
    print("TIKTOK_CLIENT_SECRET = (Client secret ở trên)")
    print("TIKTOK_REFRESH_TOKEN = copy NGUYÊN dòng dưới:")
    print("=" * 70)
    print(r["refresh_token"])
    print("=" * 70)
    print(f"Token dùng được khoảng {int(r.get('refresh_expires_in', 0)) // 86400} ngày.")
