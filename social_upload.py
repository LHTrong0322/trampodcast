"""Đăng tự động video Smart Penguin Insights lên YouTube, Facebook Page, TikTok.

Chỉ chạy khi biến SOCIAL_AUTOPOST=1 (GitHub > Settings > Secrets and variables > Actions > Variables)
và đã có key của từng nền tảng trong Secrets. Thiếu key nền tảng nào thì bỏ qua nền tảng đó, không làm hỏng video.
Hướng dẫn lấy key: docs/social-setup.md

Chế độ hiển thị (Variables):
  SOCIAL_PRIVACY = private | unlisted | public   (YouTube, mặc định private để Trọng xem lại rồi bấm công khai)
  FB_PUBLISH     = 1 đăng công khai ngay, 0 lưu nháp (mặc định 0)
  TIKTOK_PRIVACY = SELF_ONLY | PUBLIC_TO_EVERYONE ... (mặc định SELF_ONLY; app TikTok chưa qua kiểm duyệt chỉ đăng được riêng tư)
Không bao giờ in key/token ra log.
"""
from __future__ import annotations

import json
from hashtags import with_tags   # hashtag không trùng (Trọng 22/11)
import os
from pathlib import Path

import re

import requests

import podcast as P

log = P.log
FB_VER = "v25.0"
TIMEOUT = 600


def _env(*names: str) -> bool:
    return all(os.getenv(n, "").strip() for n in names)



# ---------------------------------------------------------------- Facebook: luật link (Trọng 21/11)
# Thuật toán Facebook bóp tiếp cận bài có link, nên KHÔNG BAO GIỜ gắn link trong caption/mô tả.
# Link chỉ đặt ở bình luận đầu tiên; không bình luận được thì bỏ qua, không gắn link ở đâu cả.
TELEGRAM = "https://t.me/SmartPanda0322"
_URL = re.compile(r"(https?://\S+|\bt\.me/\S+|\b(?:www\.)?[a-z0-9-]+\.(?:com|io|me|xyz|net|org|gg|be)/\S*)", re.I)


def strip_links(text: str) -> str:
    out = []
    for line in (text or "").splitlines():
        if _URL.search(line):
            line = _URL.sub("", line).rstrip(" :·•-|")
            if len(re.sub(r"[^\wÀ-ỹ]", "", line)) < 12:   # dòng chỉ còn nhãn kiểu "💬 Telegram" thì bỏ hẳn
                continue
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def fb_comment(object_id: str, text: str) -> tuple[bool, str]:
    try:
        r = requests.post(f"https://graph.facebook.com/{FB_VER}/{object_id}/comments",
                          data={"access_token": os.environ["FB_PAGE_TOKEN"].strip(), "message": text}, timeout=60)
        return r.ok, r.text[:200]
    except Exception as ex:
        return False, str(ex)[:200]


def fb_link_comment(yt_url: str | None) -> str:
    parts = []
    if yt_url:
        parts.append(f"▶ Bản đầy đủ trên YouTube: {yt_url}")
    parts.append(f"💬 Telegram: {TELEGRAM}")
    return "\n".join(parts)


# ---------------------------------------------------------------- YouTube
def _yt_token() -> str:
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=60)
    r.raise_for_status()
    return r.json()["access_token"]


def yt_upload(tok: str, path: Path, title: str, desc: str, tags: list[str], privacy: str) -> str:
    meta = {"snippet": {"title": title[:100], "description": desc[:4900], "tags": tags, "categoryId": "27",
                        "defaultLanguage": "vi", "defaultAudioLanguage": "vi"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False, "embeddable": True}}
    size = path.stat().st_size
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                               "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
                      data=json.dumps(meta), timeout=60)
    r.raise_for_status()
    with open(path, "rb") as f:
        up = requests.put(r.headers["Location"], headers={"Content-Type": "video/mp4", "Content-Length": str(size)},
                          data=f, timeout=TIMEOUT)
    up.raise_for_status()
    return up.json()["id"]


