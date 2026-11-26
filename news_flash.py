"""TIN NÓNG 4 TIẾNG (Trọng 23/11/2026)

Cứ 4 tiếng (news-flash.yml, mode "pick"):
  gom tin mới (cùng nguồn với podcast) → AI chấm "quan trọng" và "câu view" → chỉ tin thật sự lớn mới đi tiếp
  → Claude xác nhận lần 2 → viết kịch bản short theo bộ khung Smart Penguin Insights (Claude chấm >= 8)
  → gửi kịch bản lên Telegram, CHỜ TRỌNG DUYỆT. Không có tin đủ lớn thì thôi, không cố làm.

Duyệt trên Telegram (đọc qua insight.py inbox; từ 23/11 bot KHÔNG còn nhận link X để làm Insight):
  nút ✅ Duyệt / ✏️ Sửa / ❌ Bỏ dưới tin nháp, hoặc lệnh /duyet, /bo, /sua <góp ý>, /tin (xem kịch bản đang chờ),
  hoặc trả lời (reply) thẳng vào tin nháp: "ok"/"duyệt" = duyệt, "bỏ" = bỏ, chữ khác = góp ý để viết lại.

Sau khi duyệt (mode "poll", news-flash-gate.yml gọi khi có lệnh mới):
  dựng short 9:16 bằng giọng xịn (sources.yaml news_flash.voice, Ludo KOL) → gửi Telegram để Trọng xem. KHÔNG tự đăng.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import podcast as P
import video as V

COMMANDS = [
    ("tin", "Xem kịch bản tin nóng đang chờ duyệt"),
    ("duyet", "Duyệt kịch bản tin nóng mới nhất (hoặc /duyet <mã>)"),
    ("sua", "Góp ý để viết lại: /sua <góp ý> hoặc /sua <mã> <góp ý>"),
    ("nhap", "Dựng nháp giọng Hải Đăng trước (hoặc /nhap <mã>)"),
    ("bo", "Bỏ kịch bản tin nóng (hoặc /bo <mã>)"),
]

JUDGE_SYSTEM = """Bạn là tổng biên tập kênh video ngắn crypto tiếng Việt "Smart Penguin Insights" (TikTok, Shorts, Reels).
Mỗi 4 tiếng bạn xem tin mới và quyết định có đáng làm NGAY một video ngắn tin nóng hay không.
Phần lớn các lần xem sẽ KHÔNG có tin nào đủ tầm: khi đó trả pick = -1. Đừng cố chọn cho có.

ĐỦ TẦM (quan trọng 9-10): sự kiện làm thay đổi thị trường hoặc chính sách, ví dụ: BTC/ETH biến động cực mạnh (khoảng 8% trở lên
trong ngày) hoặc phá đỉnh mọi thời đại; ETF lớn được duyệt hoặc dòng tiền ETF kỷ lục; Fed/chính phủ Mỹ, Việt Nam, Trung Quốc
ra quyết định lớn về crypto; sàn lớn bị hack, sập, mất khả năng rút tiền; vụ hack/exploit trên 100 triệu đô; thanh lý toàn
thị trường trên 1 tỷ đô; tổ chức lớn (BlackRock, MicroStrategy, quốc gia) mua/bán cực lớn; dự án top 20 sự cố nghiêm trọng.
CÂU VIEW (viral 9-10): tin gây sốc, dễ bàn tán, người ngoài crypto cũng muốn xem (vd ví cá voi ngủ đông 10 năm thức dậy,
người nổi tiếng/chính trị gia dính crypto, con số khó tin), NHƯNG phải là tin thật, có nguồn uy tín, không phải tin đồn.
KHÔNG ĐỦ TẦM: tin dự án nhỏ, gọi vốn thường, ra mắt tính năng, airdrop thường, phân tích/dự đoán giá, quảng cáo, tin đã cũ,
tin đã làm video rồi (danh sách bên dưới) trừ khi có diễn biến mới rất lớn."""

JUDGE_PROMPT = """TIN ĐÃ LÀM VIDEO / ĐÃ GỬI DUYỆT GẦN ĐÂY (không chọn lại):
{done}

TIN MỚI (mỗi tin có số [id]):
{items}

Trả về DUY NHẤT JSON:
{{"pick": id tin chính đáng làm video hoặc -1 nếu không tin nào đủ tầm,
  "related": [id các tin khác nói CÙNG sự kiện, để lấy thêm số liệu],
  "importance": điểm quan trọng 0-10 của tin được chọn (0 nếu pick = -1),
  "viral": điểm câu view 0-10 của tin được chọn,
  "story": "tóm tắt sự kiện 1 câu tiếng Việt",
  "why": "1 câu: vì sao đủ tầm (hoặc vì sao lần này không có tin nào đủ tầm)"}}"""

CONFIRM_PROMPT = """Bạn là biên tập viên khó tính của kênh video ngắn crypto tiếng Việt. Một AI khác đề xuất làm NGAY 1 video ngắn tin nóng.
Chỉ đồng ý khi tin CỰC KỲ quan trọng với nhà đầu tư crypto hoặc rất dễ viral, VÀ là tin thật có nguồn rõ ràng.
Tin vừa phải, dự án nhỏ, dự đoán giá, tin đồn: từ chối. Chủ kênh dặn: không có tin thật sự quan trọng thì thôi, không cố.

