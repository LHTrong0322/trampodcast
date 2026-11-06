# =====================================================================
#  TẠO "CHÌA KHOÁ" TG_SESSION CHO USERBOT — chạy 1 lần duy nhất.
#  Cách dễ nhất: vào https://colab.research.google.com → New notebook
#  → dán TOÀN BỘ file này vào 1 ô → bấm ▶ → làm theo hướng dẫn hiện ra.
# =====================================================================
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "telethon"], check=True)

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("Nhập api_id (số, lấy ở my.telegram.org): ").strip())
api_hash = input("Nhập api_hash: ").strip()

print("\nTelegram sẽ hỏi số điện thoại (dạng +84...) rồi gửi mã vào app Telegram của bạn.")
with TelegramClient(StringSession(), api_id, api_hash) as client:
    me = client.get_me()
    print(f"\n✓ Đăng nhập thành công: {me.first_name} (@{me.username})")
    print("\nCác kênh bạn đang tham gia (dùng tên/ID này cho sources.yaml):")
    for d in client.iter_dialogs():
        if d.is_channel:
            uname = getattr(d.entity, "username", None)
            print(f"   {uname or d.id:<28} {d.name}")
    print("\n" + "=" * 70)
    print("TG_SESSION — copy NGUYÊN dòng dưới, dán vào GitHub Secret tên TG_SESSION:")
    print("=" * 70)
    print(client.session.save())
    print("=" * 70)
    print("⚠️  Chuỗi này = quyền đăng nhập tài khoản Telegram của bạn. KHÔNG gửi cho ai.")