def yt_thumb(tok: str, vid: str, img: Path):
    with open(img, "rb") as f:
        r = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                          headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/png"}, data=f, timeout=120)
    if r.status_code >= 300:  # kênh chưa xác minh số điện thoại thì không được đặt ảnh bìa tuỳ chỉnh
        log(f"   ! YouTube ảnh bìa lỗi {r.status_code}: cần xác minh kênh (youtube.com/verify)")
        return False
    return True


def youtube(res: dict, seo: dict, thumb: Path | None) -> list[str]:
    if not _env("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"):
        log("   YouTube: chưa có key, bỏ qua")
        return []
    privacy = os.getenv("SOCIAL_PRIVACY", "private").strip() or "private"
    tok = _yt_token()
    title = (seo.get("yt_titles") or [res["plan"].get("title", "")])[0]
    vid = yt_upload(tok, Path(res["long"]), title, seo.get("yt_description", ""), seo.get("yt_tags", []), privacy)
    res["yt_url"] = f"https://youtu.be/{vid}"
    out = [f"YouTube video dài ({privacy}): https://youtu.be/{vid}"]
    if thumb and thumb.exists():
        yt_thumb(tok, vid, thumb)
    for i, s in enumerate(res["shorts"]):
        sh = (seo.get("shorts") or [])[i] if i < len(seo.get("shorts") or []) else {}
        t = (sh.get("yt_title") or s["title"])[:90]
        t = t if "#shorts" in t.lower() else f"{t} #Shorts"
        cap_tags = with_tags(sh.get('tiktok_caption', ''), seo.get('hashtags', []), 3)
        d = f"{cap_tags}\n\nVideo đầy đủ: https://youtu.be/{vid}"
        sid = yt_upload(tok, Path(s["path"]), t, d, seo.get("yt_tags", [])[:15], privacy)
        out.append(f"YouTube Short {i + 1} ({privacy}): https://youtube.com/shorts/{sid}")
    return out


# ---------------------------------------------------------------- Facebook Page
def facebook(res: dict, seo: dict) -> list[str]:
    if not _env("FB_PAGE_ID", "FB_PAGE_TOKEN"):
        log("   Facebook: chưa có key, bỏ qua")
        return []
    page, tok = os.environ["FB_PAGE_ID"], os.environ["FB_PAGE_TOKEN"]
    publish = os.getenv("FB_PUBLISH", "0").strip() == "1"
    out = []
    title = (seo.get("yt_titles") or [res["plan"].get("title", "")])[0]
    with open(res["long"], "rb") as f:   # video dài: đăng lên trang dạng video thường
        r = requests.post(f"https://graph-video.facebook.com/{FB_VER}/{page}/videos",
                          data={"access_token": tok, "title": title, "description": strip_links(seo.get("yt_description", ""))[:5000],
                                "published": "true" if publish else "false"},
                          files={"source": ("video.mp4", f, "video/mp4")}, timeout=TIMEOUT)
    r.raise_for_status()
    out.append(f"Facebook video dài ({'công khai' if publish else 'chưa đăng, vào Meta Business Suite để đăng'}): id {r.json().get('id')}")
    for i, s in enumerate(res["shorts"]):   # video ngắn: Reels
        sh = (seo.get("shorts") or [])[i] if i < len(seo.get("shorts") or []) else {}
        st = requests.post(f"https://graph.facebook.com/{FB_VER}/{page}/video_reels",
                           json={"upload_phase": "start", "access_token": tok}, timeout=60)
        st.raise_for_status()
        vid = st.json()["video_id"]
        size = Path(s["path"]).stat().st_size
        with open(s["path"], "rb") as f:
            up = requests.post(f"https://rupload.facebook.com/video-upload/{FB_VER}/{vid}",
                               headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size)},
                               data=f, timeout=TIMEOUT)
        up.raise_for_status()
        cap = strip_links(with_tags(sh.get('tiktok_caption') or s['title'], sh.get('tiktok_hashtags') or seo.get('hashtags', [])))
        fin = requests.post(f"https://graph.facebook.com/{FB_VER}/{page}/video_reels", params={
            "access_token": tok, "video_id": vid, "upload_phase": "finish",
            "video_state": "PUBLISHED" if publish else "DRAFT", "description": cap[:2200]}, timeout=60)
        fin.raise_for_status()
        out.append(f"Facebook Reel {i + 1} ({'công khai' if publish else 'bản nháp'}): id {vid}")
        if publish:   # link chỉ ở bình luận; lỗi thì thôi, không gắn link ở đâu
            ok, err = fb_comment(vid, fb_link_comment(res.get("yt_url")))
            out.append(f"   bình luận link: {'OK, nhớ ghim' if ok else 'không đăng được, đã bỏ qua link'}")
    return out


