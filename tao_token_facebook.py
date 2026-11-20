# =====================================================================
#  LẤY FB_PAGE_ID + FB_PAGE_TOKEN (token Trang không hết hạn), chạy 1 lần.
#  Cách dễ nhất: vào https://colab.research.google.com → New notebook
#  → dán TOÀN BỘ file này vào 1 ô → bấm ▶ → làm theo hướng dẫn hiện ra.
#  Xem đầy đủ: docs/social-setup.md (phần Facebook)
# =====================================================================
import requests

V = "v25.0"
app_id = input("Dán App ID (developers.facebook.com > app của bạn > Settings > Basic): ").strip()
app_secret = input("Dán App secret (cùng trang, bấm Show): ").strip()
short = input("Dán User access token lấy từ Graph API Explorer (đã tick quyền pages_*): ").strip()

r = requests.get(f"https://graph.facebook.com/{V}/oauth/access_token", params={
    "grant_type": "fb_exchange_token", "client_id": app_id, "client_secret": app_secret,
    "fb_exchange_token": short}).json()
if "access_token" not in r:
    raise SystemExit(f"Lỗi đổi token dài hạn: {r}")
pages = requests.get(f"https://graph.facebook.com/{V}/me/accounts",
                     params={"access_token": r["access_token"], "fields": "id,name,access_token"}).json()
for p in pages.get("data", []):
    print("\n" + "=" * 70)
    print("Trang:", p["name"])
    print("FB_PAGE_ID    =", p["id"])
    print("FB_PAGE_TOKEN = copy NGUYÊN dòng dưới:")
    print(p["access_token"])
print("=" * 70)
print("Chọn đúng Trang của kênh, tạo 2 GitHub Secret FB_PAGE_ID và FB_PAGE_TOKEN.")