TIN ĐÃ LÀM GẦN ĐÂY: {done}

ĐỀ XUẤT: {story}
Lý do AI kia đưa ra: {why}

NỘI DUNG NGUỒN:
{text}

Trả về DUY NHẤT JSON: {{"ok": true hoặc false, "importance": 0-10, "viral": 0-10, "why": "1 câu"}}"""


def log(*a):
    print(*a, flush=True)


def ncfg(cfg: dict) -> dict:
    return cfg.get("news_flash") or {}


def state_path(out: Path) -> Path:
    return out / "flash" / "state.json"


def load_state(out: Path) -> dict:
    p = state_path(out)
    st = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    st.setdefault("seen", [])
    st.setdefault("drafts", {})
    return st


def save_state(out: Path, st: dict):
    p = state_path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    st["seen"] = st["seen"][-4000:]
    keep = sorted(st["drafts"].items(), key=lambda kv: kv[1].get("created", ""))[-60:]
    st["drafts"] = dict(keep)
    p.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")


def now_vn() -> datetime:
    return datetime.now(P.VN_TZ)


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
def tg(method: str, **data):
    import insight as I
    return I.tg(method, **data)


def owner() -> str:
    return str(os.getenv("TELEGRAM_CHAT_ID", "")).strip()


def say(text: str, reply_to: int | None = None, buttons: list | None = None) -> int | None:
    data = {"chat_id": owner(), "text": P.nodash(text)[:4000], "disable_web_page_preview": "true"}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    if buttons:
        data["reply_markup"] = json.dumps({"inline_keyboard": buttons}, ensure_ascii=False)
    r = tg("sendMessage", **data) or {}
    return ((r.get("result") or {}).get("message_id"))


def setup_commands(st: dict):
    """Cài menu lệnh cho bot (hiện khi gõ "/" trong Telegram). Chạy 1 lần."""
    if st.get("commands_v") == 2:   # 2: Trọng 23/11 bỏ /list, /cook (hết gom link Insight qua Telegram)
        return
    r = tg("setMyCommands", commands=json.dumps([{"command": c, "description": d} for c, d in COMMANDS], ensure_ascii=False))
    if r and r.get("ok"):
        st["commands_v"] = 2
        log("   Đã cài menu lệnh Telegram")


def buttons_for(did: str) -> list:
    return [[{"text": "✅ Duyệt, dựng giọng xịn", "callback_data": f"nf:ok:{did}"}],
            [{"text": "🎙 Dựng nháp Hải Đăng trước", "callback_data": f"nf:draft:{did}"}],
            [{"text": "✏️ Sửa", "callback_data": f"nf:edit:{did}"}, {"text": "❌ Bỏ", "callback_data": f"nf:no:{did}"}]]


def draft_text(d: dict, plan: dict) -> str:
    sec = (plan.get("sections") or [{}])[0]
    hook = (plan.get("short_hooks") or {}).get("0") or plan.get("hook", "")
    beats = []
    for b in sec.get("beats") or []:
        what = b.get("value") or b.get("text") or b.get("label") or b.get("ticker") or ", ".join(b.get("tickers") or [])
        beats.append(f"• \"{b.get('at', '')}\" → {b.get('type', '')} {what}".strip())
    rv = plan.get("script_review") or {}
    scores = rv.get("scores") or {}
    n_words = len((hook + " " + sec.get("narration", "") + " " + plan.get("short_cta", "")).split())
    lines = [
        f"⚡ KỊCH BẢN TIN NÓNG · mã {d['id']} · chờ Trọng duyệt",
        f"Tin: {d.get('story', '')}",
        f"Vì sao chọn: {d.get('why', '')}",
        f"Quan trọng {d.get('importance', '?')}/10 · Câu view {d.get('viral', '?')}/10",
        f"Claude chấm kịch bản: {plan.get('script_score', '?')}/10"
        + (" (" + ", ".join(f"{k} {v}" for k, v in scores.items()) + ")" if scores else ""),
        f"Độ dài ước tính: khoảng {round(n_words / 3.5)} giây · giọng {str(ncfg(V.load_cfg()).get('voice', '')).split(':')[-1].split('@')[0]} · short 9:16",
        "",
        f"TIÊU ĐỀ: {plan.get('title', '')}",
        f"ẢNH BÌA: {plan.get('thumb_text', '')} · {plan.get('thumb_stat', '')}",
        "",
        f"CÂU MỞ: {hook}",
        "",
        f"LỜI ĐỌC: {sec.get('narration', '')}",
        "",
        f"CÂU KẾT: {plan.get('short_cta', '')}",
        "",
        "HÌNH THEO LỜI ĐỌC:",
        *beats,
        "",
        "Nguồn: " + " · ".join(d.get("sources", [])[:4]),
        "",
        "Bấm nút bên dưới, hoặc trả lời (reply) tin này: \"ok\" để duyệt, \"bỏ\" để bỏ, viết góp ý để mình sửa.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 1. LỌC TIN + VIẾT KỊCH BẢN
# ---------------------------------------------------------------------------
def done_list(st: dict) -> str:
    rows = sorted(st["drafts"].values(), key=lambda x: x.get("created", ""))[-15:]
    return "\n".join(f"- {r.get('created', '')[:16]}: {r.get('story', '')}" for r in rows) or "(chưa có)"


def judge(gem, cfg: dict, st: dict, items: list[dict]) -> dict:
    listing = "\n".join(f"[{i}] ({it['source']}, {it['time'].astimezone(P.VN_TZ):%H:%M}) {it['title']}\n{P.clean_text(it.get('text', ''), 400)}"
                        for i, it in enumerate(items))
    pr = JUDGE_PROMPT.format(done=done_list(st), items=listing)
    j = None
    if os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY"):
        try:   # 23/11: Gemini quá tải 503 cả 40 phút, Claude chấm trước cho nhanh, Gemini dự phòng
            import script_review as SR
            j = SR.run_claude(JUDGE_SYSTEM + "\n\n" + pr)
            j["by"] = "claude"
        except Exception as ex:
            log(f"   ! Claude chấm tin lỗi, chuyển sang Gemini: {str(ex)[:200]}")
    if j is None:
        j = V.llm_json(gem, cfg, JUDGE_SYSTEM, pr)
    try:
        j["pick"] = int(j.get("pick", -1))
    except (TypeError, ValueError):
        j["pick"] = -1
    return j


def claude_confirm(st: dict, j: dict, text: str) -> dict | None:
    if not (os.getenv("CLAUDE_CODE_OAUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")):
        return None
    try:
        import script_review as SR
        return SR.run_claude(CONFIRM_PROMPT.format(done=done_list(st), story=j.get("story", ""), why=j.get("why", ""), text=text[:6000]))
    except Exception as ex:
        log(f"   ! Claude xác nhận lỗi: {str(ex)[:200]}")
        return None


def write_script(post: dict, did: str, notes: list[str] | None = None) -> dict:
    """Viết kịch bản short tin nóng (dùng chung bộ viết + Claude chấm của Smart Penguin Insights), không đọc giọng."""
    import insight_lab as L
    os.environ["INSIGHT_FORMAT"] = "news"
    os.environ["INSIGHT_SCRIPT_ONLY"] = "1"
    os.environ.pop("INSIGHT_SCRIPT", None)
    try:
        lab = L.prepare([post], Path("lab_tin") / did, notes=notes)
    finally:
        os.environ.pop("INSIGHT_SCRIPT_ONLY", None)
    plan = json.loads((lab / "plan.json").read_text(encoding="utf-8"))
    plan["source_post"] = post
    plan.pop("lint", None)
    return plan


def save_script(out: Path, did: str, plan: dict) -> str:
    p = out / "flash" / "scripts" / f"{did}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    return str(p)


def send_draft(out: Path, d: dict):
    plan = json.loads((out / d["script"]).read_text(encoding="utf-8"))
    d["msg_id"] = say(draft_text(d, plan), buttons=buttons_for(d["id"]))


def expire(st: dict, cfg: dict):
    hrs = float(ncfg(cfg).get("expire_hours", 10))
    lim = timedelta(hours=hrs)
    for d in st["drafts"].values():
        if d.get("status") in ("waiting", "revise") and now_vn() - datetime.fromisoformat(d["created"]) > lim:
            d["status"] = "expired"
            say(f"⌛ Kịch bản tin nóng {d['id']} quá {hrs:g} tiếng chưa duyệt, tin đã cũ nên mình bỏ.",
                reply_to=d.get("msg_id"))


def pick(out: Path, cfg: dict):
    nc = ncfg(cfg)
    st = load_state(out)
    setup_commands(st)
    expire(st, cfg)
    today = now_vn().date().isoformat()
    n_today = len([d for d in st["drafts"].values() if d.get("created", "").startswith(today)])
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=float(nc.get("lookback_hours", 5)))
    if st.get("last_run"):
        since = max(since, datetime.fromisoformat(st["last_run"]) - timedelta(minutes=30))
    seen = set(st["seen"])
    log(f"① Gom tin từ {since.astimezone(P.VN_TZ):%d/%m %H:%M} (giờ VN)")
    items = P.collect(cfg, since, seen)[:150]
    st["seen"] = list(seen)
    st["last_run"] = now.isoformat()
    log(f"   {len(items)} tin mới")
    if n_today >= int(nc.get("max_per_day", 3)):
        log(f"   Hôm nay đã có {n_today} kịch bản tin nóng, đủ giới hạn, bỏ qua.")
        return save_state(out, st)
    if not items:
        return save_state(out, st)
    gem = P.Gemini(os.getenv("GEMINI_API_KEY", ""))
    log("② Chấm độ quan trọng / câu view")
    j = judge(gem, cfg, st, items)
    imp, vir = float(j.get("importance") or 0), float(j.get("viral") or 0)
    log(f"   pick={j['pick']} quan trọng {imp} · câu view {vir} · {j.get('why', '')}")
    ok = 0 <= j["pick"] < len(items) and (imp >= float(nc.get("min_importance", 9)) or vir >= float(nc.get("min_viral", 9)))
    if not ok:
        log("   Không có tin đủ tầm, lần này không làm video.")
        return save_state(out, st)
    group = [items[j["pick"]]] + [items[i] for i in (j.get("related") or [])
                                  if isinstance(i, int) and 0 <= i < len(items) and i != j["pick"]][:4]
    text = "\n\n".join(f"Nguồn: {g['source']} ({g['time'].astimezone(P.VN_TZ):%H:%M %d/%m} giờ VN)\n{g['title']}\n{g.get('text', '')}"
                       for g in group)
    c = None if j.get("by") == "claude" else claude_confirm(st, j, text)   # Claude đã chấm thì khỏi xác nhận lại
    if c is not None:
        log(f"   Claude: {'ĐỒNG Ý' if c.get('ok') else 'TỪ CHỐI'} · {c.get('why', '')}")
        if not c.get("ok"):
            return save_state(out, st)
        imp, vir = c.get("importance", imp), c.get("viral", vir)
    did = now_vn().strftime("%d%m%H%M")
    post = {"author": ", ".join(dict.fromkeys(g["source"] for g in group)), "handle": "",
            "url": group[0].get("url", ""), "title": group[0]["title"], "text": text[:9000]}
    log("③ Viết kịch bản short (Claude chấm, dưới 8 thì viết lại)")
    plan = write_script(post, did)
    d = {"id": did, "status": "waiting", "created": now_vn().isoformat(), "story": j.get("story", ""),
         "why": (c or {}).get("why") or j.get("why", ""), "importance": imp, "viral": vir,
         "sources": [g.get("url", "") for g in group if g.get("url")], "post": post,
         "script": str(Path(save_script(out, did, plan)).relative_to(out))}
    st["drafts"][did] = d
    send_draft(out, d)
    save_state(out, st)
    log(f"✓ Đã gửi kịch bản {did} lên Telegram, chờ duyệt")


def topic(out: Path, cfg: dict, brief: Path):
    """Trọng chỉ định chủ đề (vd "cook short NVDA ngay"): bỏ qua bước lọc/chấm tin và giới hạn mỗi ngày,
    nhưng vẫn viết kịch bản, Claude chấm >= 8, gửi Telegram CHỜ DUYỆT như tin tự lọc."""
    b = json.loads(brief.read_text(encoding="utf-8"))
    st = load_state(out)
    setup_commands(st)
    did = now_vn().strftime("%d%m%H%M")
    post = {"author": b.get("sources_name", "tổng hợp"), "handle": "", "url": (b.get("sources") or [""])[0],
            "title": b.get("title", ""), "text": b["text"][:9000]}
    log(f"③ Viết kịch bản short theo chủ đề Trọng chọn: {b.get('story', '')}")
    plan = write_script(post, did, b.get("notes"))
    d = {"id": did, "status": "waiting", "created": now_vn().isoformat(), "story": b.get("story", ""),
         "why": b.get("why", "Trọng chỉ định"), "importance": b.get("importance", "?"), "viral": b.get("viral", "?"),
         "sources": b.get("sources", []), "post": post, "manual": True,
         "script": str(Path(save_script(out, did, plan)).relative_to(out))}
    st["drafts"][did] = d
    send_draft(out, d)
    save_state(out, st)
    log(f"✓ Đã gửi kịch bản {did} lên Telegram, chờ duyệt")


# ---------------------------------------------------------------------------
# 2. LỆNH DUYỆT TRÊN TELEGRAM (insight.inbox gọi cho từng tin nhắn)
# ---------------------------------------------------------------------------
_OUT: Path | None = None


def _find(st: dict, did: str = "", msg_id: int | None = None) -> dict | None:
    if msg_id:
        for d in st["drafts"].values():
            if d.get("msg_id") == msg_id:
                return d
    if did:
        return st["drafts"].get(did)
    live = [d for d in st["drafts"].values() if d.get("status") in ("waiting", "revise")]
    return max(live, key=lambda d: d["created"]) if live else None


def on_update(out: Path, cfg: dict, up: dict) -> bool:
    """True = tin nhắn này là lệnh tin nóng (đã xử lý), False = để insight.inbox xử lý tiếp (link X...)."""
    cb = up.get("callback_query")
    msg = up.get("message") or {}
    text = (msg.get("text") or "").strip()
    reply_id = (msg.get("reply_to_message") or {}).get("message_id")
    st = load_state(out)
    act, d, note = "", None, ""
    if cb:
        m = re.match(r"nf:(ok|no|edit|draft):(\w+)", cb.get("data") or "")
        if not m:
            return False
        tg("answerCallbackQuery", callback_query_id=cb["id"], text="Đã nhận")
        act, d = m.group(1), st["drafts"].get(m.group(2))
    elif re.match(r"/(duyet|duyệt|bo|bỏ|sua|sửa|tin|nhap|nháp)\b", text, re.I):
        cmd, _, rest = text.partition(" ")
        cmd = cmd.lower().split("@")[0]
        if cmd == "/tin":
            live = [x for x in st["drafts"].values() if x.get("status") in ("waiting", "revise", "approved", "building")]
            say("📰 Kịch bản tin nóng:\n" + ("\n".join(f"• {x['id']} [{x['status']}]: {x.get('story', '')}" for x in live)
                                            or "Không có kịch bản nào đang chờ."))
            return True
        mid = re.match(r"(\d{8})\b\s*(.*)", rest.strip(), re.S)
        d = _find(st, mid.group(1) if mid else "", reply_id)
        note = (mid.group(2) if mid else rest).strip()
        act = {"/duyet": "ok", "/duyệt": "ok", "/bo": "no", "/bỏ": "no", "/nhap": "draft", "/nháp": "draft"}.get(cmd, "edit")
    elif text and (reply_id or not re.search(r"https?://|^/", text)):
        # Trọng 23/11: sau khi bấm "Sửa" anh gõ góp ý thành tin thường (không reply) nên bot bỏ qua.
        # Giờ: reply vào tin kịch bản, HOẶC tin chữ thường không có link khi đang có kịch bản chờ duyệt, đều tính là góp ý.
        d = _find(st, msg_id=reply_id) if reply_id else _find(st)
        if not d:
            return False
        low = text.lower().strip(" .!")
        act = "ok" if low in ("ok", "oke", "okela", "duyệt", "duyet", "được", "dựng đi", "làm đi") else \
            "no" if low in ("bỏ", "bo", "thôi", "không", "khong", "skip") else "edit"
        note = text
    else:
        return False
    if not d:
        say("Không tìm thấy kịch bản tin nóng nào đang chờ. Gõ /tin để xem danh sách.")
        return True
    if d.get("status") not in ("waiting", "revise"):
        say(f"Kịch bản {d['id']} đang ở trạng thái {d.get('status')}, không đổi được nữa.", reply_to=d.get("msg_id"))
        return True
    if act in ("ok", "draft"):   # Trọng 24/11: Hải Đăng là giọng nháp, có lúc muốn xem nháp trước rồi mới dựng giọng xịn
        d["status"] = "approved"
        d["approved"] = now_vn().isoformat()
        d["voice"] = "vieneu:Hải Đăng" if act == "draft" else ""
        say(f"✅ Đã duyệt kịch bản {d['id']}{' (bản NHÁP giọng Hải Đăng)' if act == 'draft' else ''}. Bot bắt đầu dựng short, khoảng 20 đến 40 phút sẽ gửi video.",
            reply_to=d.get("msg_id"))
    elif act == "no":
        d["status"] = "rejected"
        say(f"❌ Đã bỏ kịch bản {d['id']}.", reply_to=d.get("msg_id"))
    elif not note:
        say(f"✏️ Trả lời (reply) vào tin kịch bản {d['id']} bằng góp ý, hoặc gõ /sua {d['id']} <góp ý>.", reply_to=d.get("msg_id"))
    else:
        d["status"] = "revise"
        d.setdefault("notes", []).append(note[:800])
        say(f"✏️ Đã nhận góp ý cho {d['id']}, mình viết lại rồi gửi bản mới nhé.", reply_to=d.get("msg_id"))
    save_state(out, st)
    return True


def revise_all(out: Path, cfg: dict):
    st = load_state(out)
    for d in [x for x in st["drafts"].values() if x.get("status") == "revise"]:
        log(f"✏️ Viết lại kịch bản {d['id']} theo góp ý")
        old = json.loads((out / d["script"]).read_text(encoding="utf-8"))
        sec = (old.get("sections") or [{}])[0]
        notes = [f"Chủ kênh góp ý bản trước (BẮT BUỘC làm theo): {n}" for n in d.get("notes", [])]
        notes.append("CHỈ sửa đúng những phần chủ kênh nêu, giữ NGUYÊN từng chữ các phần còn lại của bản trước "
                     "(câu mở, lời đọc, hình, tiêu đề, ảnh bìa) nếu góp ý không nhắc tới.")
        notes.append("Bản trước: câu mở \"" + str((old.get("short_hooks") or {}).get("0", "")) + "\"; lời đọc \"" + sec.get("narration", "") + "\"")
        try:
            plan = write_script(d["post"], d["id"], notes)
        except Exception as ex:
            say(f"⚠️ Viết lại kịch bản {d['id']} lỗi: {str(ex)[:200]}")
            continue
        save_script(out, d["id"], plan)
        d["status"] = "waiting"
        d["version"] = d.get("version", 1) + 1
        send_draft(out, d)
        save_state(out, st)


# ---------------------------------------------------------------------------
# 3. DỰNG SAU KHI DUYỆT
# ---------------------------------------------------------------------------

def _fair_res(res: dict, short: Path, long: Path) -> dict:
    """Bản tối giản để chấm đối đầu: 2 bản nhận ĐÚNG cùng lượng thông tin (khung hình, không lời đọc từng giây)."""
    plan = res["plan"]
    return {"plan": {"title": "", "hook": "", "news": True, "format": plan.get("format", ""),
                     "sections": [{"narration": " ".join(s.get("narration", "") for s in plan.get("sections", []))}]},
            "long": long, "shorts": [{"path": short}], "duration": res["duration"], "voice": res.get("voice", ""), "scenes": []}


def head_to_head(gem, cfg, res: dict, old_tag: str) -> tuple[float, float] | None:
    """Trọng 27/11: chấm LẠI bản cũ và bản mới bằng CÙNG luật hiện hành, cùng bot, trong cùng lượt, rồi mới so.
    Trả (điểm mới, điểm cũ) hoặc None nếu không tải được bản cũ."""
    import subprocess
    import insight_publish as PB
    d = Path("old_release")
    d.mkdir(exist_ok=True)
    r = subprocess.run(["gh", "release", "download", f"insight-{old_tag}", "-R", os.getenv("GITHUB_REPOSITORY", "LHTrong0322/trampodcast"),
                        "-p", "*9x16.mp4", "-p", "*16x9.mp4", "-D", str(d), "--clobber"], capture_output=True, text=True)
    olds = sorted(x for x in d.glob("*short1-9x16.mp4") if "nhap" not in x.name)
    oldl = sorted(x for x in d.glob("*16x9.mp4") if "nhap" not in x.name)
    if not olds:
        log(f"   ! không tải được bản cũ {old_tag}: {(r.stderr or '')[:200]}")
        return None
    sc = []
    for rr in (_fair_res(res, res["shorts"][0]["path"], res["long"]), _fair_res(res, olds[0], oldl[0] if oldl else res["long"])):
        try:
            sc.append(float((PB.review(gem, cfg, rr, None) or {}).get("score") or 0))
        except Exception as ex:
            log(f"   ! chấm đối đầu lỗi: {str(ex)[:200]}")
            return None
    log(f"   Chấm đối đầu cùng luật: bản mới {sc[0]} / bản cũ {sc[1]}")
    return sc[0], sc[1]

def build(out: Path, cfg: dict, did: str):
    import insight_lab as L
    import insight_render as R
    import insight_publish as PB
    st = load_state(out)
    d = st["drafts"][did]
    d["status"] = "building"
    save_state(out, st)
    voice = os.getenv("NF_VOICE", "").strip() or d.get("voice") or ncfg(cfg).get("voice", "gemini:Ludo@kol")
    os.environ.update(INSIGHT_SCRIPT=str(out / d["script"]), INSIGHT_VOICE=voice,
                      INSIGHT_TWO_PASS="0", SOCIAL_AUTOPOST="0", INSIGHT_FORMAT="news")
    try:
        import preflight as PF
        lab = L.prepare("", Path("lab"))
        # Trọng 24/11: dựng → bot review → còn dưới 8 thì Claude sửa thẻ hình theo góp ý → dựng lại (giọng giữ nguyên)
        gem = P.Gemini(os.getenv("INSIGHT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", ""))
        rounds = int(os.getenv("NF_FIX_ROUNDS", "").strip() or ncfg(cfg).get("fix_rounds", 2))
        hist, rv = [], None
        best = None   # (điểm, kế hoạch, review) của vòng tốt nhất
        for k in range(rounds + 1):
            res = R.render(lab, Path("render_out"))
            rv = PB.review(gem, cfg, res, None) or {}
            hist.append(rv.get("score"))
            log(f"⑨ Review sau dựng vòng {k + 1}: {rv.get('score', '?')}/10")
            try:
                sc = float(rv.get("score") or 0)
            except (TypeError, ValueError):
                sc = 0
            if best is None or sc > best[0]:
                best = (sc, (lab / "plan.json").read_text(encoding="utf-8"), rv)
            if sc >= 8 or k == rounds or not rv.get("can_sua"):
                break
            plan = json.loads((lab / "plan.json").read_text(encoding="utf-8"))
            try:
                ch = PF.plan_fix(plan, rv)
            except Exception as ex:
                log(f"   ! tự sửa theo review lỗi: {str(ex)[:200]}")
                break
            if not ch:
                break
            L.photo_beats(lab, plan)
            (lab / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
            log("   Tự sửa theo review: " + "; ".join(ch[:8]))
        # Lỗi 26/11 (short ETF): tự sửa làm điểm tụt 6.0 → 5.6 → 5.4 mà vẫn gửi bản cuối. Giờ vòng cuối kém hơn thì dựng lại bản tốt nhất
        if best is not None and hist and best[0] > float(hist[-1] or 0):
            log(f"   Vòng cuối {hist[-1]} kém hơn vòng tốt nhất {best[0]}: dựng lại bản tốt nhất để gửi")
            (lab / "plan.json").write_text(best[1], encoding="utf-8")
            res = R.render(lab, Path("render_out"))
            rv = best[2]
            hist.append(f"giữ {best[0]}")
        res["review_rounds"] = hist
        # LUẬT CỨNG (Trọng 26/11): video ra điểm thấp hơn là không bao giờ chấp nhận. Dựng lại 1 tin đã có video mà bản mới
        # thấp hơn bản cũ thì không gửi làm bản chính, giữ bản cũ và báo điểm.
        # Trọng 27/11: điểm cũ chấm theo luật cũ thì không so được. Chấm lại CẢ 2 bản bằng luật hiện hành rồi mới so.
        old_best = float(d.get("best_score") or 0)
        new_best = best[0] if best else 0
        h2h = head_to_head(gem, cfg, res, d["best_tag"]) if d.get("best_tag") else None
        if h2h:
            new_cmp, old_cmp = h2h
            cmp_note = f"chấm lại cùng luật mới: bản mới {new_cmp}/10, bản cũ {old_cmp}/10"
        else:
            new_cmp, old_cmp = new_best, old_best
            cmp_note = f"bản mới {new_best}/10, bản cũ {old_best}/10 (không chấm lại được bản cũ)"
        if old_cmp and new_cmp < old_cmp:
            say(f"⛔ Bản dựng lại {did} KHÔNG ĐẠT: {cmp_note}. Không gửi làm bản chính, giữ bản cũ. "
                f"Các vòng: {' → '.join(str(x) for x in hist)}", reply_to=d.get("msg_id"))
            try:   # Trọng 27/11: bản bị chặn vẫn gửi để xem, ghi rõ không đăng
                PB.tg_video(res["shorts"][0]["path"], f"⛔ KHÔNG ĐẠT, chỉ để xem, KHÔNG đăng ({did}, {new_cmp}/10)")
            except Exception as ex:
                log(f"   ! gửi bản không đạt để xem lỗi: {str(ex)[:200]}")
            log(f"   ⛔ {cmp_note}: không gửi làm bản chính")
            d["status"] = "built"
            return
        if h2h:
            say(f"✅ {did}: {cmp_note}, bản mới tốt hơn nên gửi.", reply_to=d.get("msg_id"))
        pub = PB.publish(lab, res, Path("render_out"), data_dir=out, rv=rv) or {}
        d["best_score"] = new_best
        rel = str(pub.get("release") or "")
        if "/insight-" in rel:   # bản đang là bản chính, để lần dựng lại sau chấm đối đầu
            d["best_tag"] = rel.rsplit("/insight-", 1)[1]
        d["status"] = "built"
        d["built"] = now_vn().isoformat()
    except Exception as ex:
        d["status"] = "failed"
        d["error"] = str(ex)[:500]
        say(f"⚠️ Dựng short tin nóng {did} lỗi: {str(ex)[:300]}\nGõ /tin để xem, mình sẽ kiểm tra lại.", reply_to=d.get("msg_id"))
        raise
    finally:
        st2 = load_state(out)
        st2["drafts"][did] = d
        save_state(out, st2)


def poll(out: Path, cfg: dict) -> str:
    import insight as I
    st = load_state(out)
    setup_commands(st)
    save_state(out, st)
    I.inbox(out, cfg)      # đọc tin nhắn mới (chỉ lệnh tin nóng)
    revise_all(out, cfg)
    st = load_state(out)
    ready = sorted([x for x in st["drafts"].values() if x.get("status") == "approved"], key=lambda x: x.get("approved", ""))
    return ready[0]["id"] if ready else ""


def wait_reply(out: Path, cfg: dict) -> str:
    """Trọng 23/11: lịch 15 phút của GitHub gần như không chạy nên bấm duyệt/góp ý rất lag.
    Giờ sau khi gửi kịch bản, run này ở lại đọc Telegram vài giây một lần (tối đa NF_WAIT_MIN phút):
    duyệt → trả mã để dựng ngay trong run này; góp ý → viết lại và gửi lại; bỏ → dừng.
    Không chờ quanh giờ podcast (4:30 đến 5:45 VN) để không giữ chỗ của podcast."""
    import time
    import insight as I
    h = now_vn().hour + now_vn().minute / 60
    if 4.5 <= h <= 5.75:
        return ""
    end = time.time() + 60 * float(os.getenv("NF_WAIT_MIN", "30"))
    log(f"⏳ Chờ Trọng trả lời trên Telegram (tối đa {os.getenv('NF_WAIT_MIN', '30')} phút)")
    while time.time() < end:
        st = load_state(out)
        ready = [x for x in st["drafts"].values() if x.get("status") == "approved"]
        if ready:
            return sorted(ready, key=lambda x: x.get("approved", ""))[0]["id"]
        if any(x.get("status") == "revise" for x in st["drafts"].values()):
            revise_all(out, cfg)
            end = max(end, time.time() + 60 * 15)   # vừa gửi bản mới: chờ thêm
            continue
        if not any(x.get("status") == "waiting" for x in st["drafts"].values()):
            return ""
        try:
            I.inbox(out, cfg)
        except Exception as ex:
            log(f"   ! đọc Telegram lỗi: {str(ex)[:150]}")
        time.sleep(6)
    log("   Hết giờ chờ, lượt kiểm tra mỗi tiếng sẽ xử lý tiếp khi Trọng trả lời")
    return ""


def gate(state: Path, store: Path) -> str:
    """Chạy 15 phút/lần (rất nhẹ): chỉ gọi poll khi có kịch bản đang chờ VÀ có tin nhắn mới, hoặc có bản đã duyệt."""
    st = json.loads(state.read_text(encoding="utf-8")) if state.exists() and state.stat().st_size else {}
    drafts = (st.get("drafts") or {}).values()
    if any(d.get("status") == "approved" for d in drafts):
        return "yes"
    if not any(d.get("status") in ("waiting", "revise") for d in drafts):
        return "no"
    if any(d.get("status") == "revise" for d in drafts):
        return "yes"
    off = (json.loads(store.read_text(encoding="utf-8")) if store.exists() and store.stat().st_size else {}).get("offset", 0)
    r = tg("getUpdates", timeout=0, allowed_updates='["message","callback_query"]') or {}   # không truyền offset: chỉ xem, không xoá tin
    return "yes" if any(u["update_id"] > off for u in r.get("result", [])) else "no"


def watching(state: Path, hours: float = 24) -> str:
    """Trọng 24/11: lịch hẹn giờ của GitHub hay bỏ lượt (10:00 đến 14:00 không lượt canh nào chạy), nên bấm duyệt
    trên Telegram bị kẹt. Lượt canh riêng (news-flash-gate.yml loop=1) chạy chừng nào còn kịch bản cần xử lý.
    "yes" khi còn kịch bản chờ duyệt, chờ sửa hoặc đã duyệt chưa dựng, gửi trong vòng `hours` giờ
    (Telegram chỉ giữ tin nhắn chưa đọc 24 giờ, quá thì thôi canh)."""
    st = json.loads(state.read_text(encoding="utf-8")) if state.exists() and state.stat().st_size else {}
    cut = now_vn() - timedelta(hours=hours)
    for d in (st.get("drafts") or {}).values():
        if d.get("status") not in ("waiting", "revise", "approved"):
            continue
        try:
            made = datetime.fromisoformat(d.get("created", ""))
        except ValueError:
            continue
        if made.tzinfo is None:
            made = made.replace(tzinfo=P.VN_TZ)
        if made >= cut:
            return "yes"
    return "no"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["pick", "poll", "build", "gate", "watch", "topic", "revise", "setscript"])
    ap.add_argument("--script", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--brief", default="")
    ap.add_argument("--out", default="public")
    ap.add_argument("--id", default="")
    ap.add_argument("--state", default="")
    ap.add_argument("--store", default="")
    a = ap.parse_args()
    out = Path(a.out)
    cfg = V.load_cfg()

    def output(k, v):
        log(f"   → {k}={v}")
        if os.getenv("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"{k}={v}\n")
    if a.mode == "gate":
        return output("run", gate(Path(a.state), Path(a.store)))
    if a.mode == "watch":
        return output("watch", watching(Path(a.state)))
    if not ncfg(cfg).get("enabled", True):
        log("Tin nóng đang tắt trong sources.yaml (news_flash.enabled)")
        return output("build", "")
    if a.mode == "pick":
        pick(out, cfg)
        return output("build", wait_reply(out, cfg))
    if a.mode == "setscript":   # Trọng tự sửa kịch bản trong chat: ghi đè kịch bản, gửi lại Telegram chờ bấm duyệt
        st = load_state(out)
        d = st["drafts"][a.id]
        plan = json.loads(Path(a.script).read_text(encoding="utf-8"))
        save_script(out, a.id, plan)
        if os.getenv("NF_APPROVE") == "1":   # Trọng đã nói rõ "cook video" trong chat: duyệt luôn, dựng ngay
            d.update(status="approved", approved=now_vn().isoformat(), version=d.get("version", 1) + 1)
            save_state(out, st)
            say(f"✅ Đã cập nhật kịch bản {a.id} theo bản Trọng sửa (tiêu đề, ảnh bìa). Bot bắt đầu dựng short, "
                "khoảng 20 đến 40 phút sẽ gửi video.", reply_to=d.get("msg_id"))
            return output("build", a.id)
        d.update(status="waiting", version=d.get("version", 1) + 1)
        send_draft(out, d)
        save_state(out, st)
        return output("build", wait_reply(out, cfg))
    if a.mode == "revise":   # góp ý dài của Trọng gửi qua phiên code (giống /sua trên Telegram)
        st = load_state(out)
        d = st["drafts"][a.id]
        d["status"] = "revise"
        d.setdefault("notes", []).append(a.note or os.getenv("NF_NOTE", ""))
        save_state(out, st)
        revise_all(out, cfg)
        return output("build", wait_reply(out, cfg))
    if a.mode == "topic":
        topic(out, cfg, Path(a.brief))
        return output("build", wait_reply(out, cfg))
    if a.mode == "poll":
        return output("build", poll(out, cfg) or wait_reply(out, cfg))
    build(out, cfg, a.id)


if __name__ == "__main__":
    sys.exit(main())