# ---------------------------------------------------------------- TikTok
def _tt_token() -> str:
    r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", data={
        "client_key": os.environ["TIKTOK_CLIENT_KEY"], "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
        "grant_type": "refresh_token", "refresh_token": os.environ["TIKTOK_REFRESH_TOKEN"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("refresh_token") and j["refresh_token"] != os.environ["TIKTOK_REFRESH_TOKEN"]:
        log("   TikTok: refresh token đã đổi, mỗi năm nhớ chạy lại tao_token_tiktok.py và cập nhật Secret")
    return j["access_token"]


def tiktok(res: dict, seo: dict) -> list[str]:
    if not _env("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN"):
        log("   TikTok: chưa có key, bỏ qua")
        return []
    tok = _tt_token()
    H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"}
    ci = requests.post("https://open.tiktokapis.com/v2/post/publish/creator_info/query/", headers=H, timeout=60).json()
    opts = (ci.get("data") or {}).get("privacy_level_options") or ["SELF_ONLY"]
    want = os.getenv("TIKTOK_PRIVACY", "SELF_ONLY").strip() or "SELF_ONLY"
    privacy = want if want in opts else ("SELF_ONLY" if "SELF_ONLY" in opts else opts[0])
    out = []
    for i, s in enumerate(res["shorts"]):
        sh = (seo.get("shorts") or [])[i] if i < len(seo.get("shorts") or []) else {}
        cap = with_tags(sh.get('tiktok_caption') or s['title'], sh.get('tiktok_hashtags') or seo.get('hashtags', []))[:2200]
        size = Path(s["path"]).stat().st_size
        init = requests.post("https://open.tiktokapis.com/v2/post/publish/video/init/", headers=H, json={
            "post_info": {"title": cap, "privacy_level": privacy, "disable_comment": False, "disable_duet": False,
                          "disable_stitch": False, "is_aigc": True},
            "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}},
            timeout=60).json()
        if (init.get("error") or {}).get("code", "ok") != "ok":
            raise RuntimeError(f"TikTok init lỗi: {init['error'].get('code')} {init['error'].get('message', '')[:120]}")
        with open(s["path"], "rb") as f:
            up = requests.put(init["data"]["upload_url"], data=f, timeout=TIMEOUT, headers={
                "Content-Type": "video/mp4", "Content-Length": str(size), "Content-Range": f"bytes 0-{size - 1}/{size}"})
        up.raise_for_status()
        out.append(f"TikTok video {i + 1} ({privacy}): đã gửi, TikTok xử lý vài phút")
    return out


# ---------------------------------------------------------------- chạy tất cả
def run(res: dict, seo: dict, thumb: Path | None) -> list[str]:
    if os.getenv("SOCIAL_AUTOPOST", "0").strip() != "1":
        log("   Đăng tự động đang tắt (SOCIAL_AUTOPOST khác 1)")
        return []
    log("⑨ Đăng tự động lên mạng xã hội")
    lines = []
    for name, fn in [("YouTube", lambda: youtube(res, seo, thumb)), ("Facebook", lambda: facebook(res, seo)),
                     ("TikTok", lambda: tiktok(res, seo))]:
        try:
            got = fn()
            lines += got
            for g in got:
                log("   " + g)
        except Exception as ex:   # lỗi 1 nền tảng không làm hỏng các nền tảng khác
            msg = str(ex)
            for k in ("YT_CLIENT_SECRET", "YT_REFRESH_TOKEN", "FB_PAGE_TOKEN", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN"):
                if os.getenv(k):
                    msg = msg.replace(os.environ[k], "***")
            lines.append(f"{name}: LỖI {msg[:200]}")
            log(f"   ! {name} lỗi: {msg[:200]}")
    return lines
