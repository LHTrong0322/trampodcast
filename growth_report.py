"""Báo cáo tăng trưởng hằng tuần: lấy số liệu THẬT của các video đã đăng, nhờ Claude rút bài học cho video sau.

  python growth_report.py public     # public = thư mục dữ liệu (nhánh podcast-data)

YouTube: lượt xem, like, bình luận, thời lượng, ngày đăng (YouTube Data API, khoá YT_*).
         Thời gian xem trung bình và tỷ lệ bấm ảnh bìa chỉ có khi khoá có quyền yt-analytics.readonly (chưa có thì bỏ qua).
Facebook: danh sách Reels + lượt xem nếu khoá có quyền read_insights (chưa có thì bỏ qua).
Kết quả: insight/performance.json + insight/lessons.md (cập nhật) + tin nhắn Telegram.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

import insight_lessons as LS
import social_upload as SU

VN = timezone(timedelta(hours=7))


def youtube_stats() -> list[dict]:
    tok = SU._yt_token()
    H = {"Authorization": f"Bearer {tok}"}
    ch = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "contentDetails,statistics", "mine": "true"},
                      headers=H, timeout=60).json()["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params={"part": "contentDetails", "playlistId": up, "maxResults": 50},
                         headers=H, timeout=60).json().get("items", [])
    ids = [i["contentDetails"]["videoId"] for i in items]
    if not ids:
        return []
    vs = requests.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "snippet,statistics,contentDetails,status", "id": ",".join(ids)},
                      headers=H, timeout=60).json().get("items", [])
    out = []
    now = datetime.now(timezone.utc)
    for v in vs:
        if v.get("status", {}).get("privacyStatus") != "public":
            continue
        pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
        days = max(1.0, (now - pub).total_seconds() / 86400)
        st = v.get("statistics", {})
        dur = v["contentDetails"]["duration"]
        m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", dur)
        secs = (int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0)) if m else 0
        out.append({"platform": "YouTube", "kind": "Short" if secs <= 180 and "#shorts" in v["snippet"]["title"].lower() else "Video dài",
                    "id": v["id"], "title": v["snippet"]["title"], "published": pub.astimezone(VN).strftime("%d/%m %H:%M"),
                    "days": round(days, 1), "views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)),
                    "comments": int(st.get("commentCount", 0)), "seconds": secs,
                    "views_per_day": round(int(st.get("viewCount", 0)) / days, 1)})
    # số liệu sâu (giữ chân, tỷ lệ bấm) nếu có quyền yt-analytics.readonly
    try:
        start = (now - timedelta(days=28)).strftime("%Y-%m-%d")
        r = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=H, timeout=60, params={
            "ids": "channel==MINE", "startDate": start, "endDate": now.strftime("%Y-%m-%d"), "dimensions": "video",
            "metrics": "views,averageViewDuration,averageViewPercentage", "maxResults": 50, "sort": "-views"})
        if r.ok:
            rows = {row[0]: row for row in r.json().get("rows", [])}
            for v in out:
                if v["id"] in rows:
                    v["avg_view_seconds"] = rows[v["id"]][2]
                    v["avg_view_percent"] = round(rows[v["id"]][3], 1)
        else:
            print("   YouTube Analytics chưa có quyền (bỏ qua giữ chân):", r.status_code)
    except Exception as ex:
        print("   YouTube Analytics lỗi:", str(ex)[:120])
    return out


def facebook_stats() -> list[dict]:
    page, tok = os.environ.get("FB_PAGE_ID", "").strip(), os.environ.get("FB_PAGE_TOKEN", "").strip()
    if not page or not tok:
        return []
    out = []
    rl = requests.get(f"https://graph.facebook.com/{SU.FB_VER}/{page}/video_reels", timeout=60,
                      params={"fields": "id,description,created_time,length", "access_token": tok}).json().get("data", [])
    for x in rl[:30]:
        row = {"platform": "Facebook", "kind": "Reel", "id": x["id"], "title": (x.get("description") or "")[:90],
               "published": (x.get("created_time") or "")[:16]}
        ins = requests.get(f"https://graph.facebook.com/{SU.FB_VER}/{x['id']}/video_insights", timeout=60,
                           params={"access_token": tok}).json()
        for m in ins.get("data", []):
            if m.get("name") in ("blue_reels_play_count", "fb_reels_total_plays", "post_impressions_unique", "post_video_avg_time_watched"):
                row[m["name"]] = (m.get("values") or [{}])[0].get("value")
        out.append(row)
    return out


def claude_analyze(rows: list[dict], lessons_before: str) -> dict:
    """Nhờ Claude (gói Pro qua CLAUDE_CODE_OAUTH_TOKEN) rút bài học. Không có thì dùng xếp hạng đơn giản."""
    ask = ("Bạn là chuyên gia tăng trưởng kênh YouTube/Facebook crypto tiếng Việt 'Smart Penguin Insights'. "
           "Dưới đây là số liệu THẬT các video đã đăng (JSON) và bài học cũ. Hãy phân tích video/chủ đề/tiêu đề/kiểu hook nào hiệu quả, "
           "cái nào kém và vì sao (dựa trên số liệu, không đoán bừa; mẫu ít thì nói rõ là chưa đủ dữ liệu). "
           "Viết tiếng Việt dễ hiểu, không dùng dấu gạch ngang dài, nói 'insider' thay 'người trong cuộc', 'retail' thay 'nhỏ lẻ'. "
           "Chỉ in ra JSON: {\"summary\": \"2-3 câu\", \"lessons\": [\"3-6 bài học cụ thể áp dụng được cho video sau\"], "
           "\"top\": [\"tên video: lý do\"], \"next_topics\": [\"2-3 gợi ý chủ đề nên làm tiếp\"]}\n\n"
           f"SỐ LIỆU:\n{json.dumps(rows, ensure_ascii=False)}\n\nBÀI HỌC CŨ:\n{lessons_before[:3000]}")
    tok = re.sub(r"\s+", "", os.getenv("CLAUDE_CODE_OAUTH_TOKEN", ""))
    if tok and shutil.which("claude"):
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
        r = subprocess.run(["claude", "-p", ask, "--max-turns", "3", "--model", "sonnet", "--output-format", "text"],
                           cwd=tempfile.mkdtemp(), env=env, capture_output=True, text=True, timeout=600)
        m = re.search(r"\{.*\}", r.stdout, re.S)
        if m:
            try:
                return {**json.loads(m.group(0)), "by": "Claude"}
            except Exception:
                pass
        print("   Claude chưa phân tích được:", (r.stdout or r.stderr)[:200])
    yt = sorted([x for x in rows if x["platform"] == "YouTube"], key=lambda x: -x.get("views_per_day", 0))
    return {"summary": f"{len(rows)} video có số liệu. Chưa phân tích bằng Claude.", "lessons": [],
            "top": [f"{x['title']}: {x['views']} lượt xem" for x in yt[:3]], "next_topics": [], "by": "xếp hạng đơn giản"}


def main(data_dir: Path):
    rows = []
    for fn in (youtube_stats, facebook_stats):
        try:
            rows += fn()
        except Exception as ex:
            print(f"   ! {fn.__name__} lỗi: {str(ex)[:200]}")
    d = data_dir / "insight"
    d.mkdir(parents=True, exist_ok=True)
    before = (d / "lessons.md").read_text(encoding="utf-8") if (d / "lessons.md").exists() else ""
    an = claude_analyze(rows, before) if rows else {"summary": "Chưa có video công khai nào để đo.", "lessons": [], "top": [], "by": "-"}
    perf = {"week": datetime.now(VN).strftime("%d/%m/%Y"), "rows": rows, **an}
    (d / "performance.json").write_text(json.dumps(perf, ensure_ascii=False, indent=1), encoding="utf-8")
    LS.build(data_dir)
    yt = [x for x in rows if x["platform"] == "YouTube"]
    lines = [f"📈 BÁO CÁO TĂNG TRƯỞNG TUẦN {perf['week']} (phân tích: {an.get('by')})", an.get("summary", ""), ""]
    for x in sorted(yt, key=lambda x: -x["views"])[:8]:
        extra = f", giữ chân {x['avg_view_percent']}%" if x.get("avg_view_percent") is not None else ""
        lines.append(f"• [{x['kind']}] {x['title'][:60]}: {x['views']} xem ({x['views_per_day']}/ngày), {x['likes']} like, {x['comments']} bình luận{extra}")
    fb = [x for x in rows if x["platform"] == "Facebook"]
    if fb:
        lines.append(f"• Facebook: {len(fb)} Reels" + ("" if any(len(x) > 5 for x in fb) else " (chưa có quyền đọc lượt xem)"))
    if an.get("lessons"):
        lines += ["", "Bài học cho video sau:"] + [f"✅ {x}" for x in an["lessons"]]
    if an.get("next_topics"):
        lines += ["", "Gợi ý chủ đề tiếp theo:"] + [f"💡 {x}" for x in an["next_topics"]]
    msg = "\n".join(lines).replace("\u2014", ",").replace("\u2013", ",")
    print(msg)
    try:
        import insight_publish as PB
        PB.tg_text(msg)
    except Exception as ex:
        print("   ! Telegram lỗi:", ex)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "public"))
