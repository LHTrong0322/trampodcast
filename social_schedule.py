"""Đặt lịch đăng theo file kế hoạch Trọng đã duyệt (scripts/posts/<tag>.json).

  python social_schedule.py post scripts/posts/20261120-1915.json   # tải lên ngay, hẹn giờ công khai
  python social_schedule.py comments                                 # đăng bình luận đã tới giờ (chạy mỗi giờ)

YouTube: dùng tính năng Lên lịch chính thức (privacyStatus=private + publishAt), đúng giờ YouTube tự công khai
và gửi thông báo như video mới. Facebook Reel: video_state=SCHEDULED + scheduled_publish_time.
Trạng thái (id video, bình luận đã đăng chưa) lưu ở scripts/posts/<tag>.state.json. Không in khoá ra log.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

import social_post as SP
import social_upload as SU

FB = SU.FB_VER


def _state_path(plan_path: Path) -> Path:
    return plan_path.with_name(plan_path.stem + ".state.json")


def _tg(msg: str):
    try:
        import insight_publish as PB
        PB.tg_text(msg)
    except Exception:
        pass


def with_endcard(path: Path, card: Path) -> Path:
    """Trọng 22/11: cuối short có thẻ "Xem bản đầy đủ" 3 giây (ảnh tĩnh, mờ dần vào)."""
    import subprocess
    out = path.with_name(path.stem + "-endcard.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-loop", "1", "-t", "3", "-i", str(card),
                    "-f", "lavfi", "-t", "3", "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex",
                    "[1:v]scale=1080:1920,format=yuv420p,fps=30,fade=t=in:st=0:d=0.35[e];[0:v]fps=30,format=yuv420p[a];"
                    "[a][0:a][e][2:a]concat=n=2:v=1:a=1[v][au]", "-map", "[v]", "-map", "[au]", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)], check=True)
    return out


def yt_existing(tok: str, title: str) -> str | None:
    """Tìm video cùng tiêu đề trong 15 video tải lên gần nhất (kể cả riêng tư/hẹn giờ)."""
    ch = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "contentDetails", "mine": "true"},
                      headers={"Authorization": f"Bearer {tok}"}, timeout=60).json()
    try:
        up = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except (KeyError, IndexError):
        return None
    r = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params={"part": "snippet", "playlistId": up, "maxResults": 15},
                     headers={"Authorization": f"Bearer {tok}"}, timeout=60).json()
    return next((i["snippet"]["resourceId"]["videoId"] for i in r.get("items", []) if i["snippet"]["title"] == title), None)


def post(plan_path: Path):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    rel = SP.fetch_release(plan["tag"], Path("rel"))
    st = json.loads(_state_path(plan_path).read_text(encoding="utf-8")) if _state_path(plan_path).exists() else {}
    report = []
    save = lambda: _state_path(plan_path).write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    y = plan.get("youtube")
    same = None
    if y and not st.get("yt_id"):
        tok = SU._yt_token()
        pl = SP.yt_playlist(tok, y.get("playlist", ""))
        desc = y["description"].replace("{PLAYLIST_URL}", f"https://www.youtube.com/playlist?list={pl}" if pl else "")
        meta = {"snippet": {"title": y["title"][:100], "description": desc[:4900], "tags": y.get("tags", []), "categoryId": "27",
                            "defaultLanguage": "vi", "defaultAudioLanguage": "vi"},
                "status": {"privacyStatus": "private", "publishAt": y["publish_at"], "selfDeclaredMadeForKids": False, "embeddable": True}}
        same = yt_existing(tok, y["title"][:100])
    if y and not st.get("yt_id") and same:   # lần chạy trước đã tải lên nhưng chưa kịp lưu trạng thái: dùng lại, không tải trùng
        st["yt_id"] = same
        save()
        report.append(f"YouTube: đã có sẵn từ lần chạy trước, lịch {y['publish_at']}. Link: https://youtu.be/{same}")
    if y and not st.get("yt_id"):
        path = rel[y.get("item", "long")]
        if y.get("endcard"):
            path = with_endcard(path, Path(y["endcard"]))
        size = path.stat().st_size
        r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                          headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                                   "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)}, data=json.dumps(meta), timeout=60)
        r.raise_for_status()
        with open(path, "rb") as f:
            up = requests.put(r.headers["Location"], headers={"Content-Type": "video/mp4", "Content-Length": str(size)}, data=f, timeout=900)
        up.raise_for_status()
        vid = up.json()["id"]
        st["yt_id"] = vid
        save()
        th = Path(y["thumb"]) if y.get("thumb") else (rel.get("thumb") if y.get("item", "long") == "long" else None)
        if th:   # short dùng bìa riêng của short, không dùng bìa video dài
            st["thumb_ok"] = SU.yt_thumb(tok, vid, th)
        SP.yt_add(tok, pl, vid)
        report.append(f"YouTube: đã tải lên, tự công khai lúc {y['publish_at']} (giờ VN +7). Link: https://youtu.be/{vid}")
    th = (Path(y["thumb"]) if y and y.get("thumb") else rel.get("thumb") if y and y.get("item", "long") == "long" else None)
    if y and st.get("yt_id") and not st.get("thumb_ok") and th:   # gắn lại ảnh bìa nếu lần trước bị chặn
        st["thumb_ok"] = SU.yt_thumb(SU._yt_token(), st["yt_id"], th)
        report.append("YouTube ảnh bìa: " + ("đã gắn" if st["thumb_ok"] else "vẫn bị chặn, kênh chưa xác minh xong"))
    fb = plan.get("facebook")
    if fb and not st.get("fb_id") and fb.get("item") == "long":   # video dài 16:9: video thường của Trang, hẹn giờ công khai
        page, tok = os.environ["FB_PAGE_ID"].strip(), os.environ["FB_PAGE_TOKEN"].strip()
        with open(rel["long"], "rb") as f:
            r = requests.post(f"https://graph-video.facebook.com/{FB}/{page}/videos", data={
                "access_token": tok, "title": fb.get("title", "")[:250], "description": SU.strip_links(fb["caption"])[:5000],
                "published": "false", "scheduled_publish_time": str(fb["publish_unix"])},
                files={"source": ("video.mp4", f, "video/mp4")}, timeout=900)
        if not r.ok:
            raise RuntimeError(f"Facebook video dài đặt lịch lỗi: {r.text[:300]}")
        st["fb_id"] = r.json().get("id", "")
        st["fb_caption_clean"] = True
        save()
        th = Path(fb["thumb"]) if fb.get("thumb") else rel.get("thumb")
        if th:
            try:
                with open(th, "rb") as fh:
                    mime = "image/png" if str(th).endswith(".png") else "image/jpeg"
                    tr = requests.post(f"https://graph.facebook.com/{FB}/{st['fb_id']}/thumbnails", params={"access_token": tok, "is_preferred": "true"},
                                       files={"source": (Path(th).name, fh, mime)}, timeout=120)
                report.append("Facebook ảnh bìa video dài: " + ("đã gắn" if tr.ok else f"lỗi {tr.status_code}"))
            except Exception as ex:
                report.append(f"Facebook ảnh bìa lỗi: {ex}")
        when = datetime.fromtimestamp(fb["publish_unix"], timezone.utc).isoformat()
        report.append(f"Facebook video dài: đã đặt lịch đăng lúc {when} (giờ VN +7), id {st['fb_id']}")
    if fb and not st.get("fb_id"):
        page, tok = os.environ["FB_PAGE_ID"].strip(), os.environ["FB_PAGE_TOKEN"].strip()
        s0 = requests.post(f"https://graph.facebook.com/{FB}/{page}/video_reels", json={"upload_phase": "start", "access_token": tok}, timeout=60)
        s0.raise_for_status()
        rid = s0.json()["video_id"]
        path = rel[fb.get("item", "short1")]
        if fb.get("endcard"):
            path = with_endcard(path, Path(fb["endcard"]))
        size = path.stat().st_size
        with open(path, "rb") as f:
            u = requests.post(f"https://rupload.facebook.com/video-upload/{FB}/{rid}",
                              headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size)}, data=f, timeout=600)
        u.raise_for_status()
        fin = requests.post(f"https://graph.facebook.com/{FB}/{page}/video_reels", params={
            "access_token": tok, "video_id": rid, "upload_phase": "finish", "video_state": "SCHEDULED",
            "scheduled_publish_time": str(fb["publish_unix"]), "description": SU.strip_links(fb["caption"])[:2200]}, timeout=60)
        if not fin.ok:
            raise RuntimeError(f"Facebook đặt lịch lỗi: {fin.text[:300]}")
        st["fb_id"] = rid
        save()
        if fb.get("thumb"):   # bìa riêng cho Reel
            try:
                with open(fb["thumb"], "rb") as fh:
                    tr = requests.post(f"https://graph.facebook.com/{FB}/{rid}/thumbnails", params={"access_token": tok, "is_preferred": "true"},
                                       files={"source": (Path(fb["thumb"]).name, fh, "image/jpeg")}, timeout=120)
                report.append("Facebook bìa Reel: " + ("đã gắn" if tr.ok else f"lỗi {tr.status_code}"))
            except Exception as ex:
                report.append(f"Facebook bìa Reel lỗi: {ex}")
        when = datetime.fromtimestamp(fb["publish_unix"], timezone.utc).isoformat()
        report.append(f"Facebook Reel: đã đặt lịch đăng lúc {when} (giờ VN +7), id {rid}")
    st.setdefault("comments_done", [])
    _state_path(plan_path).write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    for line in report:
        print("KẾT QUẢ:", line)
    if report:
        _tg("🗓 ĐÃ ĐẶT LỊCH ĐĂNG\n" + "\n".join(report))


def comments():
    now = datetime.now(timezone.utc)
    for plan_path in sorted(Path("scripts/posts").glob("*.json")):
        if plan_path.name.endswith(".state.json"):
            continue
        sp = _state_path(plan_path)
        if not sp.exists():
            continue
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        st = json.loads(sp.read_text(encoding="utf-8"))
        done = st.setdefault("comments_done", [])
        yt_url = f"https://youtu.be/{st['yt_id']}" if st.get("yt_id") else "kênh YouTube Smart Penguin Insights"
        for key in ("youtube", "facebook"):
            c = plan.get(key) or {}
            if not c.get("comment") or key in done:
                continue
            if datetime.fromisoformat(c["comment_at"].replace("Z", "+00:00")) > now:
                continue
            text = c["comment"].replace("{YT_URL}", yt_url)
            if key == "facebook" and SU.TELEGRAM not in text:   # link Telegram chỉ nằm ở bình luận Facebook
                text += f"\n💬 Telegram: {SU.TELEGRAM}"
            ok, err = False, ""
            try:
                if key == "youtube" and st.get("yt_id"):
                    tok = SU._yt_token()
                    r = requests.post("https://www.googleapis.com/youtube/v3/commentThreads", params={"part": "snippet"},
                                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                                      data=json.dumps({"snippet": {"videoId": st["yt_id"], "topLevelComment": {"snippet": {"textOriginal": text}}}}), timeout=60)
                    ok, err = r.ok, r.text[:200]
                elif key == "facebook" and st.get("fb_id"):
                    r = requests.post(f"https://graph.facebook.com/{FB}/{st['fb_id']}/comments",
                                      data={"access_token": os.environ["FB_PAGE_TOKEN"].strip(), "message": text}, timeout=60)
                    ok, err = r.ok, r.text[:200]
            except Exception as ex:
                err = str(ex)[:200]
            done.append(key)   # chỉ thử 1 lần; lỗi thì gửi Telegram để Trọng dán tay
            where = f"https://youtu.be/{st.get('yt_id')}" if key == "youtube" else "Reel trên Trang Facebook"
            if ok:
                msg = f"💬 Đã đăng bình luận {key} ({where}). Vào bấm ⋮ > Ghim nhé."
            else:
                msg = (f"💬 Máy không đăng được bình luận {key} ({err[:120]}). Dán tay rồi Ghim ở {where}:\n\n{text}"
                       if key == "youtube" else f"💬 Facebook chưa có quyền bình luận nên đã BỎ QUA link (không gắn link vào bài). Lỗi: {err[:120]}")
            print("BÌNH LUẬN:", key, "OK" if ok else "LỖI " + err)
            _tg(msg)
        # Trọng 21/11: Facebook bóp bài có link, nên caption Reel đã đăng phải sạch link (link chỉ ở bình luận)
        if st.get("fb_id") and not st.get("fb_caption_clean") and (plan.get("facebook") or {}).get("caption"):
            try:
                r = requests.post(f"https://graph.facebook.com/{FB}/{st['fb_id']}", timeout=60, data={
                    "access_token": os.environ["FB_PAGE_TOKEN"].strip(), "description": SU.strip_links(plan["facebook"]["caption"])[:2200]})
                print("FACEBOOK CAPTION SẠCH LINK:", "OK" if r.ok else f"LỖI {r.text[:200]}")
                if r.ok:
                    st["fb_caption_clean"] = True
            except Exception as ex:
                print("FACEBOOK CAPTION lỗi:", str(ex)[:150])
        # Trọng 21/11: gỡ phụ đề tự động của YouTube (đè lên phụ đề có sẵn trong video). YouTube tạo nó vài phút
        # đến vài giờ sau khi đăng, nên cứ mỗi lần chạy thì thử lại cho tới khi gỡ được (tối đa 48 giờ).
        if st.get("yt_id") and not st.get("asr_removed"):
            try:
                tok = SU._yt_token()
                H = {"Authorization": f"Bearer {tok}"}
                caps = requests.get("https://www.googleapis.com/youtube/v3/captions", params={"part": "snippet", "videoId": st["yt_id"]},
                                    headers=H, timeout=60).json().get("items", [])
                for c in caps:
                    if c["snippet"].get("trackKind") == "asr":
                        r = requests.delete("https://www.googleapis.com/youtube/v3/captions", params={"id": c["id"]}, headers=H, timeout=60)
                        if r.status_code in (200, 204):
                            st["asr_removed"] = True
                            print("PHỤ ĐỀ TỰ ĐỘNG: đã gỡ", st["yt_id"])
                pub = (plan.get("youtube") or {}).get("publish_at", "")
                if pub and now > datetime.fromisoformat(pub.replace("Z", "+00:00")) + timedelta(hours=48):
                    st["asr_removed"] = st.get("asr_removed") or "het_han"
            except Exception as ex:
                print("PHỤ ĐỀ TỰ ĐỘNG lỗi:", str(ex)[:150])
        sp.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    if sys.argv[1] == "post":
        post(Path(sys.argv[2]))
    else:
        comments()
