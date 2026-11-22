"""Đăng CHỌN LỌC một video đã dựng (GitHub Release insight-<tag>) lên từng nền tảng theo yêu cầu của Trọng.

Ví dụ: đăng video dài lên YouTube, Short 1 lên Facebook:
  python social_post.py --tag 20261120-1915 --youtube long --facebook short1 --privacy public --fb-publish 1
Mục chọn: long, short1, short2 (cách nhau bằng dấu phẩy), để trống = không đăng nền tảng đó.
Khoá lấy từ GitHub Secrets (xem docs/social-setup.md). Không in khoá ra log.
"""
from __future__ import annotations

import argparse
from hashtags import with_tags   # hashtag không trùng (Trọng 22/11)
import json
import os
import subprocess
from pathlib import Path

import requests

import social_upload as SU

FB = SU.FB_VER


def fetch_release(tag: str, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    repo = os.environ["GITHUB_REPOSITORY"]
    subprocess.run(["gh", "release", "download", f"insight-{tag}", "-R", repo, "-D", str(out), "--clobber"], check=True)
    f = {p.name: p for p in out.iterdir()}
    pick = lambda key: next((p for n, p in f.items() if key in n), None)
    return {"long": pick("-16x9.mp4"), "short1": pick("short1-9x16.mp4"), "short2": pick("short2-9x16.mp4"),
            "thumb": pick("thumbnail"), "seo": json.loads(pick("seo-").read_text(encoding="utf-8"))}


def yt_playlist(tok: str, title: str) -> str | None:
    r = requests.get("https://www.googleapis.com/youtube/v3/playlists", params={"part": "snippet", "mine": "true", "maxResults": 50},
                     headers={"Authorization": f"Bearer {tok}"}, timeout=60).json()
    return next((p["id"] for p in r.get("items", []) if p["snippet"]["title"] == title), None)


def yt_add(tok: str, playlist: str | None, vid: str):
    if not playlist:
        return
    requests.post("https://www.googleapis.com/youtube/v3/playlistItems", params={"part": "snippet"},
                  headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                  data=json.dumps({"snippet": {"playlistId": playlist, "resourceId": {"kind": "youtube#video", "videoId": vid}}}), timeout=60)


def fb_long(path: Path, title: str, desc: str, publish: bool) -> str:
    with open(path, "rb") as f:
        r = requests.post(f"https://graph-video.facebook.com/{FB}/{os.environ['FB_PAGE_ID'].strip()}/videos",
                          data={"access_token": os.environ["FB_PAGE_TOKEN"].strip(), "title": title, "description": SU.strip_links(desc)[:5000],
                                "published": "true" if publish else "false"}, files={"source": ("video.mp4", f, "video/mp4")}, timeout=600)
    r.raise_for_status()
    return r.json().get("id", "")


def fb_reel(path: Path, caption: str, publish: bool) -> str:
    page, tok = os.environ["FB_PAGE_ID"].strip(), os.environ["FB_PAGE_TOKEN"].strip()
    st = requests.post(f"https://graph.facebook.com/{FB}/{page}/video_reels", json={"upload_phase": "start", "access_token": tok}, timeout=60)
    st.raise_for_status()
    vid = st.json()["video_id"]
    size = path.stat().st_size
    with open(path, "rb") as f:
        up = requests.post(f"https://rupload.facebook.com/video-upload/{FB}/{vid}",
                           headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size)}, data=f, timeout=600)
    up.raise_for_status()
    fin = requests.post(f"https://graph.facebook.com/{FB}/{page}/video_reels", params={
        "access_token": tok, "video_id": vid, "upload_phase": "finish",
        "video_state": "PUBLISHED" if publish else "DRAFT", "description": SU.strip_links(caption)[:2200]}, timeout=60)
    fin.raise_for_status()
    return vid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--youtube", default="")
    ap.add_argument("--facebook", default="")
    ap.add_argument("--privacy", default="public")
    ap.add_argument("--fb-publish", default="1")
    ap.add_argument("--title", default="")
    ap.add_argument("--playlist", default="Tư duy đầu tư crypto")
    a = ap.parse_args()
    rel = fetch_release(a.tag, Path("rel"))
    seo = rel["seo"]
    title = a.title.strip() or (seo.get("yt_titles") or [""])[0]
    sh = seo.get("shorts") or [{}, {}]
    cap = lambda i: with_tags((sh[i] if i < len(sh) else {}).get('tiktok_caption', ''),
                              (sh[i] if i < len(sh) else {}).get('tiktok_hashtags') or seo.get('hashtags', []))
    yt_items = [x.strip() for x in a.youtube.split(",") if x.strip()]
    fb_items = [x.strip() for x in a.facebook.split(",") if x.strip()]
    report, long_id = [], None
    if yt_items:
        try:
            tok = SU._yt_token()
            if "long" in yt_items:
                long_id = SU.yt_upload(tok, rel["long"], title, seo.get("yt_description", ""), seo.get("yt_tags", []), a.privacy)
                if rel["thumb"]:
                    SU.yt_thumb(tok, long_id, rel["thumb"])
                yt_add(tok, yt_playlist(tok, a.playlist), long_id)
                report.append(f"YouTube video dài ({a.privacy}): https://youtu.be/{long_id}")
            pl_short = yt_playlist(tok, "Shorts insight")
            for i, k in enumerate(["short1", "short2"]):
                if k in yt_items and rel[k]:
                    t = ((sh[i] if i < len(sh) else {}).get("yt_title") or title)[:90]
                    t = t if "#shorts" in t.lower() else f"{t} #Shorts"
                    d = cap(i) + (f"\n\nVideo đầy đủ: https://youtu.be/{long_id}" if long_id else "")
                    sid = SU.yt_upload(tok, rel[k], t, d, seo.get("yt_tags", [])[:15], a.privacy)
                    yt_add(tok, pl_short, sid)
                    report.append(f"YouTube Short {i + 1} ({a.privacy}): https://youtube.com/shorts/{sid}")
        except Exception as ex:
            report.append(f"YouTube LỖI: {str(ex)[:200]}")
    if fb_items:
        pub = a.fb_publish.strip() == "1"
        try:
            if "long" in fb_items:
                fid = fb_long(rel["long"], title, seo.get("yt_description", ""), pub)
                report.append(f"Facebook video dài ({'công khai' if pub else 'chưa đăng'}): id {fid}")
                if pub:
                    ok, _ = SU.fb_comment(fid, SU.fb_link_comment(f"https://youtu.be/{long_id}" if long_id else None))
                    report.append(f"   bình luận link: {'OK, nhớ ghim' if ok else 'không đăng được, đã bỏ qua link'}")
            for i, k in enumerate(["short1", "short2"]):
                if k in fb_items and rel[k]:
                    rid = fb_reel(rel[k], cap(i), pub)
                    report.append(f"Facebook Reel từ Short {i + 1} ({'công khai' if pub else 'bản nháp'}): id {rid}")
                    if pub:
                        ok, _ = SU.fb_comment(rid, SU.fb_link_comment(f"https://youtu.be/{long_id}" if long_id else None))
                        report.append(f"   bình luận link: {'OK, nhớ ghim' if ok else 'không đăng được, đã bỏ qua link'}")
        except Exception as ex:
            report.append(f"Facebook LỖI: {str(ex)[:200]}")
    for line in report:
        print("KẾT QUẢ:", line)
    try:
        import insight_publish as PB
        PB.tg_text("📤 ĐĂNG THEO YÊU CẦU\n" + "\n".join(report))
    except Exception:
        pass


if __name__ == "__main__":
    main()
