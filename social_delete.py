"""Xoá video cũ trên YouTube / Facebook theo yêu cầu của Trọng (chỉ chạy khi Trọng ra lệnh). Không in khoá ra log."""
import os
import sys

import requests

import social_upload as SU


def main(yt_ids: str, fb_ids: str):
    for vid in [x.strip() for x in yt_ids.split(",") if x.strip()]:
        tok = SU._yt_token()
        r = requests.delete("https://www.googleapis.com/youtube/v3/videos", params={"id": vid},
                            headers={"Authorization": f"Bearer {tok}"}, timeout=60)
        print(f"YouTube xoá {vid}: {'OK' if r.status_code == 204 else r.status_code} {r.text[:200]}")
    for vid in [x.strip() for x in fb_ids.split(",") if x.strip()]:
        r = requests.delete(f"https://graph.facebook.com/{SU.FB_VER}/{vid}",
                            params={"access_token": os.environ["FB_PAGE_TOKEN"].strip()}, timeout=60)
        print(f"Facebook xoá {vid}: {r.status_code} {r.text[:200]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
